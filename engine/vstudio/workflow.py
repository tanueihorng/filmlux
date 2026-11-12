"""Agent workflow helpers: one exact next step, approval gates, feedback rounds, a scorecard, exports.

Built so a small or local model can produce a solid video by following instructions instead of planning:
`python studio.py next <name>` always says what to do now, which command to run, and when to stop for the user.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import shutil
from pathlib import Path

from .config import ROOT, WORK

GATES = ("brief", "script", "images", "stills")


# ---------------------------------------------------------------- state (approvals and the last clean qa)
def _state_path(d: Path) -> Path:
    return d / ".state.json"


def load_state(d: Path) -> dict:
    try:
        return json.loads(_state_path(d).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(d: Path, st: dict) -> None:
    _state_path(d).write_text(json.dumps(st, indent=2), encoding="utf-8")


def spec_hash(d: Path) -> str:
    try:
        return hashlib.sha1((d / "project.json").read_bytes()).hexdigest()[:16]
    except OSError:
        return ""


def approve(d: Path, gate: str) -> None:
    if gate not in GATES:
        raise SystemExit(f"unknown gate '{gate}'. Gates: {', '.join(GATES)}")
    st = load_state(d); st.setdefault("approved", {})[gate] = {"at": _now(), "spec": spec_hash(d)}
    save_state(d, st)
    print(f"approved: {gate}  (recorded in {_state_path(d).name}). Next: python studio.py next {d.name}")


def record_qa(d: Path, issues, mode: str) -> None:
    """Remember that this exact project.json passed qa (guided: no issues; creative: no errors)."""
    st = load_state(d)
    ok = not issues if mode == "guided" else not any(l == "ERROR" for l, _, _ in issues)
    st["qa"] = {"spec": spec_hash(d), "ok": ok, "at": _now()}
    save_state(d, st)


def _now():
    return _dt.datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------- template detection
def _starter_files(name: str):
    return [f for f in (ROOT / "packs").glob(f"*/starter/{name}") if f.exists()]


def _is_template(path: Path) -> bool:
    if not path.exists():
        return True
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if not text or "<video title>" in text or "What the video must achieve (one sentence)" in text:
        return True
    return any(text == f.read_text(encoding="utf-8", errors="ignore").strip() for f in _starter_files(path.name))


def _renders(d: Path):
    rd = d / "renders"
    vs = []
    for f in rd.glob("*_v*.mp4") if rd.exists() else []:
        m = re.search(r"_v(\d+)\.mp4$", f.name)
        if m:
            vs.append((int(m.group(1)), f))
    return [f for _, f in sorted(vs)]


def _open_feedback(d: Path):
    f = d / "feedback.md"
    if not f.exists():
        return []
    return [l.strip()[6:] for l in f.read_text(encoding="utf-8").splitlines() if l.strip().startswith("- [ ]")]


# ---------------------------------------------------------------- next
def next_step(d: Path, py: str = "python") -> None:
    """Print the one next step. Deterministic: it reads files and the recorded state, it never guesses."""
    name = d.name if d.parent == ROOT / "projects" else str(d)
    spec = json.loads((d / "project.json").read_text(encoding="utf-8"))
    mode = "creative" if spec.get("mode") == "creative" else "guided"
    st = load_state(d); ap = st.get("approved", {}); h = spec_hash(d)
    stills_sheet = WORK / "stills" / d.name / "_stills_sheet.jpg"
    renders = _renders(d)

    def say(status, now, run=None, gate=None):
        print(f"Project: {name}  ({mode} mode)")
        for k, v in status:
            print(f"  [{'x' if v else ' '}] {k}")
        print(f"\nNEXT: {now}")
        if run:
            print(f"RUN:  {run}")
        if gate:
            print(f"STOP: {gate}")
        print(f"THEN: {py} studio.py next {name}")

    from .render import placeholder_checks, Project
    prj = Project(d)
    pending = [sc for sc in prj.scenes if sc.get("_pending")] + [ly for sc in prj.scenes for ly in sc.get("layers") or [] if ly.get("_pending")]
    uses_gen = any(sc.get("gen") for sc in prj.scenes) or any(ly.get("gen") for sc in prj.scenes for ly in sc.get("layers") or [])
    for sc in prj.scenes:
        sc.setdefault("dur", 5.0)
    leftovers = placeholder_checks(prj)
    qa_ok = st.get("qa", {}).get("spec") == h and st.get("qa", {}).get("ok")
    stills_fresh = stills_sheet.exists() and stills_sheet.stat().st_mtime >= (d / "project.json").stat().st_mtime
    last = renders[-1] if renders else None
    render_fresh = last is not None and last.stat().st_mtime >= (d / "project.json").stat().st_mtime
    fb = _open_feedback(d)
    status = [("brief.md written", not _is_template(d / "brief.md")), ("brief approved", "brief" in ap),
              ("script.md written", not _is_template(d / "script.md")), ("script and look approved", "script" in ap),
              ("project.json filled in (no template text)", not leftovers and not _is_template(d / "script.md"))]
    if uses_gen:
        status += [("AI images generated", not pending), ("AI images approved", "images" in ap)]
    status += [("stills made for this project.json", stills_fresh), ("qa passed for this project.json", qa_ok),
               ("stills approved", "stills" in ap and ap["stills"].get("spec") == h), ("rendered", render_fresh)]

    if _is_template(d / "brief.md"):
        return say(status, "Write brief.md: copy templates/brief.md, fill every row from the user's answers and the files in inbox/ "
                           "(read inbox/brief.json first if it exists). Keep it short.", None,
                   f"Show the user brief.md and ask them to approve it. When they say yes, run: {py} studio.py approve {name} brief")
    if "brief" not in ap:
        return say(status, "Ask the user to approve brief.md (change it until they do).", f"{py} studio.py approve {name} brief",
                   "Wait for the user's yes before running the command.")
    if _is_template(d / "script.md"):
        return say(status, "Start from the user's Vision in brief.md (their own words): map each part to a scene type and layout, and plan a custom "
                           f"scene ({py} studio.py scene {name} <scene>) where nothing fits, with a \"why\" quoting them. "
                           f"Read the Beats and Treatments in packs/{spec.get('pack', '<pack>')}/PACK.md. Unless the user already chose a structure "
                           "(brief.md), write 2-3 treatments at the top of script.md: different structures (scene types and layouts per beat), "
                           "not only different looks. Then fill the storyboard (templates/storyboard.md) for your recommended one: one row per scene "
                           "with beat, scene type and layout, on-screen text, narration (under 25 words) and the visual. Vary the layout "
                           f"({py} studio.py scenes). Then propose a look (theme, motion, caption style), one line each on why.", f"{py} studio.py scenes",
                   f"Show the user the treatments, script.md and the look; ask which treatment they want. When they approve, run: {py} studio.py approve {name} script")
    if "script" not in ap:
        return say(status, "Ask the user to pick a treatment, approve script.md and pick a look (rewrite the storyboard if they pick another treatment).", f"{py} studio.py approve {name} script",
                   "Wait for the user's yes before running the command.")
    if leftovers:
        where = "; ".join(f"{w}: {m.split(' -> ')[0]}" for _, w, m in leftovers[:4])
        return say(status, f"Fill in project.json from script.md. Template text is still in it ({where}). Use only scene types and layouts listed by "
                           f"'{py} studio.py scenes'; one scene per script row, with the layout from the storyboard.", f"{py} studio.py plan {name}")
    if pending:
        return say(status, f"{len(pending)} AI image(s) are not made yet. List them, make each with your image tool (IMAGEGEN.md), then check.",
                   f"{py} studio.py imagegen {name}   then   {py} studio.py imagegen {name} --check")
    if uses_gen and "images" not in ap:
        return say(status, "Show the user every AI image and say which are AI-made.", f"{py} studio.py approve {name} images",
                   "Wait for the user's yes before running the command.")
    if not stills_fresh:
        return say(status, "Make preview stills of this version. Open _stills_sheet.jpg and look; if you cannot open images, read "
                           "stills_report.txt and fix every PROBLEM line.", f"{py} studio.py stills {name}")
    if not qa_ok:
        return say(status, "Run qa and fix every line it prints (each says '-> fix:' with the exact change). "
                           + ("Guided mode: it must end with 'no issues'." if mode == "guided" else "Creative mode: no ERRORs; fix each WARN or keep it on purpose and tell the user why."),
                   f"{py} studio.py qa {name}")
    if not ("stills" in ap and ap["stills"].get("spec") == h):
        return say(status, "Show the user the stills sheet (and the audio preview if they want it).", f"{py} studio.py approve {name} stills",
                   "Wait for the user's yes before running the command.")
    if not render_fresh:
        return say(status, "Render the video. It takes about 6 minutes per minute of video; run it in the background. "
                           f"(Optional first: {py} studio.py render {name} --draft for a quick pacing check.)", f"{py} studio.py render {name}")
    if fb:
        return say(status, f"{len(fb)} feedback item(s) are open in feedback.md: change only what they ask, tick each one (- [x]), then stills, qa, render.",
                   f"{py} studio.py stills {name}")
    return say(status, f"Review {last.name}: open {last.with_suffix('.contact.jpg').name}, check the first 10 s, every scene change and the "
                       f"last 10 s. Report the path, length and the scorecard. Ask the user for feedback.",
               f"{py} studio.py score {name}",
               f"When the user gives feedback, record it: {py} studio.py feedback {name} \"<their words>\"")


# ---------------------------------------------------------------- feedback rounds
def feedback(d: Path, text: str) -> None:
    rs = _renders(d); ver = re.search(r"_v(\d+)\.mp4$", rs[-1].name).group(1) if rs else "draft"
    items = [x.strip(" -•\t") for x in re.split(r"\n|;", text) if x.strip(" -•\t")]
    f = d / "feedback.md"
    head = "" if f.exists() else "# Feedback\n\nOne section per version. Tick an item (- [x]) when the change is made.\n"
    block = f"\n## On v{ver} ({_dt.date.today().isoformat()})\n" + "".join(f"- [ ] {i}\n" for i in items)
    with open(f, "a", encoding="utf-8") as fh:
        fh.write(head + block)
    print(f"recorded {len(items)} item(s) in {f}. Change only what they ask, tick each, then: python studio.py next {d.name}")


# ---------------------------------------------------------------- scorecard
def metrics(prj, issues) -> dict:
    from .render import LOUD_TRANSITIONS, _onscreen_words
    sc_ = prj.scenes
    voiced = [sc for sc in sc_ if sc.get("_voice")]
    wpm = (sum(len(sc["say"].split()) for sc in voiced) / sum(sc["_voice"] for sc in voiced) * 60) if voiced else 0
    over = sum(1 for sc in sc_ if sc["type"] not in ("screen", "html") and _onscreen_words(sc) > max(16, 4 * sc.get("dur", 5)))
    static = max([sc["dur"] for sc in sc_ if sc["type"] not in ("screen", "html")] or [0])
    loud = sum(1 for i, sc in enumerate(sc_) if i and str(sc.get("transition") or "").partition(":")[0] in LOUD_TRANSITIONS)
    return {"length_s": round(prj.total, 1), "scenes": len(sc_), "scene_types": len({sc["type"] for sc in sc_}),
            "narration_wpm": round(wpm), "scenes_too_wordy": over, "longest_static_s": round(static, 1),
            "loud_transitions": loud, "qa_errors": sum(l == "ERROR" for l, _, _ in issues),
            "qa_warnings": sum(l == "WARN" for l, _, _ in issues)}


def save_score(prj, out: Path, issues) -> Path:
    p = out.with_suffix(".score.json")
    p.write_text(json.dumps({"version": out.name, "at": _now(), "metrics": metrics(prj, issues)}, indent=2), encoding="utf-8")
    return p


# lower is better, except where noted; "band" metrics are best inside a range
_BETTER = {"scene_types": "higher", "narration_wpm": (130, 165), "length_s": None, "scenes": None}


def score(prj, issues) -> None:
    now = metrics(prj, issues)
    prev_f = sorted((prj.dir / "renders").glob("*.score.json"), key=lambda f: f.stat().st_mtime) if (prj.dir / "renders").exists() else []
    prev = json.loads(prev_f[-1].read_text(encoding="utf-8")) if prev_f else None
    print(f"Scorecard: {prj.title}" + (f"  (compared with {prev['version']})" if prev else "  (no earlier render to compare)"))
    for k, v in now.items():
        was = prev["metrics"].get(k) if prev else None
        rule = _BETTER.get(k, "lower"); verdict = ""
        if was is not None and was != v and rule:
            if isinstance(rule, tuple):
                dist = lambda x: 0 if rule[0] <= x <= rule[1] else min(abs(x - rule[0]), abs(x - rule[1]))
                verdict = "better" if dist(v) < dist(was) else "worse" if dist(v) > dist(was) else ""
            else:
                verdict = "better" if (v > was) == (rule == "higher") else "worse"
        print(f"  {k:18s} {str(was) if was is not None else '-':>8s} -> {v!s:>8s}  {verdict}")
    print("Targets: qa 0/0, scenes_too_wordy 0, narration 130-165 wpm, longest static scene under 14 s, loud transitions 3 or fewer. "
          "Then score the craft by eye with PLAYBOOK.md section 7.")


# ---------------------------------------------------------------- start from the saved brief
def apply_brief(d: Path, brief_file: Path) -> list[str]:
    """Copy the brief builder's choices (inbox/brief.json) into a new project's project.json and brief.md."""
    b = json.loads(brief_file.read_text(encoding="utf-8")); pj = d / "project.json"
    spec = json.loads(pj.read_text(encoding="utf-8")); done = []
    if b.get("voice"):
        spec["voice"] = None if b["voice"] == "none" else {**(spec.get("voice") or {}), "name": b["voice"]}; done.append(f"voice {b['voice']}")
    if b.get("music"):
        spec["music"] = "none" if b["music"] == "none" else {**(spec.get("music") if isinstance(spec.get("music"), dict) else {}), "mood": b["music"]}; done.append(f"music {b['music']}")
    if b.get("captions"):
        spec["captions"] = b["captions"]; done.append(f"captions {b['captions']}")
    for k in ("theme", "format", "mode", "treatment"):
        if b.get(k):
            spec[k] = b[k]; done.append(f"{k} {b[k]}")
    pj.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    refs = b.get("references") or []
    rows = [("Vision (the user's own words: build this first)", b.get("vision")),
            ("References", "; ".join(refs) if isinstance(refs, list) else refs),
            ("Purpose and audience", b.get("purpose")), ("Length", b.get("length")), ("Must-say messages and call to action", b.get("must_say")),
            ("AI images", "yes" if b.get("ai_images") else "no" if "ai_images" in b else None),
            ("Treatment (structure)", b.get("treatment") or ("show options with the script" if "treatment" in b else None))]
    rows = [(k, v) for k, v in rows if v]
    if rows:
        bm = d / "brief.md"; text = bm.read_text(encoding="utf-8") if bm.exists() else ""
        note = "## From the brief builder (inbox/brief.json)\n\n" + "".join(f"- **{k}:** {v}\n" for k, v in rows) + "\n"
        bm.write_text(note + text, encoding="utf-8"); done.append("brief.md notes")
    return done


# ---------------------------------------------------------------- exports
def latest_render(d: Path) -> Path:
    rs = _renders(d)
    if not rs:
        raise SystemExit(f"no render yet in {d / 'renders'} (python studio.py render {d.name})")
    return rs[-1]


def export(src: Path, kind: str, width: int, start: float, end: float | None, fps: int) -> Path:
    import av
    import numpy as np
    from PIL import Image
    tag = f"_{start:g}-{end:g}s" if (start or end) else ""
    out = src.with_name(src.stem + tag + "." + kind)
    c = av.open(str(src)); v = c.streams.video[0]; dur = float(c.duration / 1e6); end = min(end or dur, dur)
    w = width - width % 2; h = int(round(w * v.height / v.width / 2) * 2)
    if kind == "gif":
        frames, nxt = [], start
        for f in c.decode(v):
            t = float(f.pts * v.time_base)
            if t < nxt - 1e-3:
                continue
            if t > end:
                break
            frames.append(f.to_image().resize((w, h), Image.LANCZOS)); nxt += 1 / fps
        c.close()
        if not frames:
            raise SystemExit("no frames in that range")
        sample = Image.new("RGB", (w, h * min(6, len(frames))))
        for i, k in enumerate(np.linspace(0, len(frames) - 1, min(6, len(frames))).astype(int)):
            sample.paste(frames[k], (0, i * h))
        pal = sample.quantize(255, method=Image.Quantize.MEDIANCUT)
        q = [fr.quantize(palette=pal, dither=Image.Dither.NONE) for fr in frames]
        q[0].save(out, save_all=True, append_images=q[1:], duration=int(1000 / fps), loop=0, optimize=True, disposal=1)
    else:
        o = av.open(str(out), "w")
        vs = o.add_stream("libvpx-vp9", rate=fps); vs.width, vs.height, vs.pix_fmt = w, h, "yuv420p"
        vs.options = {"crf": "33", "b": "0", "deadline": "good", "cpu-used": "4", "row-mt": "1"}
        a_in = c.streams.audio[0] if c.streams.audio and "libopus" in av.codecs_available else None
        if a_in is not None:
            as_ = o.add_stream("libopus", rate=48000); as_.layout = "stereo"; as_.bit_rate = 128000
            rs = av.AudioResampler(format="s16", layout="stereo", rate=48000)
        nxt, n = start, 0
        for f in c.decode(v):
            t = float(f.pts * v.time_base)
            if t < nxt - 1e-3:
                continue
            if t > end:
                break
            vf = av.VideoFrame.from_image(f.to_image().resize((w, h), Image.LANCZOS)); vf.pts = n; n += 1; nxt += 1 / fps
            for pk in vs.encode(vf):
                o.mux(pk)
        for pk in vs.encode():
            o.mux(pk)
        if a_in is not None:
            c.seek(int(start / a_in.time_base), stream=a_in)
            for f in c.decode(a_in):
                t = float(f.pts * a_in.time_base)
                if t < start:
                    continue
                if t > end:
                    break
                for g in rs.resample(f):
                    g.pts = None
                    for pk in as_.encode(g):
                        o.mux(pk)
            for pk in as_.encode():
                o.mux(pk)
        o.close(); c.close()
    print(f"{kind} -> {out}  ({out.stat().st_size / 1e6:.1f} MB, {w}x{h}, {fps} fps, {end - start:.1f}s)")
    return out


def vertical(d: Path, name: str | None = None) -> Path:
    """A 9:16 copy of a project as a new project: same script, voice and theme; pop captions for phones."""
    dst = d.parent / (name or f"{d.name}-vertical")
    if dst.exists():
        raise SystemExit(f"{dst} already exists")
    shutil.copytree(d, dst, ignore=shutil.ignore_patterns("renders", ".cache", ".state.json", "*.bak", "feedback.md"))
    (dst / "renders").mkdir(exist_ok=True)
    pj = dst / "project.json"; spec = json.loads(pj.read_text(encoding="utf-8"))
    spec["format"] = "9:16"; spec.setdefault("caption_style", "pop"); spec["title"] = spec.get("title", d.name) + " (vertical)"
    pj.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    shots = sum(1 for sc in spec.get("scenes", []) if sc.get("type") == "screen")
    print(f"created {dst} (9:16, pop captions). Next: python studio.py stills {dst.name}"
          + (f"\n  {shots} screen scene(s): in portrait, centre each camera on the action (cam) or the UI will be small." if shots else ""))
    return dst
