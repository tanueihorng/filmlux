"""Paths, formats and machine settings for Filmlux (Windows, macOS and Linux)."""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]            # the Video_Studio folder
ENGINE = ROOT / "engine"
STAGE = ENGINE / "stage" / "stage.html"
ASSETS = ROOT / "assets"
THEMES = ROOT / "themes"
PROJECTS = ROOT / "projects"
INBOX = ROOT / "inbox"
WORK = Path(tempfile.gettempdir()) / "video_studio"

FPS = 30
SR = 48000
FORMATS = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}

IS_WIN, IS_MAC = os.name == "nt", sys.platform == "darwin"
PY = "python" if IS_WIN else "python3"                 # what to type in a terminal on this OS (for messages)


def edge_path() -> str:
    """A Chromium browser for headless capture: Edge or Chrome (Chromium/Brave also work). Override with VS_BROWSER."""
    home = Path.home()
    mac_apps = [("Microsoft Edge", "Microsoft Edge"), ("Google Chrome", "Google Chrome"), ("Chromium", "Chromium"), ("Brave Browser", "Brave Browser")]
    local = os.environ.get("LOCALAPPDATA", "")
    cands = [os.environ.get("VS_BROWSER", ""),
             r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
             r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
             r"C:\Program Files\Google\Chrome\Application\chrome.exe",
             r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
             str(Path(local) / "Google" / "Chrome" / "Application" / "chrome.exe") if local else "",
             *[f"/Applications/{a}.app/Contents/MacOS/{b}" for a, b in mac_apps],
             *[str(home / "Applications" / f"{a}.app" / "Contents" / "MacOS" / b) for a, b in mac_apps],
             *[shutil.which(n) or "" for n in ("microsoft-edge", "microsoft-edge-stable", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser")]]
    for c in cands:
        if c and Path(c).exists():
            return c
    raise RuntimeError("No Edge/Chrome found. Install Microsoft Edge or Google Chrome, or set VS_BROWSER to a Chromium browser executable.")


def h264_encoder():
    """(codec name, options) for H.264. libx264 is in the PyAV wheels; the others are fallbacks for unusual builds."""
    import av
    for name, opts in (("libx264", lambda crf: {"crf": str(crf), "preset": "medium"}),
                       ("h264_videotoolbox", lambda crf: {"b": "16M", "allow_sw": "1"}),          # macOS hardware encoder
                       ("libopenh264", lambda crf: {"b": "16M"}),
                       ("h264_mf", lambda crf: {"b": "16M"})):                                     # Windows Media Foundation
        try:
            av.codec.Codec(name, "w")
            return name, opts
        except Exception:
            continue
    raise RuntimeError("No H.264 encoder in this PyAV build. Run: pip install --upgrade av")
