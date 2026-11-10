"""Filmlux command line. Run from this folder. On macOS/Linux type python3 instead of python.

  python studio.py check                         is this machine ready? (packages, browser, voice, fonts)
  python studio.py app                           open the local Studio app in your browser (projects, inbox upload, previews, renders, compare)
  python studio.py new <name> [--pack P] [--theme T] [--format F]   create projects/<name>/ from a pack (python studio.py packs)
  python studio.py plan <project>                fitted timeline: every scene's start, length, voice length
  python studio.py stills <project> [t1,t2,...]  preview frames (default: one per scene) + a sheet, in <temp>/video_studio/stills
  python studio.py audio <project>               the whole soundtrack as a wav (voice + music), ~1 min
  python studio.py qa <project>                  layout + content checks (overflow, safe area, long lines, missing files)
  python studio.py render <project> [--force]    full render -> projects/<name>/renders/<name>_vN.mp4 (+ .srt, contact sheet, QA)
  python studio.py thumb <project> [scene]       thumbnail / poster frame PNG
  python studio.py imagegen <project> [--check]  optional AI images: list what to generate (assets/gen/REQUESTS.md) / verify them
  python studio.py motion                        list motion styles and transitions
  python studio.py cutout <in.png> <out.png>     remove a flat green (#00ff00) background -> transparent PNG (for parallax cutouts)
  python studio.py packs | themes                style packs and visual themes
  python studio.py voices                        list the neural voices
  python studio.py moods                         list the music moods
  python studio.py samples                       rebuild the gallery stills + voice/music samples used by START_HERE.html
  python studio.py shortcut                      a double-click "Filmlux" launcher on the Desktop (Windows .lnk, macOS .command)

<project> is a folder name under projects/ (or a path).
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "engine"))


def proj(name):
    from vstudio.render import Project
    p = Path(name)
    if not p.exists():
        p = ROOT / "projects" / name
    return Project(p)


def cmd_check(_):
    ok = True
    def rep(good, msg):
        nonlocal ok; ok &= good; print(("  OK   " if good else "  FAIL ") + msg)
    import platform
    from vstudio.config import PY
    print(f"{platform.system()} {platform.release()} ({platform.machine()}), Python {sys.version.split()[0]}")
    rep(sys.version_info >= (3, 10), "Python 3.10+")
    for m in ("av", "numpy", "PIL", "websocket", "edge_tts", "truststore"):
        try:
            importlib.import_module(m); rep(True, m)
        except Exception as e:
            rep(m == "truststore", f"{m}: {e}  ->  {PY} -m pip install -r requirements.txt" + ("  (optional)" if m == "truststore" else ""))
    try:
        from vstudio.config import edge_path
        rep(True, "browser: " + edge_path())
    except Exception as e:
        rep(False, str(e))
    for f in ("InterDisplay-Regular.ttf", "InterDisplay-Medium.ttf", "InterDisplay-SemiBold.ttf"):
        rep((ROOT / "assets" / "fonts" / f).exists(), f"font {f}")
    try:
        from vstudio.config import h264_encoder
        rep(True, f"H.264 encoder ({h264_encoder()[0]})")
    except Exception as e:
        rep(False, f"H.264 encoder: {e}")
    try:
        from vstudio.config import WORK
        WORK.mkdir(parents=True, exist_ok=True); (WORK / ".w").write_text("ok"); (WORK / ".w").unlink(); rep(True, f"temp folder writable ({WORK})")
    except Exception as e:
        rep(False, f"temp folder: {e}")
    try:
        from vstudio.capture import Browser
        from vstudio.config import STAGE
        b = Browser(STAGE, 640, 360); b.close(); rep(True, "headless capture works")
    except Exception as e:
        rep(False, f"headless capture: {e}")
    print(f"\nReady. Next: {PY} studio.py app   (or ask your agent: Read AGENTS.md and make my video)" if ok else "\nFix the FAIL lines above.")


def cmd_new(a):
    src = ROOT / "packs" / a.pack / "starter"
    if not src.exists():
        raise SystemExit(f"unknown pack '{a.pack}'. Packs: " + ", ".join(sorted(d.name for d in (ROOT / "packs").iterdir() if (d / "starter").exists())))
    dst = ROOT / "projects" / a.name
    if dst.exists():
        raise SystemExit(f"{dst} already exists")
    shutil.copytree(src, dst)
    for d in ("assets", "renders"):
        (dst / d).mkdir(exist_ok=True)
    if a.theme or a.format:
        pj = dst / "project.json"; spec = json.loads(pj.read_text(encoding="utf-8"))
        if a.theme:
            if not (ROOT / "themes" / f"{a.theme}.json").exists():
                raise SystemExit(f"unknown theme '{a.theme}' (python studio.py themes)")
            spec["theme"] = a.theme
        if a.format:
            spec["format"] = a.format
        pj.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"created {dst}  (pack: {a.pack}). Edit brief.md, script.md and project.json, then: python studio.py plan {a.name}")


def cmd_packs(_):
    for d in sorted((ROOT / "packs").iterdir()):
        f = d / "PACK.md"
        if f.exists():
            line = next((l for l in f.read_text(encoding="utf-8").splitlines() if l.startswith("**For:**")), "")
            print(f"  {d.name:18s} {line.replace('**For:**', '').strip()}")


def cmd_themes(_):
    for f in sorted((ROOT / "themes").glob("*.json")):
        t = json.loads(f.read_text(encoding="utf-8"))
        print(f"  {f.stem:10s} {t.get('about', t.get('name', ''))}  [motion {t.get('motion', 'smooth')}, transition {t.get('transition', 'fade')}]")


def cmd_motion(_):
    from vstudio.render import MOTIONS, TRANSITIONS, DIRECTIONS
    print("motion (how elements arrive; theme default, project 'motion', or per scene):")
    print("  " + ", ".join(MOTIONS))
    print("transition (how a scene arrives; 'kind' or 'kind:direction'):")
    print("  " + ", ".join(k for k in TRANSITIONS if k not in ("dissolve", "push", "cut")))
    print("  directions (slide, wipe, cube): " + ", ".join(DIRECTIONS))
    print("  transition_timing: ease (default), linear, spring.  Details and taste notes: SPEC.md > Motion and transitions")


def cmd_cutout(a):
    """Remove a flat key-colour background (default: sampled from the border, usually #00ff00) -> transparent PNG."""
    import numpy as np
    from PIL import Image
    im = np.asarray(Image.open(a.input).convert("RGB"), np.float32)
    border = np.concatenate([im[0], im[-1], im[:, 0], im[:, -1]])
    key = np.median(border, axis=0) if not a.key else np.array([int(a.key.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)], np.float32)
    d = np.linalg.norm(im - key, axis=2) / 441.7                      # 0 = key colour, 1 = far away
    alpha = np.clip((d - a.tolerance) / max(1e-3, a.softness), 0, 1)
    g = key.argmax()                                                   # despill: pull the key channel down on the edges
    others = np.delete(im, g, axis=2).max(axis=2); im[..., g] = np.minimum(im[..., g], np.maximum(others, im[..., g] * alpha))
    out = np.dstack([im, alpha * 255]).clip(0, 255).astype(np.uint8)
    Path(a.output).parent.mkdir(parents=True, exist_ok=True); Image.fromarray(out, "RGBA").save(a.output)
    print(f"  cutout -> {a.output}  (key {'#%02x%02x%02x' % tuple(int(v) for v in key)}, {100 * (alpha < .5).mean():.0f}% removed)")


def cmd_imagegen(a):
    from vstudio import imagegen
    p = proj(a.project)
    if a.check:
        ok = imagegen.check(p)
        sys.exit(0 if ok else 1)
    imagegen.requests(p)


def cmd_app(a):
    from vstudio.app import serve
    serve(port=a.port, open_browser=not a.no_browser)


def cmd_plan(a):
    from vstudio.render import plan
    plan(proj(a.project).prepare())


def cmd_stills(a):
    from vstudio.render import stills
    times = [float(x) for x in a.times.split(",")] if a.times else None
    stills(proj(a.project).prepare(), times)


def cmd_audio(a):
    from vstudio.render import audio_preview
    audio_preview(proj(a.project).prepare())


def cmd_qa(a):
    from vstudio.render import Frames, qa
    p = proj(a.project).prepare(); fr = Frames(p)
    try:
        issues = qa(p, fr)
    finally:
        fr.close()
    for lvl, where, msg in issues:
        print(f"  {lvl:5s} {where}: {msg}")
    ne, nw = sum(l == "ERROR" for l, _, _ in issues), sum(l == "WARN" for l, _, _ in issues)
    print("no issues" if not issues else f"{ne} error(s), {nw} warning(s)" + ("  (errors block the render; warnings are craft advice: fix them or keep them on purpose)" if nw else ""))


def cmd_render(a):
    from vstudio.render import render
    render(proj(a.project).prepare(), force=a.force)


def cmd_thumb(a):
    from vstudio.render import thumbnail
    thumbnail(proj(a.project).prepare(), int(a.scene or 0))


def cmd_voices(_):
    from vstudio.voice import VOICES, DEFAULT_VOICE
    for k, v in VOICES.items():
        print(f"  {k:24s} {v}{'   (default)' if k == DEFAULT_VOICE else ''}")


def cmd_moods(_):
    from vstudio.audio import MOODS
    for k, v in MOODS.items():
        print(f"  {k:10s} {v['desc']}")
    print("  none       no music (voice only)")


def write_lnk(path: Path, target: Path, args: str, workdir: Path, desc: str, icon: Path | None = None):
    """Create a Windows shortcut with the shell's own IShellLink API (via ctypes): the same call Explorer uses.
    No PowerShell (often locked down), no extra packages."""
    import ctypes
    from ctypes import POINTER, byref, c_void_p, c_wchar_p, HRESULT, WINFUNCTYPE
    from ctypes import wintypes

    class GUID(ctypes.Structure):
        _fields_ = [("a", wintypes.DWORD), ("b", wintypes.WORD), ("c", wintypes.WORD), ("d", ctypes.c_ubyte * 8)]

    def guid(s):
        h = s.replace("-", ""); g = GUID(int(h[:8], 16), int(h[8:12], 16), int(h[12:16], 16)); g.d[:] = bytes.fromhex(h[16:]); return g

    ole = ctypes.OleDLL("ole32")
    ole.CoInitialize(None)
    link = c_void_p()
    ole.CoCreateInstance(byref(guid("00021401-0000-0000-C000-000000000046")), None, 1,           # CLSID_ShellLink, CLSCTX_INPROC_SERVER
                         byref(guid("000214F9-0000-0000-C000-000000000046")), byref(link))     # IID_IShellLinkW

    def method(obj, index, *argtypes):
        vtbl = ctypes.cast(obj, POINTER(POINTER(c_void_p))).contents
        return WINFUNCTYPE(HRESULT, c_void_p, *argtypes)(vtbl[index])

    method(link, 20, c_wchar_p)(link, str(target))                       # SetPath
    method(link, 11, c_wchar_p)(link, args)                              # SetArguments
    method(link, 9, c_wchar_p)(link, str(workdir))                       # SetWorkingDirectory
    method(link, 7, c_wchar_p)(link, desc)                               # SetDescription
    method(link, 17, c_wchar_p, ctypes.c_int)(link, str(icon or target), 0)   # SetIconLocation
    pf = c_void_p()
    method(link, 0, POINTER(GUID), POINTER(c_void_p))(link, byref(guid("0000010B-0000-0000-C000-000000000046")), byref(pf))   # QueryInterface IPersistFile
    method(pf, 6, c_wchar_p, wintypes.BOOL)(pf, str(path), True)         # IPersistFile::Save
    method(pf, 2)(pf); method(link, 2)(link)                             # Release


def _desktop() -> Path:
    if os.name == "nt":
        import winreg
        try:                                           # the real Desktop (often redirected to OneDrive)
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as k:
                return Path(os.path.expandvars(winreg.QueryValueEx(k, "Desktop")[0]))
        except OSError:
            pass
    return Path.home() / "Desktop"


def cmd_shortcut(_):
    """A double-click 'Filmlux' launcher on the Desktop. It holds this machine's paths, so it is made per
    computer and never shipped in the zip. Run it again if you move the folder.
      Windows: Filmlux.lnk -> python.exe (works where .bat files and double-clicked .py files are blocked)
      macOS:   Filmlux.command (opens Terminal, starts the app, opens the browser)
      Linux:   video-studio.desktop"""
    desktop = _desktop(); desktop.mkdir(parents=True, exist_ok=True)
    exe = Path(sys.executable)
    try:
        if os.name == "nt":
            if exe.name.lower() == "pythonw.exe":
                exe = exe.with_name("python.exe")
            out = desktop / "Filmlux.lnk"
            write_lnk(out, exe, f'"{ROOT / "studio.py"}" app', ROOT, "Open Filmlux Studio", ROOT / "assets" / "brand" / "filmlux.ico")
        elif sys.platform == "darwin":
            out = desktop / "Filmlux.command"
            out.write_text(f'#!/bin/bash\n# Opens Filmlux Studio. Keep this window open while you use it; close it to stop.\n'
                           f'cd "{ROOT}" || exit 1\nexec "{exe}" studio.py app\n', encoding="utf-8")
            out.chmod(0o755)
        else:
            out = desktop / "video-studio.desktop"
            out.write_text(f"[Desktop Entry]\nType=Application\nName=Filmlux\nComment=Open Filmlux Studio\n"
                           f'Exec="{exe}" "{ROOT / "studio.py"}" app\nPath={ROOT}\nIcon={ROOT / "assets" / "brand" / "filmlux-mark.png"}\nTerminal=true\n', encoding="utf-8")
            out.chmod(0o755)
    except OSError as e:
        raise SystemExit(f"could not create the launcher: {e}")
    for old in ("Video Studio.lnk", "Video Studio.command", "video-studio.desktop"):   # launcher from before the rename
        try:
            (desktop / old).unlink()
        except OSError:
            pass
    print(f"  created {out}")
    print("Double-click 'Filmlux' on your Desktop to open the app. (Run this again if you move the folder.)")
    if sys.platform == "darwin":
        print("First time only: if macOS says it can't verify the file, right-click it > Open > Open.")


def cmd_samples(_):
    sys.path.insert(0, str(ROOT / "tools"))
    import make_samples
    make_samples.main()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("check").set_defaults(f=cmd_check)
    n = sp.add_parser("new"); n.add_argument("name"); n.add_argument("--pack", default="motion_promo"); n.add_argument("--theme"); n.add_argument("--format", choices=["16:9", "9:16", "1:1", "4:5"]); n.set_defaults(f=cmd_new)
    g = sp.add_parser("imagegen"); g.add_argument("project"); g.add_argument("--check", action="store_true"); g.set_defaults(f=cmd_imagegen)
    g = sp.add_parser("cutout"); g.add_argument("input"); g.add_argument("output"); g.add_argument("--key", default="")
    g.add_argument("--tolerance", type=float, default=.18); g.add_argument("--softness", type=float, default=.12); g.set_defaults(f=cmd_cutout)
    ap_ = sp.add_parser("app"); ap_.add_argument("--port", type=int, default=8765); ap_.add_argument("--no-browser", action="store_true"); ap_.set_defaults(f=cmd_app)
    sp.add_parser("packs").set_defaults(f=cmd_packs); sp.add_parser("themes").set_defaults(f=cmd_themes); sp.add_parser("motion").set_defaults(f=cmd_motion)
    for c, f in (("plan", cmd_plan), ("audio", cmd_audio), ("qa", cmd_qa)):
        x = sp.add_parser(c); x.add_argument("project"); x.set_defaults(f=f)
    s = sp.add_parser("stills"); s.add_argument("project"); s.add_argument("times", nargs="?"); s.set_defaults(f=cmd_stills)
    r = sp.add_parser("render"); r.add_argument("project"); r.add_argument("--force", action="store_true"); r.set_defaults(f=cmd_render)
    t = sp.add_parser("thumb"); t.add_argument("project"); t.add_argument("scene", nargs="?"); t.set_defaults(f=cmd_thumb)
    sp.add_parser("voices").set_defaults(f=cmd_voices); sp.add_parser("moods").set_defaults(f=cmd_moods)
    sp.add_parser("samples").set_defaults(f=cmd_samples)
    sp.add_parser("shortcut").set_defaults(f=cmd_shortcut)
    a = ap.parse_args(); a.f(a)
