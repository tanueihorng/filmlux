"""Filmlux Studio (the app): a local web UI over the same commands the coding agent uses.

  python studio.py app            -> http://127.0.0.1:8765 opens in your browser

Standard library only. Listens on 127.0.0.1 (this computer only). Every action runs `python studio.py ...`
in the background, so the app and the agent always produce identical results.
"""
from __future__ import annotations

import json
import os
import mimetypes
import re
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from .config import INBOX, PROJECTS, ROOT, THEMES, WORK

APP = ROOT / "engine" / "app" / "index.html"
SERVE_ROOTS = {"files": ROOT, "work": WORK}
SAFE_DIRS = ("projects", "examples", "assets", "inbox", "packs", "themes")
RUNNABLE = {"plan", "stills", "audio", "qa", "render", "thumb", "imagegen", "imagegen-check", "check", "samples"}
JOBS: dict[str, dict] = {}
LOCK = threading.Lock()
mimetypes.add_type("video/mp4", ".mp4"); mimetypes.add_type("audio/mp4", ".m4a"); mimetypes.add_type("text/javascript", ".js")


def slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", s.strip()).strip("_")[:60]


def project_dir(name: str) -> Path:
    if name.startswith("examples/"):
        p = (ROOT / name).resolve()
    else:
        p = (PROJECTS / slug(name)).resolve()
    if not (p.is_relative_to(PROJECTS.resolve()) or p.is_relative_to((ROOT / "examples").resolve())) or not (p / "project.json").exists():
        raise FileNotFoundError(name)
    return p


def projects():
    out = []
    for base, label in ((PROJECTS, ""), (ROOT / "examples", "examples/")):
        for d in sorted(base.iterdir()) if base.exists() else []:
            pj = d / "project.json"
            if not pj.exists():
                continue
            try:
                s = json.loads(pj.read_text(encoding="utf-8"))
            except Exception as e:
                s = {"title": f"(project.json error: {e})"}
            renders = sorted((d / "renders").glob("*.mp4"), key=lambda f: f.stat().st_mtime) if (d / "renders").exists() else []
            out.append({"id": label + d.name, "example": bool(label), "title": s.get("title", d.name), "theme": s.get("theme", "navy"),
                        "format": s.get("format", "16:9"), "scenes": len(s.get("scenes", [])),
                        "renders": [rel(r) for r in renders], "modified": max([pj.stat().st_mtime] + [r.stat().st_mtime for r in renders])})
    return sorted(out, key=lambda p: (p["example"], -p["modified"]))


def rel(p: Path) -> str:
    return p.resolve().relative_to(ROOT).as_posix()


def project_detail(name):
    d = project_dir(name)
    spec = json.loads((d / "project.json").read_text(encoding="utf-8"))
    rd = d / "renders"
    renders = []
    for r in sorted(rd.glob("*.mp4"), key=lambda f: f.stat().st_mtime) if rd.exists() else []:
        renders.append({"video": rel(r), "size_mb": round(r.stat().st_size / 1e6, 1), "time": time.strftime("%d %b %H:%M", time.localtime(r.stat().st_mtime)),
                        "contact": rel(r.with_suffix(".contact.jpg")) if r.with_suffix(".contact.jpg").exists() else None,
                        "srt": rel(r.with_suffix(".srt")) if r.with_suffix(".srt").exists() else None,
                        "qa": r.with_suffix(".qa.txt").read_text(encoding="utf-8") if r.with_suffix(".qa.txt").exists() else ""})
    sd = WORK / "stills" / d.name
    stills = sorted(f.name for f in sd.glob("t*.jpg")) if sd.exists() else []
    gen = d / "assets" / "gen" / "REQUESTS.md"
    return {"id": name, "dir": str(d), "spec": spec, "renders": renders, "stills": stills, "stills_dir": d.name,
            "sheet": (sd / "_stills_sheet.jpg").exists(), "audio": (WORK / f"{d.name}_audio_preview.wav").exists(),
            "brief": (d / "brief.md").read_text(encoding="utf-8") if (d / "brief.md").exists() else "",
            "script": (d / "script.md").read_text(encoding="utf-8") if (d / "script.md").exists() else "",
            "imagegen": gen.read_text(encoding="utf-8") if gen.exists() else "",
            "pending_images": sum(1 for sc in spec.get("scenes", []) for o in [sc] + (sc.get("layers") or [])
                                  if o.get("gen") and not (d / o.get("src", "_")).exists())}


def catalogue():
    packs = []
    for d in sorted((ROOT / "packs").iterdir()):
        if (d / "PACK.md").exists():
            md = (d / "PACK.md").read_text(encoding="utf-8")
            line = next((l for l in md.splitlines() if l.startswith("**For:**")), "").replace("**For:**", "").strip()
            st = json.loads((d / "starter" / "project.json").read_text(encoding="utf-8")) if (d / "starter" / "project.json").exists() else {}
            packs.append({"name": d.name, "for": line, "md": md, "theme": st.get("theme"), "format": st.get("format", "16:9"),
                          "stills": sorted(f.name for f in (ROOT / "assets" / "gallery").glob(f"{d.name}_*.jpg"))})
    themes = []
    for f in sorted(THEMES.glob("*.json")):
        t = json.loads(f.read_text(encoding="utf-8"))
        themes.append({"name": f.stem, "about": t.get("about", ""), "mode": t.get("mode"), "colors": t.get("colors", {}),
                       "still": f"theme_{f.stem}.jpg" if (ROOT / "assets" / "gallery" / f"theme_{f.stem}.jpg").exists() else None})
    from .audio import MOODS
    from .voice import VOICES
    return {"packs": packs, "themes": themes, "voices": [{"name": k, "desc": v} for k, v in VOICES.items()],
            "moods": [{"name": k, "desc": v["desc"]} for k, v in MOODS.items()]}


def inbox():
    INBOX.mkdir(exist_ok=True)
    return [{"name": f.name, "kb": round(f.stat().st_size / 1024)} for f in sorted(INBOX.iterdir()) if f.is_file() and f.name != "README.md"]


# ------------------------------------------------------------------ background jobs
def run_job(cmd: str, project: str | None):
    if cmd not in RUNNABLE:
        raise ValueError(cmd)
    with LOCK:
        busy = [j for j in JOBS.values() if j["status"] == "running" and j["cmd"] == "render"]
        if cmd == "render" and busy:
            raise RuntimeError("A render is already running. Wait for it to finish (renders share the machine's browser capacity).")
    args = [sys.executable, "-u", str(ROOT / "studio.py")]
    args += ["imagegen", project, "--check"] if cmd == "imagegen-check" else [cmd] + ([project] if project else [])
    jid = uuid.uuid4().hex[:10]
    job = {"id": jid, "cmd": cmd, "project": project, "status": "running", "log": [], "rc": None, "started": time.time()}
    JOBS[jid] = job

    def work():
        try:
            p = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            for line in p.stdout:
                job["log"].append(line.rstrip()); job["log"] = job["log"][-400:]
            job["rc"] = p.wait()
            job["status"] = "done" if job["rc"] == 0 else "failed"
        except Exception as e:
            job["log"].append(f"error: {e}"); job["status"] = "failed"
        job["ended"] = time.time()
    threading.Thread(target=work, daemon=True).start()
    return job


# ------------------------------------------------------------------ HTTP
class Handler(BaseHTTPRequestHandler):
    server_version = "VideoStudio/2"

    def log_message(self, *a):
        pass

    def send_json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(b)

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def guard(self):                                   # only pages served by this app may call the API
        origin = self.headers.get("Origin") or ""
        host = self.headers.get("Host") or ""
        if origin and urlparse(origin).netloc != host:
            self.send_json({"error": "cross-origin request refused"}, 403); return False
        return True

    def do_GET(self):
        u = urlparse(self.path); path = unquote(u.path)
        try:
            if path in ("/", "/index.html"):
                return self.file(APP)
            if path == "/api/state":
                from .config import PY
                return self.send_json({"projects": projects(), "inbox": inbox(), **catalogue(), "py": PY, "os": sys.platform,
                                       "jobs": sorted(({k: v for k, v in j.items() if k != "log"} for j in JOBS.values()), key=lambda j: -j["started"])[:20]})
            if path.startswith("/api/project/"):
                return self.send_json(project_detail(path[len("/api/project/"):]))
            if path.startswith("/api/job/"):
                j = JOBS.get(path.split("/")[-1])
                return self.send_json(j or {"error": "no such job"}, 200 if j else 404)
            m = re.match(r"^/(files|work)/(.+)$", path)
            if m:
                base = SERVE_ROOTS[m.group(1)].resolve(); f = (base / m.group(2)).resolve()
                if not f.is_relative_to(base) or (m.group(1) == "files" and f.relative_to(base).parts[0] not in SAFE_DIRS):
                    return self.send_json({"error": "not allowed"}, 403)
                return self.file(f)
            self.send_json({"error": "not found"}, 404)
        except FileNotFoundError as e:
            self.send_json({"error": f"not found: {e}"}, 404)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def do_POST(self):
        if not self.guard():
            return
        u = urlparse(self.path); path = unquote(u.path); q = parse_qs(u.query)
        try:
            if path == "/api/upload":                  # raw body upload into inbox/ (streamed; any size)
                name = Path(q.get("name", ["upload"])[0]).name
                name = re.sub(r"[^\w.\- ()]+", "_", name).strip() or "upload"
                INBOX.mkdir(exist_ok=True); dst = INBOX / name; k = 1
                while dst.exists():
                    dst = INBOX / f"{Path(name).stem} ({k}){Path(name).suffix}"; k += 1
                n = int(self.headers.get("Content-Length") or 0); left = n
                with open(dst, "wb") as fh:
                    while left > 0:
                        chunk = self.rfile.read(min(1 << 20, left))
                        if not chunk:
                            break
                        fh.write(chunk); left -= len(chunk)
                return self.send_json({"saved": dst.name, "bytes": n})
            data = json.loads(self.body() or b"{}")
            if path == "/api/brief":
                INBOX.mkdir(exist_ok=True); (INBOX / "brief.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                return self.send_json({"saved": "inbox/brief.json"})
            if path == "/api/new":
                name = slug(data.get("name", ""))
                if not name:
                    return self.send_json({"error": "give the project a name"}, 400)
                args = [sys.executable, str(ROOT / "studio.py"), "new", name, "--pack", data.get("pack", "motion_promo")]
                if data.get("theme"):
                    args += ["--theme", data["theme"]]
                if data.get("format"):
                    args += ["--format", data["format"]]
                if data.get("mode") in ("guided", "creative"):
                    args += ["--mode", data["mode"]]
                r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                return self.send_json({"ok": r.returncode == 0, "id": name, "out": (r.stdout + r.stderr).strip()}, 200 if r.returncode == 0 else 400)
            if path == "/api/run":
                job = run_job(data.get("cmd", ""), data.get("project"))
                return self.send_json({"job": job["id"]})
            m = re.match(r"^/api/project/(.+)/save$", path)
            if m:
                d = project_dir(m.group(1)); spec = data.get("spec")
                if not isinstance(spec, dict) or not isinstance(spec.get("scenes"), list):
                    return self.send_json({"error": "project.json must be an object with a 'scenes' list"}, 400)
                pj = d / "project.json"; (d / "project.json.bak").write_text(pj.read_text(encoding="utf-8"), encoding="utf-8")
                pj.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
                return self.send_json({"saved": True, "backup": "project.json.bak"})
            self.send_json({"error": "not found"}, 404)
        except (RuntimeError, ValueError) as e:
            self.send_json({"error": str(e)}, 409)
        except FileNotFoundError as e:
            self.send_json({"error": f"not found: {e}"}, 404)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def file(self, f: Path):                           # static files with HTTP Range (so videos can seek)
        if not f.exists() or not f.is_file():
            return self.send_json({"error": "not found"}, 404)
        size = f.stat().st_size; ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        rng = self.headers.get("Range"); start, end = 0, size - 1
        if rng and (m := re.match(r"bytes=(\d*)-(\d*)", rng)):
            if m.group(1):
                start = int(m.group(1)); end = int(m.group(2)) if m.group(2) else size - 1
            else:
                start = max(0, size - int(m.group(2)))
            end = min(end, size - 1)
            self.send_response(206); self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            self.send_response(200)
        self.send_header("Content-Type", ctype + ("; charset=utf-8" if ctype.startswith("text/") else ""))
        self.send_header("Accept-Ranges", "bytes"); self.send_header("Content-Length", str(end - start + 1)); self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        try:
            with open(f, "rb") as fh:
                fh.seek(start); left = end - start + 1
                while left > 0:
                    chunk = fh.read(min(1 << 20, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk); left -= len(chunk)
        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
            pass


def open_url(url):
    """Open the default browser: os.startfile on Windows, `open` on macOS, webbrowser elsewhere."""
    try:
        if os.name == "nt":
            os.startfile(url)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            webbrowser.open(url)
    except Exception:
        webbrowser.open(url)


def already_running(port):
    try:
        import urllib.request
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))      # never via a proxy
        with opener.open(f"http://127.0.0.1:{port}/api/state", timeout=1.5) as r:
            return r.status == 200 and r.headers.get("Server", "").startswith("VideoStudio")
    except Exception:
        return False


def log(msg):
    """Start-up log (helps when the app is launched from a shortcut and its window closes)."""
    try:
        WORK.mkdir(parents=True, exist_ok=True)
        with open(WORK / "app.log", "a", encoding="utf-8") as fh:
            fh.write(time.strftime("%Y-%m-%d %H:%M:%S ") + str(msg) + "\n")
    except Exception:
        pass


def serve(port=8765, open_browser=True):
    log(f"start pid={os.getpid()} exe={sys.executable} cwd={os.getcwd()}")
    try:
        _serve(port, open_browser)
    except BaseException as e:
        import traceback
        log("stopped: " + "".join(traceback.format_exception(e)).strip())
        raise


def _serve(port, open_browser):
    if already_running(port):                          # the app is already open (another window): just show it
        url = f"http://127.0.0.1:{port}/"
        print(f"Filmlux Studio is already running: {url}")
        if open_browser:
            open_url(url)
        return
    srv = None
    for p in range(port, port + 20):
        try:
            srv = ThreadingHTTPServer(("127.0.0.1", p), Handler); port = p; break
        except OSError:
            continue
    if srv is None:
        raise SystemExit("No free port found near 8765.")
    url = f"http://127.0.0.1:{port}/"
    log(f"listening {url}")
    print(f"\n  Filmlux Studio: {url}\n\n  Your browser should open by itself. If it doesn't, paste the link above into Edge or Chrome."
          f"\n  Keep this window open while you use the app. Close it (or press Ctrl+C) to stop.\n", flush=True)
    if open_browser:
        threading.Timer(.6, lambda: open_url(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("stopped")
