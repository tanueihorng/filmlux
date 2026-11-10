"""Headless Edge/Chrome frame capture over the DevTools protocol (no Playwright, no extra executables)."""
from __future__ import annotations

import atexit
import base64
import io
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

import websocket
from PIL import Image

from .config import edge_path


def free_port() -> int:
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


CALL_DEADLINE = 60.0                                   # seconds for any single DevTools call, however chatty the browser is
_OPEN: set = set()
_JOB = None


def _job():
    """Windows: a Job Object that kills every browser we start when this Python process ends, even if it is force-killed."""
    global _JOB
    if _JOB is not None or os.name != "nt":
        return _JOB
    try:
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.CreateJobObjectW.restype = wintypes.HANDLE
        k32.OpenProcess.restype = wintypes.HANDLE

        class BASIC(ctypes.Structure):
            _fields_ = [("a", ctypes.c_int64), ("b", ctypes.c_int64), ("LimitFlags", wintypes.DWORD), ("c", ctypes.c_size_t), ("d", ctypes.c_size_t),
                        ("e", wintypes.DWORD), ("f", ctypes.c_size_t), ("g", wintypes.DWORD), ("h", wintypes.DWORD)]

        class IOC(ctypes.Structure):
            _fields_ = [("x", ctypes.c_uint64 * 6)]

        class EXT(ctypes.Structure):
            _fields_ = [("Basic", BASIC), ("Io", IOC), ("p", ctypes.c_size_t), ("q", ctypes.c_size_t), ("r", ctypes.c_size_t), ("s", ctypes.c_size_t)]
        h = k32.CreateJobObjectW(None, None)
        info = EXT(); info.Basic.LimitFlags = 0x2000   # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if h and k32.SetInformationJobObject(h, 9, ctypes.byref(info), ctypes.sizeof(info)):
            _JOB = (k32, h)
    except Exception:
        _JOB = False
    return _JOB


def _adopt(pid: int):
    j = _job()
    if j:
        k32, h = j
        ph = k32.OpenProcess(0x0001 | 0x0100, False, pid)   # PROCESS_TERMINATE | PROCESS_SET_QUOTA
        if ph:
            k32.AssignProcessToJobObject(h, ph); k32.CloseHandle(ph)


LOCAL = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # never send 127.0.0.1 through a corporate proxy


def _watchdog(child_pid: int):
    """macOS/Linux: a tiny shell loop that kills the browser's process group if this Python process disappears
    (even when it is force-killed, which skips atexit)."""
    if os.name == "nt":
        return None
    try:
        return subprocess.Popen(["/bin/sh", "-c", f"while kill -0 {os.getpid()} 2>/dev/null && kill -0 {child_pid} 2>/dev/null; do sleep 2; done; "
                                                  f"kill -9 -{child_pid} 2>/dev/null"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except Exception:
        return None


def _sweep_old_profiles(max_age_h=6):
    """Remove browser profile folders left behind by crashed runs (older than a few hours, so never a live one)."""
    cutoff = time.time() - max_age_h * 3600
    for d in Path(tempfile.gettempdir()).glob("vstudio_edge_*"):
        try:
            if d.is_dir() and d.stat().st_mtime < cutoff:
                shutil.rmtree(d, ignore_errors=True)
        except OSError:
            pass


_sweep_old_profiles()


@atexit.register
def _close_all():
    for b in list(_OPEN):
        b.close()


class Browser:
    """Loads one HTML page at a fixed viewport; call eval() to drive it and shot() to grab a frame."""

    def __init__(self, page: Path, width: int, height: int, ready_expr: str = "window.ready === true"):
        for attempt in range(3):                       # a fresh headless browser occasionally hangs at start-up: kill it and try again
            try:
                self._start(page, width, height, ready_expr); return
            except (websocket.WebSocketTimeoutException, TimeoutError, RuntimeError, OSError) as e:
                self.close()
                if attempt == 2:
                    raise RuntimeError(f"Headless browser failed to start 3 times: {e}") from e
                time.sleep(1.5)

    def _start(self, page, width, height, ready_expr):
        self.ws = None
        self.port = free_port()
        self.prof = tempfile.mkdtemp(prefix="vstudio_edge_")
        self.proc = subprocess.Popen([edge_path(), "--headless=new", f"--remote-debugging-port={self.port}",
                                      f"--user-data-dir={self.prof}", "--hide-scrollbars", "--mute-audio", "--no-first-run",
                                      "--disable-extensions", "--disable-background-networking", "--disable-sync",
                                      "--force-device-scale-factor=1", "--allow-file-access-from-files", "about:blank"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                     start_new_session=(os.name != "nt"))   # own process group on macOS/Linux, so close() can end all of it
        _adopt(self.proc.pid); self.dog = _watchdog(self.proc.pid); _OPEN.add(self)
        tabs = None
        for _ in range(150):
            try:
                tabs = json.load(LOCAL.open(f"http://127.0.0.1:{self.port}/json", timeout=2))
                break
            except Exception:
                time.sleep(.2)
        if not tabs:
            raise RuntimeError("Headless browser did not start (check VS_BROWSER / group policy).")
        url = [t for t in tabs if t["type"] == "page"][0]["webSocketDebuggerUrl"]
        self.ws = websocket.create_connection(url, suppress_origin=True, timeout=45)
        self.i = 0
        # no Page.enable / Runtime.enable: they make the browser stream events we never need
        self.call("Emulation.setDeviceMetricsOverride", width=width, height=height, deviceScaleFactor=1, mobile=False)
        self.call("Page.navigate", url=Path(page).resolve().as_uri())
        for _ in range(300):
            try:
                if self.eval(f"({ready_expr}) ? 'ok' : 'no'") == "ok":
                    break
            except RuntimeError:
                pass
            time.sleep(.1)
        else:
            raise RuntimeError(f"Page never became ready: {page}")
        self.shot()                                    # warm-up capture: the first paint can lag right after start-up

    def call(self, method, **params):
        self.i += 1
        self.ws.send(json.dumps({"id": self.i, "method": method, "params": params}))
        end = time.time() + CALL_DEADLINE
        while True:
            if time.time() > end:
                raise websocket.WebSocketTimeoutException(f"{method}: no reply in {CALL_DEADLINE:.0f}s")
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.i:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg["result"]

    def eval(self, expr, await_promise=False):
        r = self.call("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=await_promise)
        if "exceptionDetails" in r:
            d = r["exceptionDetails"]
            raise RuntimeError(d.get("exception", {}).get("description") or d.get("text") or str(d))
        return r["result"].get("value")

    def shot(self) -> Image.Image:
        for attempt in range(3):                       # a busy machine can stall one capture: retry rather than fail the render
            try:
                # headless Chromium paints only when something changes: nudge an invisible pixel so a fresh frame always exists
                self.k = getattr(self, "k", 0) + 1
                self.eval("(() => { let d = document.getElementById('__vs_tick'); if (!d) { d = document.createElement('div'); d.id = '__vs_tick';"
                          " d.style.cssText = 'position:fixed;left:0;top:0;width:1px;height:1px;pointer-events:none;z-index:2147483647';"
                          f" document.documentElement.appendChild(d); }} d.style.background = 'rgba(0,0,0,{0.004 + (self.k % 2) * 0.002})'; return 1; }})()")
                data = self.call("Page.captureScreenshot", format="jpeg", quality=96, fromSurface=True)["data"]   # ~3x faster than PNG
                return Image.open(io.BytesIO(base64.b64decode(data))).convert("RGB")
            except websocket.WebSocketTimeoutException:
                if attempt == 2:
                    raise
                time.sleep(1)

    def close(self):
        try:
            if getattr(self, "ws", None):
                self.ws.close()
        except Exception:
            pass
        try:
            if os.name != "nt":
                import signal
                os.killpg(self.proc.pid, signal.SIGTERM)        # the browser and all its helper processes
            else:
                self.proc.terminate()
            self.proc.wait(5)
        except Exception:
            try:
                if os.name != "nt":
                    import signal
                    os.killpg(self.proc.pid, signal.SIGKILL)
                else:
                    self.proc.kill()
            except Exception:
                pass
        if getattr(self, "dog", None):
            try:
                self.dog.kill()
            except Exception:
                pass
        _OPEN.discard(self)
        if getattr(self, "prof", None):
            shutil.rmtree(self.prof, ignore_errors=True)
