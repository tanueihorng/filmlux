"""Natural neural voiceover (Microsoft neural voices via edge-tts), cached per line, trimmed and levelled.

The narration TEXT is sent to Microsoft's online speech service: never put personal data in narration.
Offline alternative: voice "local" uses the computer's own speech engine (Windows SAPI through COM, macOS `say`,
Linux `espeak-ng`). Nothing leaves the machine, but it sounds robotic: use it for drafts or sensitive narration.
Behind a corporate HTTPS proxy, `truststore` makes Python use the Windows certificate store (checks stay on).
"""
from __future__ import annotations

import asyncio
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import av
import numpy as np

from .config import SR

VOICES = {
    "en-US-AvaNeural":      "US female, warm and natural. Default; the team's favourite.",
    "en-US-AndrewNeural":   "US male, calm and trustworthy. Leadership, serious topics.",
    "en-US-EmmaNeural":     "US female, bright and friendly. Onboarding, upbeat explainers.",
    "en-US-BrianNeural":    "US male, relaxed and conversational. Casual walkthroughs.",
    "en-GB-SoniaNeural":    "UK female, crisp. Formal or international audiences.",
    "en-GB-RyanNeural":     "UK male, steady. Formal narration.",
    "en-SG-LunaNeural":     "Singapore English female. Local audiences.",
    "en-SG-WayneNeural":    "Singapore English male. Local audiences.",
    "en-AU-NatashaNeural":  "Australian female, warm.",
    "en-IN-NeerjaNeural":   "Indian English female, clear.",
    "zh-CN-XiaoxiaoNeural": "Mandarin female (for translated narration).",
    "ms-MY-YasminNeural":   "Malay female (for translated narration).",
    "ta-IN-PallaviNeural":  "Tamil female (for translated narration).",
    "local":                "Offline: this computer's own voice. Private (no internet) but robotic. Drafts, sensitive scripts.",
}
DEFAULT_VOICE, DEFAULT_RATE = "en-US-AvaNeural", "-4%"
VO_DB = -17.0          # target RMS of speech (dBFS)


def is_local(voice) -> bool:
    return str(voice or "").split(":")[0] == "local"


def clip_path(cache: Path, text: str, voice: str, rate: str) -> Path:
    return cache / (hashlib.sha1(f"{voice}|{rate}|{text}".encode()).hexdigest()[:16] + (".wav" if is_local(voice) else ".mp3"))


def _rate_pct(rate) -> float:
    try:
        return float(str(rate or "0").strip().rstrip("%"))
    except ValueError:
        return 0.0


def _sapi_to_wav(text: str, out: Path, rate) -> None:
    """Windows SAPI 5 through its COM interface (ctypes only): works where PowerShell and script hosts are locked down."""
    import ctypes
    from ctypes import POINTER, byref, c_long, c_ulong, c_ulonglong, c_void_p, c_wchar_p, HRESULT, WINFUNCTYPE
    from ctypes import wintypes

    class GUID(ctypes.Structure):
        _fields_ = [("a", wintypes.DWORD), ("b", wintypes.WORD), ("c", wintypes.WORD), ("d", ctypes.c_ubyte * 8)]

    class WFX(ctypes.Structure):
        _fields_ = [("tag", wintypes.WORD), ("ch", wintypes.WORD), ("sr", wintypes.DWORD), ("bps", wintypes.DWORD),
                    ("align", wintypes.WORD), ("bits", wintypes.WORD), ("cb", wintypes.WORD)]

    def guid(s):
        h = s.replace("-", ""); g = GUID(int(h[:8], 16), int(h[8:12], 16), int(h[12:16], 16)); g.d[:] = bytes.fromhex(h[16:]); return g

    def method(obj, index, *argtypes):
        vtbl = ctypes.cast(obj, POINTER(POINTER(c_void_p))).contents
        return WINFUNCTYPE(HRESULT, c_void_p, *argtypes)(vtbl[index])

    ole = ctypes.OleDLL("ole32"); ole.CoInitialize(None)
    vo, st = c_void_p(), c_void_p()
    ole.CoCreateInstance(byref(guid("96749377-3391-11D2-9EE3-00C04F797396")), None, 1, byref(guid("6C44DF74-72B9-4992-A1EC-EF996E0422D4")), byref(vo))  # SpVoice
    ole.CoCreateInstance(byref(guid("715D9C59-4442-11D2-9605-00C04F8EE628")), None, 1, byref(guid("12E3CCA9-7518-44C5-A5E7-BA5A79CB929E")), byref(st))  # SpStream
    try:
        fmt = WFX(1, 1, 24000, 48000, 2, 16, 0)
        method(st, 17, c_wchar_p, ctypes.c_int, POINTER(GUID), POINTER(WFX), c_ulonglong)(          # ISpStream::BindToFile
            st, str(out), 3, byref(guid("C31ADBAE-527F-4ff5-A230-F62BB61FF70C")), byref(fmt), 0)
        method(vo, 13, c_void_p, wintypes.BOOL)(vo, st, True)                                         # ISpVoice::SetOutput
        method(vo, 28, c_long)(vo, max(-10, min(10, round(_rate_pct(rate) / 10))))                    # ISpVoice::SetRate
        method(vo, 20, c_wchar_p, wintypes.DWORD, POINTER(c_ulong))(vo, text, 0, None)                 # ISpVoice::Speak
        method(st, 18)(st)                                                                             # ISpStream::Close
    finally:
        method(vo, 2)(vo); method(st, 2)(st)


def _local_to_wav(text: str, out: Path, voice: str, rate) -> None:
    name = str(voice).partition(":")[2]
    if os.name == "nt":
        _sapi_to_wav(text, out, rate)
    elif sys.platform == "darwin":
        args = ["say", "--data-format=LEI16@24000", "-o", str(out), "-r", str(int(175 * (1 + _rate_pct(rate) / 100)))]
        subprocess.run(args + (["-v", name] if name else []) + [text], check=True, capture_output=True)
    elif shutil.which("espeak-ng") or shutil.which("espeak"):
        exe = shutil.which("espeak-ng") or shutil.which("espeak")
        args = [exe, "-w", str(out), "-s", str(int(165 * (1 + _rate_pct(rate) / 100)))]
        subprocess.run(args + (["-v", name] if name else []) + [text], check=True, capture_output=True)
    else:
        raise RuntimeError("No offline speech engine found: install espeak-ng, or use an online voice")


def synth(lines, cache: Path, voice=DEFAULT_VOICE, rate=DEFAULT_RATE, force=False):
    """Fetch every missing clip. Returns how many were synthesised."""
    cache.mkdir(parents=True, exist_ok=True)
    todo = [t for t in dict.fromkeys(lines) if t and (force or not clip_path(cache, t, voice, rate).exists()
                                                      or clip_path(cache, t, voice, rate).stat().st_size == 0)]
    if not todo:
        return 0
    if is_local(voice):
        for t in todo:
            _local_to_wav(t, clip_path(cache, t, voice, rate), voice, rate)
        return len(todo)
    try:
        import truststore
        truststore.inject_into_ssl()
    except ImportError:
        pass
    try:
        import edge_tts
    except ImportError as e:
        raise RuntimeError("edge-tts is not installed: pip install -r requirements.txt") from e

    async def go():
        for t in todo:
            for attempt in range(3):
                try:
                    await edge_tts.Communicate(t, voice, rate=rate).save(str(clip_path(cache, t, voice, rate)))
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    await asyncio.sleep(1.5)
    try:
        asyncio.run(go())
    except Exception as e:
        raise RuntimeError(f"Voice synthesis failed ({e}). It needs internet access to Microsoft's speech service; "
                           "in a sandbox, enable network for this step.") from e
    return len(todo)


_cache = {}


def load(cache: Path, text: str, voice=DEFAULT_VOICE, rate=DEFAULT_RATE) -> np.ndarray:
    """Mono float32 at SR, silence trimmed, levelled to VO_DB, with tiny fades."""
    p = clip_path(cache, text, voice, rate)
    if p in _cache:
        return _cache[p]
    c = av.open(str(p)); rs = av.AudioResampler(format="fltp", layout="mono", rate=SR); parts = []
    for f in c.decode(audio=0):
        parts += [g.to_ndarray()[0] for g in rs.resample(f)]
    parts += [g.to_ndarray()[0] for g in rs.resample(None)]
    c.close()
    x = np.concatenate(parts).astype(np.float32) if parts else np.zeros(SR // 10, np.float32)
    a = np.abs(x); k = 480; env = np.convolve(a, np.ones(k) / k, "same"); on = np.where(env > .01)[0]
    if len(on):
        x = x[max(0, on[0] - 1200): on[-1] + 2400]
    loud = x[np.abs(x) > .02]
    rms = np.sqrt(np.mean(loud ** 2)) if loud.size else 1
    x = x * (10 ** (VO_DB / 20) / max(rms, 1e-4))
    f = np.linspace(0, 1, 240, dtype=np.float32); x[:240] *= f; x[-240:] *= f[::-1]
    _cache[p] = x.astype(np.float32)
    return _cache[p]


def duration(cache: Path, text: str, voice=DEFAULT_VOICE, rate=DEFAULT_RATE) -> float:
    return len(load(cache, text, voice, rate)) / SR
