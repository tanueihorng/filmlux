"""Build the media that START_HERE.html shows, plus synthetic demo footage.

  python studio.py samples

Writes:
  assets/gallery/*.jpg                    stills of each style pack and theme
  assets/samples/voice_*.mp3              one line from each narrator voice (needs internet once)
  assets/samples/music_*.m4a              20 s of each music mood
  assets/gallery/manifest.js              lists all of the above for START_HERE.html
  examples/sample_footage/demo_app.mp4    a synthetic 'screen recording' (fake app, no real data) for trying the release_film pack
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

import av  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from vstudio import audio, voice  # noqa: E402
from vstudio.capture import Browser  # noqa: E402
from vstudio.config import SR, h264_encoder  # noqa: E402
from vstudio.render import Project, compose, Frames  # noqa: E402

GAL, SMP = ROOT / "assets" / "gallery", ROOT / "assets" / "samples"


def demo_footage():
    out = ROOT / "examples" / "sample_footage" / "demo_app.mp4"; out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        return out
    b = Browser(ROOT / "tools" / "demo_app.html", 1920, 1080)
    part = out.with_suffix(".part.mp4")
    codec, opts = h264_encoder()
    c = av.open(str(part), "w"); vs = c.add_stream(codec, rate=30); vs.width, vs.height, vs.pix_fmt = 1920, 1080, "yuv420p"
    vs.options = opts(18)
    try:
        for n in range(300):
            b.eval(f"renderAt({n / 30:.4f})"); vf = av.VideoFrame.from_image(b.shot()); vf.pts, vf.time_base = n, Fraction(1, 30)
            for p in vs.encode(vf):
                c.mux(p)
        for p in vs.encode():
            c.mux(p)
    finally:
        c.close(); b.close()
    part.replace(out)                                  # only a complete file gets the real name
    print("demo footage ->", out)
    return out


SHOWCASE = {
    "motion_promo": [
        {"type": "kinetic", "lines": ["Bold.", "Clear.", "<em>Memorable</em>."], "dur": 3},
        {"type": "bento", "title": "Everything, <em>at a glance</em>", "tiles": [
            {"label": "Insight", "title": "One view of every customer", "size": "2x2", "accent": True}, {"label": "Assist", "title": "Ask, don't search", "size": "2x1"},
            {"label": "Reach", "title": "Personal, at scale"}, {"label": "Act", "title": "Replies to actions"}]},
        {"type": "end", "title": "Launching <em>today</em>", "sub": "Your product, your promise", "cta": "Try it now"}],
    "explainer": [
        {"type": "process", "title": "How it works", "steps": [{"title": "Collect", "body": "Your data"}, {"title": "Understand", "body": "AI insight"},
                                                               {"title": "Act", "body": "Outreach"}, {"title": "Learn", "body": "Replies"}]},
        {"type": "chart", "kind": "column", "title": "Replies per week", "data": [["W1", 12], ["W2", 19], ["W3", 27], ["W4", 41]], "note": "Sample data"},
        {"type": "compare", "title": "What changes", "left": {"title": "Before", "items": ["Scattered files", "Manual emails"]},
         "right": {"title": "After", "items": ["One view", "Tracked replies"]}}],
    "release_film": [
        {"type": "title", "eyebrow": "Release 2", "title": "Campaigns, <em>in one click</em>", "sub": "What's new and how to use it"},
        {"type": "screen", "src": "examples/sample_footage/demo_app.mp4", "a": 0, "b": 3.0, "est": .5, "cam": [[0, .5, .5, 1.0]]},
        {"type": "screen", "src": "examples/sample_footage/demo_app.mp4", "a": 2.2, "b": 6.5, "est": 0, "cam": [[0, .62, .3, 1.0], [0.8, .78, .2, 1.3]],
         "callouts": [[0.3, 1.3, .86, .025, .985, .095]], "_still": 1.0}],
    "data_story": [
        {"type": "stat", "eyebrow": "Reply rate", "value": "41%", "label": "up from 19%", "sub": "Sample data"},
        {"type": "chart", "kind": "line", "title": "Week four was the <em>turning point</em>", "data": [["W1", 19], ["W2", 22], ["W3", 31], ["W4", 41]], "unit": "%", "note": "Sample data"},
        {"type": "timeline", "title": "What happens <em>next</em>", "items": [{"when": "Nov", "title": "Roll out"}, {"when": "Dec", "title": "Measure"}, {"when": "Jan", "title": "Scale"}]}],
    "cinematic_brand": [
        {"type": "quote", "text": "Every customer has a <em>story</em>.", "by": ""},
        {"type": "section", "number": "02", "eyebrow": "What we built", "title": "A place to <em>listen</em>"},
        {"type": "end", "title": "Built to <em>last</em>", "sub": "A milestone, together"}],
    "ai_illustrated": [
        {"type": "split", "src": "assets/gen/x.png", "gen": "an illustration of the idea", "eyebrow": "The idea", "title": "Pictures from your <em>words</em>", "body": "Your agent draws them; the studio animates them."},
        {"type": "process", "title": "From prompt to <em>picture</em>", "steps": ["Describe", "Generate", "Check", "Animate"]},
        {"type": "title", "eyebrow": "Optional", "title": "AI images, <em>your</em> call", "sub": "Placeholders until they exist"}],
}
SHOWCASE.update({
    "kinetic_type": [
        {"type": "kinetic", "lines": ["Stop searching.", "Start <em>knowing</em>."], "dur": 3},
        {"type": "section", "number": "01", "eyebrow": "The shift", "title": "One <em>idea</em> per screen"},
        {"type": "stat", "eyebrow": "Proof", "value": "3x", "label": "faster answers", "sub": "Sample data"}],
    "tech_architecture": [
        {"type": "title", "eyebrow": "Architecture", "title": "How the system <em>works</em>", "sub": "From raw signals to governed answers"},
        {"type": "process", "title": "How data <em>flows</em>", "steps": ["Capture", "Resolve", "Govern", "Serve"]},
        {"type": "bento", "eyebrow": "Building blocks", "title": "What's <em>inside</em>", "tiles": [{"size": "2x1", "title": "Ingestion", "body": "Streams and batch"},
            {"title": "Identity", "body": "One customer"}, {"title": "Policy", "body": "Who sees what"}, {"size": "2x1", "title": "Serving API", "body": "Answers in milliseconds"}]}],
    "whiteboard_explainer": [
        {"type": "title", "eyebrow": "How to", "title": "How do I <em>escalate</em> a case?", "sub": "Four steps, two minutes"},
        {"type": "process", "title": "The <em>steps</em>", "steps": ["Open", "Check", "Escalate", "Confirm"]},
        {"type": "compare", "title": "Do and <em>don't</em>", "left": {"title": "Don't", "items": ["Forward by email", "Skip the notes"]}, "right": {"title": "Do", "items": ["Use the form", "Add context"]}}],
    "handmade_story": [
        {"type": "title", "eyebrow": "Team spotlight", "title": "Meet the people behind <em>every reply</em>"},
        {"type": "quote", "text": "We read every message like it's from a <em>neighbour</em>.", "by": "Support lead", "role": "Sample quote"},
        {"type": "timeline", "title": "Their <em>journey</em>", "items": [{"when": "2023", "title": "Two people"}, {"when": "2024", "title": "A team"}, {"when": "2025", "title": "A community"}]}],
    "retro_hype": [
        {"type": "kinetic", "lines": ["Press <em>play</em>."], "dur": 2.5},
        {"type": "section", "number": "01", "eyebrow": "Level", "title": "The <em>launch</em>"},
        {"type": "stat", "eyebrow": "High score", "value": "10x", "label": "more replies", "sub": "Sample data"}],
})
PACK_THEME = {"data_story": "newsroom", "cinematic_brand": "cinema", "ai_illustrated": "warm", "kinetic_type": "brutal", "tech_architecture": "blueprint",
              "whiteboard_explainer": "whiteboard", "handmade_story": "collage", "retro_hype": "vhs"}
VERTICAL = [{"type": "kinetic", "lines": ["Stop.", "<em>Ask</em>."], "dur": 3, "say": "Stop searching. Just ask."},
            {"type": "stat", "eyebrow": "Every week", "value": "5 hrs", "label": "back for you", "say": "Five hours back, every week."},
            {"type": "end", "title": "Try it <em>today</em>", "cta": "Open the app", "say": "Try it today."}]


def gallery():
    GAL.mkdir(parents=True, exist_ok=True); items = []
    tmp = Path(tempfile.mkdtemp(prefix="vs_gal_"))
    try:
        for pack, scenes in SHOWCASE.items():
            d = tmp / pack; d.mkdir()
            (d / "project.json").write_text(json.dumps({"title": pack, "theme": PACK_THEME.get(pack, "navy"), "voice": None, "music": None, "captions": "none", "scenes": scenes}))
            p = Project(d).prepare(synth=False); fr = Frames(p); cache = {}
            try:
                for i, sc in enumerate(p.scenes):
                    T = sc["_start"] + (sc["_still"] if "_still" in sc else sc["dur"] * (.5 if sc["type"] == "screen" else .9))
                    f = GAL / f"{pack}_{i + 1}.jpg"; compose(fr, T, cache).resize((960, 540)).save(f, quality=86); items.append(f.name)
            finally:
                fr.close()
        d = tmp / "social_vertical"; d.mkdir()                     # three phone frames side by side
        (d / "project.json").write_text(json.dumps({"title": "v", "theme": "neon", "format": "9:16", "caption_style": "pop", "voice": None, "music": None, "captions": "custom",
                                                    "scenes": [dict(sc, caption=sc["say"]) for sc in VERTICAL]}))
        p = Project(d).prepare(synth=False); fr = Frames(p); cache = {}
        try:
            canvas = Image.new("RGB", (960, 540), (8, 8, 16))
            for i, sc in enumerate(p.scenes):
                im = compose(fr, sc["_start"] + sc["dur"] * .45, cache).resize((270, 480)); canvas.paste(im, (60 + i * 300, 30))
            f = GAL / "social_vertical_1.jpg"; canvas.save(f, quality=86); items.append(f.name)
        finally:
            fr.close()
        for th in sorted(x.stem for x in (ROOT / "themes").glob("*.json")):
            d = tmp / f"t_{th}"; d.mkdir()
            (d / "project.json").write_text(json.dumps({"theme": th, "voice": None, "music": None, "captions": "none", "scenes": [
                {"type": "title", "eyebrow": "Theme · " + th, "title": "Your story, <em>beautifully</em> told", "sub": json.loads((ROOT / "themes" / f"{th}.json").read_text(encoding="utf-8")).get("name", th)}]}))
            p = Project(d).prepare(synth=False); fr = Frames(p)
            try:
                f = GAL / f"theme_{th}.jpg"; compose(fr, p.scenes[0]["dur"] * .9, {}).resize((960, 540)).save(f, quality=86); items.append(f.name)
            finally:
                fr.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"gallery: {len(items)} stills")


def voices():
    SMP.mkdir(parents=True, exist_ok=True); cache = Path(tempfile.gettempdir()) / "video_studio" / "voice_samples"
    lines = {}
    for v in voice.VOICES:
        first = v.split("-")[2].replace("Neural", "")
        lines[v] = {"zh": "你好，我可以为你的视频配音，清晰又自然。", "ms": "Hai, saya boleh menjadi suara untuk video anda.",
                    "ta": "வணக்கம், உங்கள் வீடியோவுக்கு நான் குரல் கொடுக்கிறேன்."}.get(v[:2],
                    f"Hi, I'm {first}. I'll narrate your video, clearly and naturally.")
    for v, line in lines.items():
        out = SMP / f"voice_{v}.mp3"
        if out.exists():
            continue
        try:
            voice.synth([line], cache, v, voice.DEFAULT_RATE); shutil.copy(voice.clip_path(cache, line, v, voice.DEFAULT_RATE), out)
        except Exception as e:
            print(f"  voice sample skipped for {v}: {e}")
    print("voice samples ->", SMP)


def music():
    SMP.mkdir(parents=True, exist_ok=True)
    for mood in audio.MOODS:
        out = SMP / f"music_{mood}.m4a"
        if out.exists():
            continue
        x = audio.bed(20, mood, 0, 20, -20)
        c = av.open(str(out), "w"); s = c.add_stream("aac", rate=SR); s.layout = "stereo"; s.bit_rate = 160000
        x = np.pad(x, ((0, 0), (0, (-x.shape[1]) % 1024)))
        for k in range(0, x.shape[1], 1024):
            f = av.AudioFrame.from_ndarray(np.ascontiguousarray(x[:, k:k + 1024]), format="fltp", layout="stereo"); f.sample_rate = SR; f.pts = k
            for p in s.encode(f):
                c.mux(p)
        for p in s.encode():
            c.mux(p)
        c.close()
    print("music samples ->", SMP)


def manifest():
    m = {"packs": {p: sorted(f.name for f in GAL.glob(f"{p}_*.jpg")) for p in list(SHOWCASE) + ["social_vertical"]},
         "themes": sorted(f.name for f in GAL.glob("theme_*.jpg")),
         "voices": [{"name": v, "desc": d, "file": f"voice_{v}.mp3"} for v, d in voice.VOICES.items() if (SMP / f"voice_{v}.mp3").exists()],
         "moods": [{"name": k, "desc": v["desc"], "file": f"music_{k}.m4a"} for k, v in audio.MOODS.items()]}
    (GAL / "manifest.js").write_text("window.MANIFEST = " + json.dumps(m, indent=1, ensure_ascii=False) + ";\n", encoding="utf-8")
    print("manifest ->", GAL / "manifest.js")


def main():
    demo_footage(); gallery(); voices(); music(); manifest()


if __name__ == "__main__":
    main()
