"""Filmlux renderer: project.json -> fitted timeline -> frames (stage HTML / screen footage / custom HTML)
-> captions -> music + voice mix -> H.264/AAC MP4, plus .srt, contact sheet and a QA report.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import wave
from fractions import Fraction
from pathlib import Path

import av
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import audio, voice
from .capture import Browser
from .config import ASSETS, FORMATS, FPS, ROOT, SR, STAGE, THEMES, WORK, h264_encoder

KIT = STAGE.parent.parent / "kit" / "filmlux-kit.js"     # helpers injected into every custom html scene

DEFAULT_DUR = {"title": 4.5, "kinetic": 5.0, "bullets": 6.0, "stat": 4.5, "quote": 5.5, "chart": 6.5, "process": 6.5,
               "image": 5.0, "split": 6.0, "bento": 6.5, "compare": 6.5, "end": 5.0, "screen": 0, "html": 5.0,
               "section": 3.5, "logo": 3.5, "timeline": 7.0,
               "polaroids": 6.5, "note": 5.5, "countdown": 4.5, "wordwall": 5.0, "annotate": 7.5, "chat": 7.5}
IMAGE_TYPES = ("image", "split", "title", "quote", "annotate")
# Every way a scene type can be composed ("layout"); the first is the default. Mirrors LAYOUTS in engine/stage/stage.html.
LAYOUTS = {
    "title": ["center", "left", "bottom", "giant", "photo"], "kinetic": ["center", "stack"], "bullets": ["split", "stack", "big"],
    "stat": ["center", "left", "giant"], "quote": ["center", "side", "note", "huge"], "chart": ["full", "side"],
    "image": ["frame", "full", "polaroid"], "split": ["side", "overlap", "full", "stacked", "polaroid"],
    "bento": ["grid", "row", "pinboard", "list"], "compare": ["cards", "halves"], "section": ["side", "center"],
    "timeline": ["line", "steps", "vertical"], "end": ["center", "left", "band"],
    "polaroids": ["pile", "row"], "note": ["sticky", "card"], "countdown": ["center"], "wordwall": ["rows", "stack"],
    "annotate": ["side", "over"], "chat": ["center", "side"],
}
# The composition each (type, layout) puts on screen. qa uses it to stop a film from repeating one frame.
COMPOSITION = {
    "centred": {"title:center", "kinetic:center", "stat:center", "quote:center", "end:center", "logo:center", "countdown:center", "section:center", "chat:center"},
    "left-type": {"title:left", "title:bottom", "title:giant", "kinetic:stack", "stat:left", "stat:giant", "quote:huge", "end:left", "section:side", "bullets:big", "wordwall:stack", "bento:list"},
    "side-by-side": {"split:side", "split:polaroid", "bullets:split", "chart:side", "quote:side", "timeline:vertical", "annotate:side", "chat:side"},
    "grid": {"bento:grid", "bento:row", "bullets:stack", "compare:cards"},
    "full-bleed": {"title:photo", "image:full", "split:full", "split:overlap", "compare:halves", "end:band", "wordwall:rows"},
    "diagram": {"process:path", "timeline:line", "timeline:steps", "chart:full", "split:stacked", "annotate:over", "image:frame"},
    "objects": {"polaroids:pile", "polaroids:row", "note:sticky", "note:card", "quote:note", "bento:pinboard", "image:polaroid"},
}


def layout_of(sc):
    opts = LAYOUTS.get(sc["type"])
    if not opts:
        return {"process": "path", "logo": "center"}.get(sc["type"], "default")
    L = sc.get("layout")
    if not L and sc["type"] == "title" and sc.get("align") == "left":
        L = "left"
    if not L and sc["type"] == "image" and sc.get("full"):
        L = "full"
    return L if L in opts else opts[0]


def composition_of(sc):
    key = f"{sc['type']}:{layout_of(sc)}"
    return next((k for k, v in COMPOSITION.items() if key in v), "other")
LEAD, TAIL = .35, .7          # voice starts LEAD s into its scene; TAIL s of breathing room after it
XFADE = .4                    # default dissolve between scenes (s)
STILL_EXT = (".png", ".jpg", ".jpeg", ".webp")   # a screen scene can tour a still screenshot instead of a video
DRAFT_FPS = 10                                    # render --draft: a third of the frames, for checking pacing
MOTIONS = ("smooth", "snappy", "spring", "bouncy", "heavy", "mask", "typewriter", "stopmotion", "focus", "flip", "slam", "gentle", "glitch")


# ---------------------------------------------------------------- project
class Project:
    def __init__(self, folder: Path):
        self.dir = Path(folder).resolve()
        f = self.dir / "project.json"
        if not f.exists():
            raise SystemExit(f"No project.json in {self.dir}")
        self.spec = json.loads(f.read_text(encoding="utf-8"))
        s = self.spec
        self.title = s.get("title", self.dir.name)
        self.W, self.H = FORMATS.get(s.get("format", "16:9"), FORMATS["16:9"])
        th = s.get("theme", "navy")
        tp = THEMES / f"{th}.json" if not str(th).endswith(".json") else self.dir / th
        self.theme = json.loads(tp.read_text(encoding="utf-8"))
        if s.get("look"):                                        # project-level look overrides the theme's
            self.theme["look"] = {**self.theme.get("look", {}), **s["look"]}
        if s.get("caption_style"):
            self.theme["caption"] = {**self.theme.get("caption", {}), "style": s["caption_style"]}
        for k in ("motion", "transition", "transition_timing"):                       # project-level motion / transition override the theme's
            if s.get(k):
                self.theme[k] = s[k]
        v = s.get("voice") or {}
        self.voice = v.get("name", voice.DEFAULT_VOICE) if s.get("voice") is not None else None
        self.rate = v.get("rate", voice.DEFAULT_RATE)
        m = s.get("music", {"mood": "calm"})
        self.mood = None if m in (None, "none") else m.get("mood", "calm")
        self.music_file = None if m in (None, "none") else m.get("file")
        self.music_db = (m or {}).get("level_db", -27.0) if m not in (None, "none") else -27.0
        self.whoosh = (m or {}).get("whoosh", True) if m not in (None, "none") else False
        self.captions = s.get("captions", "narration")          # narration | custom | none
        self.mode = "creative" if s.get("mode") == "creative" else "guided"   # guided (default) | creative
        self.cache = self.dir / ".cache" / "voice"
        self.scenes = [dict(sc) for sc in s.get("scenes", [])]
        for sc in self.scenes:
            if sc.get("src") and not re.match(r"^(https?:|data:)", sc["src"]):
                sc["_path"] = str(self.resolve(sc["src"]))
            if sc["type"] == "screen" and Path(str(sc.get("src", ""))).suffix.lower() in STILL_EXT:
                sc["_still"] = True; sc["a"] = 0.0; sc["b"] = float(sc.get("dur", 6.0)); sc["speed"] = 1.0
            for ly in sc.get("layers") or []:
                if ly.get("src") and not re.match(r"^(https?:|data:)", ly["src"]):
                    ly["_path"] = str(self.resolve(ly["src"]))
            if sc.get("photos"):                                 # polaroids: each print has its own picture
                sc["photos"] = [dict(o) for o in sc["photos"]]
                for o in sc["photos"]:
                    if o.get("src") and not re.match(r"^(https?:|data:)", o["src"]):
                        o["_path"] = str(self.resolve(o["src"]))
                    if o.get("gen") and not Path(o.get("_path", "")).exists():
                        o["_pending"] = gen_prompt(o["gen"])
            # an AI image that has not been generated yet: previews show a placeholder, QA blocks the final render
            if sc["type"] in IMAGE_TYPES and sc.get("gen") and not Path(sc.get("_path", "")).exists() and not sc.get("layers"):
                sc["_pending"] = gen_prompt(sc["gen"])
            for ly in sc.get("layers") or []:
                if ly.get("gen") and not Path(ly.get("_path", "")).exists():
                    ly["_pending"] = gen_prompt(ly["gen"])

    def resolve(self, p) -> Path:
        q = Path(p)
        for base in (self.dir, ROOT):
            if (base / q).exists():
                return (base / q).resolve()
        return (self.dir / q).resolve()

    def lines(self):
        return [sc["say"] for sc in self.scenes if sc.get("say")]

    def prepare(self, synth=True):
        """Synthesise voice (cached), then fit every scene's duration to its line."""
        if self.voice and synth:
            n = voice.synth(self.lines(), self.cache, self.voice, self.rate)
            if n:
                print(f"voice: synthesised {n} line(s) with {self.voice} {self.rate}")
        t = 0.0
        for sc in self.scenes:
            vd = voice.duration(self.cache, sc["say"], self.voice, self.rate) if (self.voice and sc.get("say")) else 0
            sc["_voice"] = vd
            if sc["type"] == "screen":
                base = (sc["b"] - sc["a"]) / sc.get("speed", 1.0) + sc.get("hold", 0) + sc.get("est", 0)
                need = LEAD + vd + TAIL if vd else 0
                sc["_hold"] = sc.get("hold", 0) + max(0, need - base)
                sc["dur"] = (sc["b"] - sc["a"]) / sc.get("speed", 1.0) + sc["_hold"] + sc.get("est", 0)
            else:
                sc["dur"] = max(float(sc.get("dur", DEFAULT_DUR.get(sc["type"], 5.0))), LEAD + vd + TAIL if vd else 0)
            sc["_start"] = t; t += sc["dur"]
        self.total = t
        return self

    def stage_spec(self):
        scenes = []
        for sc in self.scenes:
            d = {k: v for k, v in sc.items() if not k.startswith("_")}
            if sc.get("_path"):
                d["src"] = Path(sc["_path"]).as_uri()
            if sc.get("_pending"):
                d["pending"] = sc["_pending"]
            if sc.get("layers"):
                d["layers"] = [{**{k: v for k, v in ly.items() if not k.startswith("_")},
                                **({"src": Path(ly["_path"]).as_uri()} if ly.get("_path") else {}),
                                **({"pending": ly["_pending"]} if ly.get("_pending") else {})} for ly in sc["layers"]]
            if sc.get("photos"):
                d["photos"] = [{**{k: v for k, v in o.items() if not k.startswith("_")},
                                **({"src": Path(o["_path"]).as_uri()} if o.get("_path") else {}),
                                **({"pending": o["_pending"]} if o.get("_pending") else {})} for o in sc["photos"]]
            scenes.append(d)
        theme = dict(self.theme)
        return {"width": self.W, "height": self.H, "theme": theme, "scenes": scenes, "root_uri": ROOT.as_uri(), "title": self.title,
                "brand_mark": self.spec.get("brand_mark", True), "captions": bool(self.captions_list())}

    def scene_at(self, T):
        for i, sc in enumerate(self.scenes):
            if T < sc["_start"] + sc["dur"] or i == len(self.scenes) - 1:
                return i, sc, T - sc["_start"]

    def captions_list(self):
        out = []
        if self.captions == "none":
            return out
        for sc in self.scenes:
            text = sc.get("caption") if self.captions == "custom" or sc.get("caption") else sc.get("say")
            if text and sc.get("caption") is not False:
                for k, part in enumerate(split_caption(text)):
                    span = sc["dur"] - .3; n = len(split_caption(text))
                    s = sc["_start"] + .25 + span * k / n
                    out.append((s, sc["_start"] + .25 + span * (k + 1) / n - .05, part))
        return out

    def pop_list(self):
        """Word-by-word captions (caption style "pop"): 1-3 word chunks timed across each voice line."""
        out = []
        if self.captions == "none":
            return out
        for sc in self.scenes:
            text = sc.get("caption") if self.captions == "custom" or sc.get("caption") else sc.get("say")
            if not text or sc.get("caption") is False:
                continue
            ws = re.sub(r"<[^>]+>", "", text).split()
            t0 = sc["_start"] + LEAD; span = sc["_voice"] or max(1.0, sc["dur"] - .9)
            wt = [len(w) + 2 + (4 if re.search(r"[.,;:!?]$", w) else 0) for w in ws]; tot = sum(wt); acc = 0; timed = []
            for w, k in zip(ws, wt):
                a = t0 + span * acc / tot; acc += k; timed.append((w, a, t0 + span * acc / tot))
            chunk = []
            for item in timed:
                chunk.append(item)
                if len(chunk) == 3 or re.search(r"[.,;:!?]$", item[0]) or sum(len(c[0]) for c in chunk) > 16:
                    out.append((chunk[0][1], chunk[-1][2], chunk)); chunk = []
            if chunk:
                out.append((chunk[0][1], chunk[-1][2], chunk))
        return out

    def next_out(self):
        rd = self.dir / "renders"; rd.mkdir(exist_ok=True)
        slug = re.sub(r"[^A-Za-z0-9]+", "_", self.dir.name).strip("_")
        v = 1
        while (rd / f"{slug}_v{v}.mp4").exists():
            v += 1
        return rd / f"{slug}_v{v}.mp4"


def gen_prompt(g):
    return g if isinstance(g, str) else g.get("prompt", "")


def split_caption(text, maxc=72):
    """Long narration -> 1-2 caption cards that each fit one line."""
    text = re.sub(r"<[^>]+>", "", text)
    if len(text) <= maxc:
        return [text]
    parts = re.split(r"(?<=[.!?;:,])\s+", text)
    out, cur = [], ""
    for p in parts:
        if len(cur) + len(p) + 1 <= maxc or not cur:
            cur = (cur + " " + p).strip()
        else:
            out.append(cur); cur = p
    out.append(cur)
    res = []
    for o in out:                                   # hard-wrap anything still too long at a word boundary
        while len(o) > maxc + 10:
            cut = o.rfind(" ", 0, maxc); res.append(o[:cut]); o = o[cut + 1:]
        res.append(o)
    return res


# ---------------------------------------------------------------- footage scenes
class Reader:
    def __init__(self, path):
        self.path, self.c, self.lt, self.img = path, None, -1.0, None

    def _open(self, t):
        if self.c:
            self.c.close()
        self.c = av.open(str(self.path)); self.v = self.c.streams.video[0]
        self.c.seek(int(max(0, t - 1.5) / self.v.time_base), stream=self.v)
        self.it = self.c.decode(self.v); self.last = None; self.lt = -1.0; self.nxt = None

    def get(self, t):
        if self.c is None or t < self.lt - 1e-6 or t > self.lt + 3:
            self._open(t)
        while True:
            if self.nxt is None:
                try:
                    self.nxt = next(self.it)
                except StopIteration:
                    break
            nt = float(self.nxt.pts * self.v.time_base)
            if nt <= t + 1e-4 or self.last is None:
                self.last, self.lt, self.nxt = self.nxt, nt, None
                if nt > t + 1e-4:
                    break
            else:
                break
        return self.last.to_image().convert("RGB")


def _rgb(h, default=(255, 255, 255)):
    h = str(h or "").strip().lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) if len(h) == 6 else default


def ease(p):
    p = min(1, max(0, p)); return p * p * (3 - 2 * p)


def cam_at(sc, rt):
    keys = sc.get("cam") or [[0, .5, .5, 1.0]]
    est = sc.get("est", 0)
    def at(t):
        if t <= keys[0][0]:
            return keys[0][1:]
        for (t0, *a), (t1, *b) in zip(keys, keys[1:]):
            if t <= t1:
                p = ease((t - t0) / max(1e-6, t1 - t0)); return [x + (y - x) * p for x, y in zip(a, b)]
        return keys[-1][1:]
    if rt < est:
        return [.5, .5, 1.0]
    c = at(rt - est); p = ease((rt - est) / 1.1)
    return [.5 + (c[0] - .5) * p, .5 + (c[1] - .5) * p, 1 + (c[2] - 1) * p]


class Composer:
    """Screen-recording scenes: camera crop/zoom, callouts, framed window on the theme backdrop."""

    def __init__(self, prj: Project):
        self.p = prj; self.readers = {}; self.backdrops = {}; self.stills = {}
        self.accent = tuple(int(prj.theme["colors"]["accent"].lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))

    def source(self, sc, rt):
        if sc.get("_still"):
            if sc["_path"] not in self.stills:
                self.stills[sc["_path"]] = Image.open(sc["_path"]).convert("RGB")
            return self.stills[sc["_path"]]
        r = self.readers.setdefault(sc["_path"], Reader(sc["_path"]))
        est = sc.get("est", 0); play = max(0, rt - est)
        st = sc["a"] + min(play, (sc["b"] - sc["a"]) / sc.get("speed", 1.0)) * sc.get("speed", 1.0)
        return r.get(st)

    def frame(self, i, sc, rt, backdrop):
        est = sc.get("est", 0)
        src = self.source(sc, rt); sw, sh = src.size
        cx, cy, z = cam_at(sc, rt); z = max(1.0, z)
        cw, ch = sw / z, sh / z
        x0 = min(max(0, cx * sw - cw / 2), sw - cw); y0 = min(max(0, cy * sh - ch / 2), sh - ch)
        crop = src.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch)))
        W, H = self.p.W, self.p.H
        framed = sc.get("frame", True)
        grow = ease((z - 1.0) / .25) if framed else 1.0
        s = (.88 + .12 * grow) if framed else 1.0
        bw, bh = W * s, (H * (s if H <= W else .62 + .38 * grow * 0))
        k = min(bw / cw, bh / ch) if H <= W else (W * s) / cw
        ww, wh = int(cw * k), int(ch * k)
        win = crop.resize((ww, wh), Image.LANCZOS)
        out = backdrop.copy()
        ox, oy = (W - ww) // 2, int((H - wh) / 2 - (H * .02 * (1 - grow) if framed and H <= W else 0))
        P = lambda ax, ay: ((ax * sw - x0) * k, (ay * sh - y0) * k)     # source fraction -> window pixel
        t = rt - est
        if sc.get("typing"):
            win = self.typing(win, sc, t, P, src, k)
        labels = []
        # callouts (source-normalised boxes), dim outside the box inside the window; an optional 7th item is a label
        for co in sc.get("callouts", []):
            t0, t1, a0, b0, a1, b1 = co[:6]
            a = ease((rt - est - t0) / .35) * (1 - ease((rt - est - t1) / .3))
            if a <= 0:
                continue
            X0 = (a0 * sw - x0) * k; Y0 = (b0 * sh - y0) * k; X1 = (a1 * sw - x0) * k; Y1 = (b1 * sh - y0) * k
            dim = Image.new("L", (ww, wh), int(110 * a)); ImageDraw.Draw(dim).rounded_rectangle([X0 - 8, Y0 - 8, X1 + 8, Y1 + 8], 14, fill=0)
            win = Image.composite(Image.new("RGB", (ww, wh), (8, 12, 24)), win, dim)
            ov = Image.new("RGBA", (ww, wh), (0, 0, 0, 0)); g = 1 + .04 * (1 - a)
            mx, my = (X0 + X1) / 2, (Y0 + Y1) / 2; hw, hh = (X1 - X0) / 2 * g + 8, (Y1 - Y0) / 2 * g + 8
            ImageDraw.Draw(ov).rounded_rectangle([mx - hw, my - hh, mx + hw, my + hh], 14, outline=self.accent + (int(255 * a),), width=4)
            win = Image.alpha_composite(win.convert("RGBA"), ov).convert("RGB")
            if len(co) > 6 and co[6]:
                labels.append((str(co[6]), X0, Y0, X1, Y1, a))
        if labels or sc.get("toasts") or sc.get("cursor"):
            win = self.overlays(win, sc, t, P, labels)
        if framed:
            rad = int(22 * min(W, H) / 1080 * (1 - grow) + 1)
            m = Image.new("L", (ww, wh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, ww - 1, wh - 1], rad, fill=255)
            sh_ = Image.new("RGBA", (ww + 160, wh + 160), (0, 0, 0, 0))
            ImageDraw.Draw(sh_).rounded_rectangle([80, 110, 80 + ww, 110 + wh], rad, fill=(0, 0, 0, int(150 * (1 - grow))))
            out = out.convert("RGBA"); out.alpha_composite(sh_.filter(ImageFilter.GaussianBlur(36)), (ox - 80, oy - 80)); out = out.convert("RGB")
            out.paste(win, (ox, oy), m)
        else:
            out.paste(win, (ox, oy))
        # entrance: gentle rise + fade for the first 0.6 s of the scene
        e = ease(rt / .6)
        if e < 1:
            out = Image.blend(backdrop, out, e)
        return out


    # ---- walkthrough overlays: typed text, callout labels, pop-up toasts, an animated cursor with click ripples
    def typing(self, win, sc, t, P, src, k):
        d = ImageDraw.Draw(win); sw, sh = src.size
        for ty in sc.get("typing", []):
            t0 = float(ty.get("t", 0))
            if t < t0 - 1e-6:
                continue
            text = str(ty.get("text", "")); n = min(len(text), int((t - t0) * float(ty.get("cps", 14))))
            bx = ty["box"]; (X0, Y0), (X1, Y1) = P(bx[0], bx[1]), P(bx[2], bx[3])
            bg = src.getpixel((min(sw - 1, int(bx[0] * sw) + 4), min(sh - 1, int((bx[1] + bx[3]) / 2 * sh))))
            fg = (24, 24, 28) if .299 * bg[0] + .587 * bg[1] + .114 * bg[2] > 140 else (242, 242, 245)
            d.rectangle([X0 + 2, Y0 + 2, X1 - 2, Y1 - 2], fill=bg)
            px = max(9, int(float(ty.get("size", min((bx[3] - bx[1]) * sh * .48, sh * .03))) * k))
            f = font(px, "Regular"); pad = px * .7; lines, cur = [], ""
            for w in text[:n].split(" "):
                cand = (cur + " " + w) if cur else w
                if f.getlength(cand) <= (X1 - X0) - 2 * pad or not cur:
                    cur = cand
                else:
                    lines.append(cur); cur = w
            lines.append(cur)
            lh = px * 1.4; y = (Y0 + Y1) / 2 - lh / 2 if (Y1 - Y0) < 2.4 * lh else Y0 + pad * .8
            for ln in lines:
                d.text((X0 + pad, y), ln, font=f, fill=fg); y += lh
            if n < len(text) or int(t * 2) % 2 == 0:                        # caret: solid while typing, then blinks
                cx = X0 + pad + f.getlength(lines[-1]) + 2
                d.rectangle([cx, y - lh + px * .15, cx + max(2, px // 9), y - lh + px * 1.15], fill=self.accent)
        return win

    def overlays(self, win, sc, t, P, labels):
        ww, wh = win.size; ov = Image.new("RGBA", (ww, wh), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        fpx = max(13, int(min(ww, wh * 1.6) * .017)); f = font(fpx, "Medium")
        for text, X0, Y0, X1, Y1, a in labels:                         # light chip under (or over) the callout box
            tw = f.getlength(text); cw, ch = tw + fpx * 2.4, fpx * 2.1
            cx, cy = max(6, min(ww - cw - 6, X0)), Y1 + 18
            if cy + ch > wh - 6:
                cy = Y0 - 18 - ch
            d.rounded_rectangle([cx, cy, cx + cw, cy + ch], ch / 2, fill=(251, 248, 242, int(240 * a)))
            d.ellipse([cx + fpx * .7, cy + ch / 2 - fpx * .25, cx + fpx * 1.2, cy + ch / 2 + fpx * .25], fill=self.accent + (int(255 * a),))
            d.text((cx + fpx * 1.6, cy + ch / 2), text, font=f, fill=(20, 22, 32, int(255 * a)), anchor="lm")
        for t0, t1, text in sc.get("toasts", []):                      # dark pop-up pill, bottom centre
            a = ease((t - t0) / .25) * (1 - ease((t - t1) / .25))
            if a <= 0:
                continue
            tw = f.getlength(text); cw, ch = tw + fpx * 3.6, fpx * 2.4
            cx, cy = (ww - cw) / 2, wh - ch - wh * .05 + (1 - a) * 12
            d.rounded_rectangle([cx, cy, cx + cw, cy + ch], ch / 2, fill=(30, 30, 34, int(238 * a)), outline=(70, 70, 78, int(255 * a)))
            r = fpx * .55; d.ellipse([cx + fpx * .9, cy + ch / 2 - r, cx + fpx * .9 + 2 * r, cy + ch / 2 + r], fill=self.accent + (int(255 * a),))
            d.text((cx + fpx * 2.5, cy + ch / 2), text, font=f, fill=(244, 244, 245, int(255 * a)), anchor="lm")
        keys = sc.get("cursor") or []
        if keys and t >= keys[0][0]:
            x, y = keys[-1][1:3]
            for (ta, xa, ya), (tb, xb, yb) in zip(keys, keys[1:]):
                if t <= tb:
                    e = ease((t - ta) / max(1e-6, tb - ta)); x, y = xa + (xb - xa) * e, ya + (yb - ya) * e; break
            X, Y = P(x, y); u = max(18, wh * .04) / 20
            for c in sc.get("clicks", []):                             # ripple
                q = (t - c) / .55
                if 0 <= q < 1:
                    r = (6 + 34 * q) * u * 1.4
                    d.ellipse([X - r, Y - r, X + r, Y + r], outline=self.accent + (int(255 * (1 - q)),), width=max(2, int(3 * u)))
            if any(0 <= t - c < .12 for c in sc.get("clicks", [])):
                u *= .86
            arrow = [(0, 0), (0, 16), (4, 12.5), (6.8, 18.6), (9.6, 17.4), (7, 11.6), (12, 11.6)]
            a_ = min(1, (t - keys[0][0]) / .25)
            d.polygon([(X + 2 * u + ax * u, Y + 3 * u + ay * u) for ax, ay in arrow], fill=(0, 0, 0, int(90 * a_)))
            d.polygon([(X + ax * u, Y + ay * u) for ax, ay in arrow], fill=(255, 255, 255, int(255 * a_)), outline=(16, 18, 28, int(255 * a_)), width=max(1, int(1.6 * u)))
        return Image.alpha_composite(win.convert("RGBA"), ov).convert("RGB")


# ---------------------------------------------------------------- captions
_fonts = {}


def font(px, weight="Medium"):
    k = (px, weight)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(str(ASSETS / "fonts" / f"InterDisplay-{weight}.ttf"), px)
    return _fonts[k]


def _font_file(path, px):
    k = (path, px)
    if k not in _fonts:
        try:
            _fonts[k] = ImageFont.truetype(str(ASSETS / "fonts" / path), px)
        except OSError:                                # a Pillow build without WOFF2 support: use the bundled TTF
            _fonts[k] = ImageFont.truetype(str(ASSETS / "fonts" / "InterDisplay-SemiBold.ttf"), px)
    return _fonts[k]


def draw_pop(img, T, chunks, theme, W, H):
    """Social-style captions: big bold words, the spoken word lit in the accent colour."""
    act = [c for c in chunks if c[0] - .05 <= T < c[1] + .12]
    if not act:
        return img
    s, e, words = act[-1]
    u = min(W, H) / 1080; cs = theme.get("caption", {})
    hi = tuple(cs.get("chip", [255, 210, 0])); ink = tuple(cs.get("ink", [255, 255, 255]))
    upper = cs.get("upper", True); fname = cs.get("font", "inter-800.woff2")
    k = min(1, max(0, (T - s + .05) / .12)); size = int((84 if H > W else 74) * u * (.9 + .1 * k))
    f = _font_file(fname, size); sp = f.getlength(" ")
    toks = [(w.upper() if upper else w) for w, _, _ in words]
    widths = [f.getlength(t) for t in toks]; total = sum(widths) + sp * (len(toks) - 1)
    while total > W * .86 and size > 30:
        size -= 2; f = _font_file(fname, size); sp = f.getlength(" "); widths = [f.getlength(t) for t in toks]; total = sum(widths) + sp * (len(toks) - 1)
    lb = H * .075 if theme.get("look", {}).get("letterbox") else 0
    cy = H * (.78 if H > W else .83) - lb * .5
    fr = img.convert("RGBA"); y0 = max(0, int(cy - size * 1.4)); y1 = min(H, int(cy + size * 1.6))   # shadow only in the caption strip
    sh = Image.new("RGBA", (W, y1 - y0), (0, 0, 0, 0)); d2 = ImageDraw.Draw(sh)
    x = (W - total) / 2
    for t, w in zip(toks, widths):
        d2.text((x, cy + 6 * u - y0), t, font=f, fill=(0, 0, 0, 150), anchor="lm"); x += w + sp
    fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10 * u)), (0, y0))
    d = ImageDraw.Draw(fr); x = (W - total) / 2
    lit = max([k for k, (_, a, _) in enumerate(words) if a - .03 <= T] or [0])       # exactly one word lit: the one being spoken
    for k, ((w, a, b), t, wd) in enumerate(zip(words, toks, widths)):
        on = k == lit
        d.text((x, cy), t, font=f, fill=hi + (255,) if on else ink + (255,), anchor="lm", stroke_width=max(2, int(5 * u)), stroke_fill=(0, 0, 0, 230)); x += wd + sp
    return fr.convert("RGB")


def draw_bar(img, T, caps, theme, W, H):
    """Lower-third bar: accent stripe + solid panel, left-aligned (newsroom / corporate)."""
    act = [c for c in caps if c[0] <= T < c[1] + .2]
    if not act:
        return img
    s, e, text = act[-1]
    a = min(1, max(0, (T - s) / .25)) * (1 - min(1, max(0, (T - e) / .2)))
    if a <= 0:
        return img
    u = min(W, H) / 1080; cs = theme.get("caption", {})
    fill = tuple(cs.get("fill", [12, 20, 40, 220]))[:3]; ink = tuple(cs.get("ink", [255, 255, 255])); chip = tuple(cs.get("chip", [237, 25, 61]))
    size = int(34 * u); f = font(size)
    while f.getlength(text) > W * .74 and size > 22 * u:
        size -= 1; f = font(size)
    pad = int(30 * u); h = int(size * 2.1); w = int(f.getlength(text) + pad * 2 + 10 * u)
    lb = H * .075 if theme.get("look", {}).get("letterbox") else 0
    x = int(W * .08 - (1 - a) * 30 * u); y = int(H - h - lb - (60 * u if H <= W else H * .16))
    fr = img.convert("RGBA"); ov = Image.new("RGBA", (w, h), fill + (int(235 * a),)); d = ImageDraw.Draw(ov)
    d.rectangle([0, 0, int(10 * u), h], fill=chip + (int(255 * a),))
    d.text((int(10 * u) + pad, h / 2), text, font=f, fill=ink + (int(255 * a),), anchor="lm")
    fr.alpha_composite(ov, (max(0, x), y))
    return fr.convert("RGB")


def draw_captions(img, T, caps, theme, W, H):
    style = theme.get("caption", {}).get("style", "glass")
    if style == "bar":
        return draw_bar(img, T, caps, theme, W, H)
    act = [c for c in caps if c[0] <= T < c[1] + .25]
    if not act:
        return img
    s, e, text = act[-1]
    a = min(1, max(0, (T - s) / .3)) * (1 - min(1, max(0, (T - e) / .25)))
    if a <= 0:
        return img
    u = min(W, H) / 1080
    cs = theme.get("caption", {}); fill = tuple(cs.get("fill", [12, 20, 40, 150])); ink = tuple(cs.get("ink", [255, 255, 255]))
    size = int(36 * u); f = font(size)
    while f.getlength(text) > W * .78 and size > 24 * u:
        size -= 1; f = font(size)
    pad = int(34 * u); h = int(size * 2.4); w = int(f.getlength(text) + pad * 2)
    lb = H * .075 if theme.get("look", {}).get("letterbox") else 0
    x = (W - w) // 2; y = int(H - h - lb - (64 * u if H <= W else H * .16)) + int((1 - min(1, (T - s) / .4)) * 18 * u)
    fr = img.convert("RGBA")
    shadow = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([40, 52, 40 + w, 52 + h], int(26 * u), fill=(0, 0, 0, int(100 * a)))
    fr.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)), (max(0, x - 40), max(0, y - 40)))
    box = (x, y, x + w, y + h)
    bg = fr.crop(box).filter(ImageFilter.GaussianBlur(18))
    bg = Image.alpha_composite(bg, Image.new("RGBA", bg.size, fill))
    d = ImageDraw.Draw(bg)
    d.rounded_rectangle([0, 0, w - 1, h - 1], int(26 * u), outline=(255, 255, 255, 60), width=1)
    d.text((w / 2, h / 2 + 1), text, font=f, fill=ink, anchor="mm")
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], int(26 * u), fill=int(255 * a))
    bg.putalpha(m); fr.alpha_composite(bg, (x, y))
    return fr.convert("RGB")


# ---------------------------------------------------------------- the frame source
class Frames:
    def __init__(self, prj: Project):
        self.p = prj
        self.stage = Browser(STAGE, prj.W, prj.H)
        self.stage.eval(f"setSpec({json.dumps(prj.stage_spec())})", await_promise=True)
        self.comp = Composer(prj); self.custom = {}; self.backdrop = {}
        self.caps = prj.captions_list()
        self.pop = prj.pop_list() if prj.theme.get("caption", {}).get("style") == "pop" else None

    def raw(self, T):
        i, sc, rt = self.p.scene_at(T)
        if sc["type"] == "screen":
            if i not in self.backdrop:
                self.stage.eval(f"renderFrame({i}, 1.0)", await_promise=True); self.backdrop[i] = self.stage.shot()
            return self.comp.frame(i, sc, rt, self.backdrop[i])
        if sc["type"] == "html":
            b = self.html_page(i)
            self.html_seek(b, rt)
            return b.shot()
        self.stage.eval(f"renderFrame({i}, {rt:.5f})", await_promise=True)
        return self.stage.shot()

    def html_page(self, i):
        """The browser for html scene i: loads the page, injects the Filmlux kit, hands it FILMLUX (props + the film's look)."""
        b = self.custom.get(i)
        if b is None:
            sc = self.p.scenes[i]
            b = self.custom[i] = Browser(Path(sc["_path"]), self.p.W, self.p.H,
                                         "window.ready === true || (document.readyState === 'complete' && !window.__waitReady)")
            b.eval(KIT.read_text(encoding="utf-8") + "\n;true")
            fl = {"props": sc.get("props") or {}, "theme": {"colors": self.p.theme.get("colors", {}), "type": self.p.theme.get("type", {}), "mode": self.p.theme.get("mode")},
                  "width": self.p.W, "height": self.p.H, "dur": sc["dur"], "fonts": (ASSETS / "fonts").as_uri(),
                  "motion": sc.get("motion") or self.p.theme.get("motion") or "smooth", "captions": bool(self.caps) and sc.get("caption") is not False}
            b.eval(f"window.FILMLUX = {json.dumps(fl)}; Promise.resolve(window.onFilmlux ? window.onFilmlux(window.FILMLUX) : true)", await_promise=True)
        return b

    @staticmethod
    def html_seek(b, rt):
        b.eval(f"(window.renderAt ? Promise.resolve(window.renderAt({rt:.5f})) : (Object.values(window.__timelines || {{}}).forEach(tl => tl.seek({rt:.5f}, false)), true))",
               await_promise=True)

    def close(self):
        self.stage.close()
        for b in self.custom.values():
            b.close()


# Scene transitions. Names follow Remotion's presentations (fade, slide, wipe, flip, clockwipe, iris, cube, none) plus
# a few film ones. Direction: "slide:from-left", "wipe:from-top-right" ... Timing: transition_timing "ease" | "linear" | "spring".
TRANSITIONS = {"fade": XFADE, "dissolve": XFADE, "none": 0, "cut": 0, "slide": .6, "push": .6, "wipe": .6, "flip": .7, "clockwipe": .7,
               "iris": .6, "cube": .7, "zoom": .5, "dip": .6, "flash": .45, "blur": .5, "glitch": .3}
DIRECTIONS = ("from-left", "from-right", "from-top", "from-bottom", "from-top-left", "from-top-right", "from-bottom-left", "from-bottom-right")


def transition_kind(sc, prj=None):
    """-> (kind, direction)"""
    raw = str(sc.get("transition") or (prj.theme.get("transition") if prj else None) or "fade")
    k, _, d = raw.partition(":")
    k = k if k in TRANSITIONS else "fade"
    d = d or sc.get("transition_direction") or (prj.theme.get("transition_direction") if prj else None) or ""
    return k, (d if d in DIRECTIONS else "")


def xfade_len(sc, prj=None):
    k, _ = transition_kind(sc, prj)
    return 0 if TRANSITIONS[k] == 0 else float(sc.get("transition_s", TRANSITIONS[k]))


def spring_value(t, damping=10.0, stiffness=100.0, mass=1.0):
    """Remotion's spring(): damped harmonic oscillator from 0 to 1."""
    if t <= 0:
        return 0.0
    w0 = math.sqrt(stiffness / mass); z = damping / (2 * math.sqrt(stiffness * mass))
    if z < 1:
        wd = w0 * math.sqrt(1 - z * z); x = math.exp(-z * w0 * t) * (-math.cos(wd * t) - z * w0 / wd * math.sin(wd * t))
    elif z == 1:
        x = math.exp(-w0 * t) * (-1 - w0 * t)
    else:
        r = math.sqrt(z * z - 1); r1, r2 = -w0 * (z - r), -w0 * (z + r); B = r1 / (r2 - r1); x = (-1 - B) * math.exp(r1 * t) + B * math.exp(r2 * t)
    return 1 + x


def timing(p, kind="ease"):
    p = min(1, max(0, p))
    if kind == "linear":
        return p
    if kind == "spring":                                        # springTiming {damping 20, stiffness 200}, overshoot clamped
        return 1.0 if p >= 1 else min(1.0, spring_value(p * .55, 20, 200))
    return ease(p)


_GRID = {}


def _grid(W, H):
    if (W, H) not in _GRID:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); _GRID[(W, H)] = (xx, yy)
    return _GRID[(W, H)]


def _zoom(img, s):
    W, H = img.size; w, h = int(W / s), int(H / s); x0, y0 = (W - w) // 2, (H - h) // 2
    return img.crop((x0, y0, x0 + w, y0 + h)).resize((W, H), Image.BILINEAR)


def _shade(img, k):
    return Image.blend(Image.new("RGB", img.size, (0, 0, 0)), img, max(0.0, min(1.0, k)))


def transition(a, b, p, kind="fade", accent=(255, 255, 255), direction="", tm="ease"):
    """Blend the outgoing frame a into the incoming frame b at progress p (0..1)."""
    e = timing(p, tm)
    if kind in ("fade", "dissolve"):
        return Image.blend(a, b, e)
    W, H = b.size
    if kind in ("dip", "flash"):
        c = Image.new("RGB", (W, H), (0, 0, 0) if kind == "dip" else accent)
        return Image.blend(a, c, ease(p * 2)) if p < .5 else Image.blend(c, b, ease(p * 2 - 1))
    if kind == "zoom":
        return Image.blend(_zoom(a, 1 + .12 * e), _zoom(b, 1.18 - .18 * e), e)
    if kind == "blur":
        r = 18 * math.sin(math.pi * p)
        return Image.blend(a.filter(ImageFilter.GaussianBlur(r)), b.filter(ImageFilter.GaussianBlur(r)), e)
    if kind == "flip":                                          # the old scene turns edge-on, the new one turns in
        out = Image.new("RGB", (W, H), (0, 0, 0))
        src, k = (a, 1 - e * 2) if e < .5 else (b, e * 2 - 1)
        w = max(1, int(W * k)); h = int(H * (.92 + .08 * k)); im = _shade(src.resize((w, h), Image.BILINEAR), .55 + .45 * k)
        out.paste(im, ((W - w) // 2, (H - h) // 2)); return out
    if kind == "cube":                                          # both scenes on the faces of a turning cube
        out = Image.new("RGB", (W, H), (0, 0, 0)); fw = max(1, int(W * (1 - e))); nw = max(1, W - fw)
        rev = direction in ("from-left",)
        A2 = _shade(a.resize((fw, H), Image.BILINEAR), 1 - .45 * e); B2 = _shade(b.resize((nw, H), Image.BILINEAR), .55 + .45 * e)
        if rev:
            out.paste(B2, (0, 0)); out.paste(A2, (nw, 0))
        else:
            out.paste(A2, (0, 0)); out.paste(B2, (fw, 0))
        return out
    A = np.asarray(a, np.float32); B = np.asarray(b, np.float32)
    if kind in ("slide", "push"):                               # new scene slides in and pushes the old one out
        d = direction or "from-right"; out = np.empty_like(A)
        if d in ("from-right", "from-left"):
            off = int(e * W)
            if d == "from-right":
                out[:, :W - off] = A[:, off:]; out[:, W - off:] = B[:, :off]
            else:
                out[:, off:] = A[:, :W - off]; out[:, :off] = B[:, W - off:]
        else:
            off = int(e * H)
            if d.startswith("from-bottom"):
                out[:H - off] = A[off:]; out[H - off:] = B[:off]
            else:
                out[off:] = A[:H - off]; out[:off] = B[H - off:]
    elif kind == "glitch":
        rng = np.random.default_rng(int(p * 97) + 7); out = (A if p < .5 else B).copy(); k = math.sin(math.pi * p)
        for _ in range(14):
            y0 = int(rng.integers(0, H - 8)); h = int(rng.integers(6, max(8, H // 14))); out[y0:y0 + h] = np.roll(out[y0:y0 + h], int(rng.normal(0, W * .06 * k)), axis=1)
        d = int(W * .008 * k) + 1; out[..., 0] = np.roll(out[..., 0], d, axis=1); out[..., 2] = np.roll(out[..., 2], -d, axis=1)
    else:
        xx, yy = _grid(W, H)
        if kind == "iris":
            R = math.hypot(W, H) / 2 * 1.04; m = np.clip((e * R - np.hypot(xx - W / 2, yy - H / 2)) / (W * .02), 0, 1)
        elif kind == "clockwipe":                               # a clock hand sweeps round from 12 o'clock
            th = (np.arctan2(xx - W / 2, -(yy - H / 2)) + 2 * math.pi) % (2 * math.pi); m = np.clip((e * 2 * math.pi * 1.02 - th) / .04, 0, 1)
        else:                                                   # wipe: soft edge from the given side (default from-left)
            d = direction or "from-left"; vx = (1 if "left" in d else -1 if "right" in d else 0); vy = (1 if "top" in d else -1 if "bottom" in d else 0)
            n = math.hypot(vx, vy) or 1; vx, vy = vx / n, vy / n
            proj = ((xx if vx >= 0 else W - xx) * abs(vx) + (yy if vy >= 0 else H - yy) * abs(vy)); span = W * abs(vx) + H * abs(vy); soft = span * .08
            m = np.clip((e * (span + soft) - proj) / soft, 0, 1)
        out = A * (1 - m[..., None]) + B * m[..., None]
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))


# ---------------------------------------------------------------- audio
def soundtrack(prj: Project):
    n = int(prj.total * SR)
    vo = np.zeros(n, np.float32)
    end = 0.0
    for sc in prj.scenes:
        if prj.voice and sc.get("say"):
            x = voice.load(prj.cache, sc["say"], prj.voice, prj.rate)
            t = max(sc["_start"] + LEAD, end + .2); k = int(t * SR); e = min(n, k + len(x))
            if k < n:
                vo[k:e] += x[:e - k]
            end = t + len(x) / SR
    if prj.music_file:
        mus = load_music(prj.resolve(prj.music_file), prj.total, prj.music_db)
    else:
        mus = audio.bed(prj.total, prj.mood, 0, prj.total, prj.music_db) if prj.mood else np.zeros((2, n), np.float32)
    if prj.whoosh and prj.mood:
        for i, sc in enumerate(prj.scenes[1:], 1):
            if sc["type"] in ("title", "end", "kinetic", "stat", "bento") and xfade_len(sc, prj) > 0:
                w = audio.whoosh(30 + i); k = int(max(0, sc["_start"] - .6) * SR); e = min(n, k + len(w))
                mus[:, k:e] += (w[:e - k] * .025).astype(np.float32)
    mix = audio.master(mus[:, :n], vo, duck=.6 if prj.mood or prj.music_file else 0)
    return mix


def load_music(path, total, level_db):
    c = av.open(str(path)); rs = av.AudioResampler(format="fltp", layout="stereo", rate=SR); parts = []
    for f in c.decode(audio=0):
        parts += [g.to_ndarray() for g in rs.resample(f)]
    c.close()
    x = np.concatenate(parts, axis=1).astype(np.float32); n = int(total * SR)
    while x.shape[1] < n:
        x = np.concatenate([x, x], axis=1)
    x = x[:, :n]; t = np.arange(n) / SR
    x *= np.clip(t / 1.5, 0, 1) * np.clip((total - t) / 2.5, 0, 1)
    rms = np.sqrt((x ** 2).mean()); x *= 10 ** (level_db / 20) / max(rms, 1e-6)
    return x


def write_wav(path, mix):
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(mix.T, -1, 1) * 32767).astype("<i2").tobytes())


# ---------------------------------------------------------------- QA
def qa(prj: Project, fr: Frames | None = None):
    issues = []
    for i, sc in enumerate(prj.scenes):
        tag = f"scene {i + 1} ({sc['type']})"
        if sc.get("_pending"):
            issues.append(("ERROR", tag, f"AI image not generated yet: {sc.get('src')} (run: python studio.py imagegen <name>, then generate it; see IMAGEGEN.md)"))
        elif (sc["type"] in ("screen", "image", "split", "html", "annotate") or sc.get("_path")) and not sc.get("layers") and not Path(sc.get("_path", "")).exists():
            issues.append(("ERROR", tag, f"file not found: {sc.get('src')}"))
        for o in sc.get("photos") or []:
            if o.get("_pending"):
                issues.append(("ERROR", tag, f"AI photo not generated yet: {o.get('src')}"))
            elif not Path(o.get("_path", "")).exists():
                issues.append(("ERROR", tag, f"photo file not found: {o.get('src')}"))
        if sc.get("layout") and sc["type"] in LAYOUTS and sc["layout"] not in LAYOUTS[sc["type"]]:
            issues.append(("WARN", tag, f"unknown layout '{sc['layout']}' for {sc['type']} (using '{LAYOUTS[sc['type']][0]}') -> fix: choose one of: {', '.join(LAYOUTS[sc['type']])}"))
        if sc["type"] == "title" and layout_of(sc) == "photo" and not sc.get("src") and not sc.get("gen"):
            issues.append(("WARN", tag, "title layout 'photo' needs a 'src' picture (it falls back to 'center') -> fix: add \"src\", or choose another layout"))
        for ly in sc.get("layers") or []:
            if ly.get("_pending"):
                issues.append(("ERROR", tag, f"AI image layer not generated yet: {ly.get('src')}"))
            elif not Path(ly.get("_path", "")).exists():
                issues.append(("ERROR", tag, f"layer file not found: {ly.get('src')}"))
        say = sc.get("say", "")
        if say and len(say.split()) > 30:
            nw = len(say.split()); k = math.ceil(nw / 20)
            issues.append(("WARN", tag, f"narration line has {nw} words; keep it under ~25 -> fix: split it into {k} scenes of about {nw // k} words each"))
        if say and re.search(r"\b[\w.]+@[\w.]+\b|\b\d{8,}\b", say):
            issues.append(("WARN", tag, "narration looks like it contains an email or long number (it is sent to the speech service)"))
        if sc["type"] == "screen":
            for k in sc.get("cam", []):
                lim = 2.0 if sc.get("_still") else 1.5          # sharp hi-res screenshots can take a closer look
                if k[3] > lim:
                    issues.append(("WARN", tag, f"camera zoom {k[3]} > {lim} loses context -> fix: set that key's zoom to {1.8 if sc.get('_still') else 1.4}"))
            if sc.get("speed", 1) > 1.5 and not sc.get("fast_ok"):
                issues.append(("WARN", tag, f"speed {sc.get('speed')}x: fine for waiting/typing, too fast for UI steps -> fix: set \"speed\": 1.2, or \"fast_ok\": true if it only shows waiting or typing"))
        if sc.get("transition") and str(sc["transition"]).partition(":")[0] not in TRANSITIONS:
            issues.append(("WARN", tag, f"unknown transition '{sc['transition']}' (using dissolve); choose from: {', '.join(TRANSITIONS)}"))
        if sc.get("motion") and sc["motion"] not in MOTIONS:
            issues.append(("WARN", tag, f"unknown motion '{sc['motion']}' (using the theme's); choose from: {', '.join(MOTIONS)}"))
        if sc["type"] == "logo" and not (sc.get("src") or sc.get("name") or (self_brand := prj.theme.get("brand") or {}).get("logo") or self_brand.get("name")):
            issues.append(("WARN", tag, "logo scene has no logo: set scene 'src' / 'name', or theme brand.logo (it falls back to the project title)"))
        if sc["dur"] > 14 and sc["type"] not in ("screen", "html"):
            issues.append(("WARN", tag, f"{sc['dur']:.1f}s on one static scene -> fix: split it into {math.ceil(sc['dur'] / 7)} scenes with one idea each"))
        if sc["type"] not in ("screen", "html") and sc["type"] not in DEFAULT_DUR:
            issues.append(("ERROR", tag, f"unknown scene type '{sc['type']}' (see SPEC.md)"))
    issues += craft_checks(prj)
    issues += placeholder_checks(prj)
    if prj.mode == "guided":                       # guided: a custom scene is allowed when it builds something the user asked for
        bespoke = [i for i, sc in enumerate(prj.scenes) if sc["type"] == "html" and not (library_scene(sc) or {}).get("guided_ok")]
        for n, i in enumerate(bespoke):
            sc = prj.scenes[i]
            if not str(sc.get("why", "")).strip():
                issues.append(("WARN", f"scene {i + 1} (html)", "a custom html scene in guided mode must say which request it fulfils -> fix: add \"why\": \"<the user's words it builds>\" "
                                                              "(or use a built-in layout / a guided_ok library scene: python studio.py scenes)"))
            elif n >= GUIDED_CUSTOM:
                issues.append(("WARN", f"scene {i + 1} (html)", f"more than {GUIDED_CUSTOM} custom html scenes in guided mode -> fix: use built-in layouts for the rest, or set \"mode\": \"creative\""))
    for s, e, text in prj.captions_list():
        if len(text) > 90:
            issues.append(("WARN", "caption", f"long caption ({len(text)} chars): {text[:50]}... -> fix: shorten that scene's say line, or set \"caption\" to a version under 72 characters"))
    if fr is not None:
        for i, sc in enumerate(prj.scenes):
            if sc["type"] == "html" and Path(sc.get("_path", "")).exists():
                issues += html_checks(fr, i, sc)
            if sc["type"] in ("screen", "html"):
                continue
            for msg in fr.stage.eval(f"qa({i})") or []:
                issues.append(("ERROR", f"scene {i + 1} ({sc['type']})", msg))
    if prj.mode == "guided":                       # guided: every craft warning must be fixed before rendering
        issues = [("ERROR" if l == "WARN" else l, w, m + (" [guided mode]" if l == "WARN" else "")) for l, w, m in issues]
    return issues


GUIDED_CUSTOM = 2          # custom html scenes a guided film may have (each with a "why")


def html_checks(fr, i, sc):
    """The same bar as built-in scenes: frames that depend only on t, nothing blank, no clipped or covered text."""
    tag, out, d = f"scene {i + 1} (html)", [], sc["dur"]
    try:
        b = fr.html_page(i)
    except Exception as e:                                       # the page itself fails to load
        return [("ERROR", tag, f"the page did not load: {str(e)[:120]}")]
    if not b.eval("!!(window.renderAt || (window.__timelines && Object.keys(window.__timelines).length))"):
        return [("ERROR", tag, "the page has no window.renderAt(t) and no paused GSAP timelines in window.__timelines (SPEC.md, html)")]
    def grab(t):
        fr.html_seek(b, t); return np.asarray(b.shot().convert("L").resize((240, 135)), dtype=np.float32)
    t1 = min(1.0, d * .3)
    a = grab(t1); grab(d * .75); c = grab(t1)
    if np.abs(a - c).mean() > 1.5:
        out.append(("ERROR", tag, "the same time gives different frames (wall-clock animation: Date.now, requestAnimationFrame or CSS animation) -> fix: draw everything from t in renderAt"))
    mid = grab(d * .6)
    if mid.std() < 3:
        out.append(("WARN", tag, f"the frame at {d * .6:.1f}s looks blank (one flat colour) -> fix: check the page draws at that time"))
    fr.html_seek(b, max(0, d - .05))
    for msg in b.eval("window.Kit ? Kit.qa() : []") or []:
        out.append(("ERROR", tag, msg + " (mark full-frame art with data-bleed)"))
    return out


_TEXT_SKIP = {"say", "caption", "src", "gen", "type", "transition", "transition_s", "transition_timing", "transition_direction",
              "motion", "cam", "note", "layers", "size", "accent", "dur", "speed", "hold", "move", "fit", "loop", "data", "unit",
              "layout", "beat", "why", "side", "ratio", "align", "focus", "tilt", "from", "to", "props"}


def library_scene(sc):
    """The manifest of a reusable html scene from scenes/<name>/ (None for a project's own html scene)."""
    p = Path(sc.get("_path", ""))
    lib = (ROOT / "scenes").resolve()
    try:
        p.resolve().relative_to(lib)
    except ValueError:
        return None
    m = p.parent / "scene.json"
    try:
        return json.loads(m.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
LOUD_TRANSITIONS = {"flash", "glitch", "iris", "cube", "clockwipe"}


def _onscreen_words(v, key=""):
    if key in _TEXT_SKIP or key.startswith("_"):
        return 0
    if isinstance(v, str):
        return len(re.sub(r"<[^>]+>", " ", v).split())
    if isinstance(v, dict):
        return sum(_onscreen_words(x, k) for k, x in v.items())
    if isinstance(v, list):
        return sum(_onscreen_words(x) for x in v)
    return 0


def _contrast(a, b):
    def lum(h):
        h = str(h).lstrip("#")
        if len(h) != 6:
            return None
        c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        c = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in c]
        return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]
    la, lb = lum(a), lum(b)
    return None if la is None or lb is None else (max(la, lb) + .05) / (min(la, lb) + .05)


def craft_checks(prj: Project):
    """Craft warnings: they never block a render. Fix them, or keep the choice on purpose and say why."""
    out, sc_ = [], prj.scenes
    for i, sc in enumerate(sc_):
        tag = f"scene {i + 1} ({sc['type']})"
        if sc["type"] in ("screen", "html"):
            continue
        n = _onscreen_words(sc)
        if n > max(16, 4 * sc.get("dur", 5)):
            d_ = sc.get("dur", 5)
            out.append(("WARN", tag, f"{n} words on screen for {d_:.1f}s; viewers read about 3 words a second -> fix: cut to {max(4, int(3 * d_ - 3))} words, or set \"dur\": {math.ceil(n / 3 + 1)}"))
        if i >= 2 and sc_[i - 1]["type"] == sc_[i - 2]["type"] == sc["type"]:
            alt = next(x for x in ("bullets", "stat", "image", "quote", "split") if x != sc["type"])
            out.append(("WARN", tag, f"third '{sc['type']}' scene in a row; vary the scene type unless the repetition is the point -> fix: make this one a '{alt}' scene"))
    # composition: the same frame again and again reads as a template, whatever the theme
    framed = [(i, composition_of(sc)) for i, sc in enumerate(sc_) if sc["type"] not in ("screen", "html")]
    for k in range(2, len(framed)):
        (i0, a), (i1, b), (i2, c_) = framed[k - 2], framed[k - 1], framed[k]
        same_type = sc_[i0]["type"] == sc_[i1]["type"] == sc_[i2]["type"]          # already reported above
        if a == b == c_ and i2 - i0 == 2 and not same_type:
            sc = sc_[i2]; opts = [l for l in LAYOUTS.get(sc["type"], []) if composition_of({**sc, "layout": l}) != c_]
            fix = f"set \"layout\" to one of: {', '.join(opts)}" if opts else "use a scene type with a different composition (python studio.py scenes)"
            out.append(("WARN", f"scene {i2 + 1} ({sc['type']})", f"third '{c_}' composition in a row (scenes {i0 + 1}-{i2 + 1} share one frame) -> fix: {fix}"))
    if len(framed) >= 6:
        fams = {c for _, c in framed}
        centred = sum(1 for _, c in framed if c == "centred")
        if len(fams) < 3:
            out.append(("WARN", "structure", f"only {len(fams)} kinds of composition across {len(framed)} scenes ({', '.join(sorted(fams))}); it will feel like one template "
                                              "-> fix: give 2-3 scenes another layout (python studio.py scenes lists them)"))
        if centred > len(framed) / 2:
            out.append(("WARN", "structure", f"{centred} of {len(framed)} scenes are centred text -> fix: move some to a 'left', 'bottom', 'giant', 'side' or 'note' layout"))
    loud = [i + 1 for i, sc in enumerate(sc_) if i > 0 and
            str(sc.get("transition") or prj.spec.get("transition") or "").partition(":")[0] in LOUD_TRANSITIONS]
    if len(loud) > 3:
        out.append(("WARN", "transitions", f"{len(loud)} loud transitions (scenes {', '.join(map(str, loud))}); they land harder on 2-3 key moments -> fix: keep {', '.join(map(str, loud[:2]))} and set the others to \"fade\""))
    c = prj.theme.get("colors", {})
    ink = [_contrast(c.get("ink"), c.get(k)) for k in ("bg0", "bg1")]
    if all(x is not None and x < 4.5 for x in ink):
        out.append(("WARN", "theme", f"text colour on the background has low contrast ({min(ink):.1f}:1, aim for 4.5:1 or more)"))
    acc = [_contrast(c.get("accent"), c.get(k)) for k in ("bg0", "bg1")]
    if all(x is not None and x < 2.2 for x in acc):
        out.append(("WARN", "theme", f"accent colour barely stands out from the background ({min(acc):.1f}:1)"))
    return out


PLACEHOLDER = re.compile(r"\b(replace|placeholder|lorem|benefit in|feature (one|two|three|four)|line (one|two|three)|call to action|product name|"
                         r"where to find it|say the|close with|your (headline|title) here|video title)\b", re.I)
_STARTER_TEXT = None


def _starter_strings():
    """Every instruction-like string in the packs' starter projects (template text that must be replaced)."""
    global _STARTER_TEXT
    if _STARTER_TEXT is None:
        found = set()
        def walk(v):
            if isinstance(v, str):
                if PLACEHOLDER.search(re.sub(r"<[^>]+>", "", v)):
                    found.add(v.strip())
            elif isinstance(v, dict):
                for x in v.values():
                    walk(x)
            elif isinstance(v, list):
                for x in v:
                    walk(x)
        for f in (ROOT / "packs").glob("*/starter/project.json"):
            try:
                walk(json.loads(f.read_text(encoding="utf-8")).get("scenes", []))
            except (OSError, ValueError):
                pass
        _STARTER_TEXT = found
    return _STARTER_TEXT


def placeholder_checks(prj: Project):
    """Template text from a pack starter that was never replaced (a common slip for any agent)."""
    out, starter = [], _starter_strings()
    for i, sc in enumerate(prj.scenes):
        left = []
        def walk(v, key=""):
            if key.startswith("_") or key in ("type", "src", "gen"):
                return
            if isinstance(v, str) and v.strip() in starter:
                left.append(v.strip())
            elif isinstance(v, dict):
                for kk, x in v.items():
                    walk(x, kk)
            elif isinstance(v, list):
                for x in v:
                    walk(x)
        walk(sc)
        for v in left[:3]:
            out.append(("WARN", f"scene {i + 1} ({sc['type']})", f"starter template text is still here: \"{v[:60]}\" -> fix: replace it with your own words (or delete the field)"))
    return out


# ---------------------------------------------------------------- commands
def plan(prj: Project):
    print(f"{prj.title}: {prj.W}x{prj.H}, {len(prj.scenes)} scenes, total {prj.total:.1f}s "
          f"({int(prj.total // 60)}:{prj.total % 60:04.1f}), voice={prj.voice or 'none'}, music={prj.music_file or prj.mood or 'none'}")
    for i, sc in enumerate(prj.scenes):
        vt = f"voice {sc['_voice']:.1f}s" if sc.get("_voice") else ""
        print(f"  {i + 1:2d}  {sc['_start']:6.2f}  {sc['dur']:5.2f}s  {sc['type']:8s} {vt:12s} {(sc.get('say') or sc.get('title') or '')[:70]}")


def compose(fr: Frames, T, prev_cache):
    """Frame at time T with dissolves and captions."""
    prj = fr.p; i, sc, rt = prj.scene_at(T)
    img = fr.raw(T)
    xf = xfade_len(sc, prj)
    if i > 0 and rt < xf:
        key = i - 1
        if key not in prev_cache:
            p = prj.scenes[i - 1]; prev_cache[key] = fr.raw(p["_start"] + p["dur"] - 1 / FPS)
        kind, direction = transition_kind(sc, prj)
        img = transition(prev_cache[key], img, rt / xf, kind, _rgb(prj.theme.get("colors", {}).get("accent2")), direction,
                         sc.get("transition_timing") or prj.theme.get("transition_timing") or "ease")
    if fr.pop is not None:
        return draw_pop(img, T, fr.pop, prj.theme, prj.W, prj.H)
    return draw_captions(img, T, fr.caps, prj.theme, prj.W, prj.H)


def stills(prj: Project, times=None, outdir=None):
    outdir = Path(outdir or WORK / "stills" / prj.dir.name); outdir.mkdir(parents=True, exist_ok=True)
    for f in outdir.glob("*.jpg"):
        f.unlink()
    fr = Frames(prj); cache = {}
    try:
        if not times:
            times = [sc["_start"] + sc["dur"] * .88 for sc in prj.scenes]
        paths = []
        for T in times:
            p = outdir / f"t{T:07.2f}.jpg"; compose(fr, min(T, prj.total - .01), cache).save(p, quality=90); paths.append(p)
        sheet(paths, outdir / "_stills_sheet.jpg")
    finally:
        fr.close()
    report, problems = stills_report(prj, times, paths, outdir / "stills_report.txt")
    print("stills ->", outdir)
    print(f"  sheet:  {outdir / '_stills_sheet.jpg'}  (open it and look)")
    print(f"  report: {report}  ({'no image problems found' if not problems else str(problems) + ' image problem(s): read it'})")
    return outdir


def stills_report(prj: Project, times, paths, out):
    """A text description of every still plus pixel checks (blank, near-duplicate, very low contrast), so an agent
    that cannot open images still gets a usable check. It does not replace looking at the sheet."""
    lines, prev, problems = [f"Stills report: {prj.title} ({prj.W}x{prj.H}, {prj.total:.1f}s)", ""], None, 0
    caps = prj.captions_list()
    for T, p in zip(times, paths):
        i, sc, rt = prj.scene_at(min(T, prj.total - .01))
        g = np.asarray(Image.open(p).convert("L").resize((320, int(320 * prj.H / prj.W))), np.float32)
        notes = []
        if g.std() < 4:
            notes.append("PROBLEM: looks blank (almost one flat colour)")
        elif np.percentile(g, 98) - np.percentile(g, 2) < 40:
            notes.append("PROBLEM: very low contrast, text may be hard to read")
        if prev is not None and prev[1] != i and np.abs(g - prev[0]).mean() < 1.5:     # two different scenes that look the same
            notes.append("PROBLEM: looks the same as the previous scene's still")
        prev = (g, i); problems += len(notes)
        words = []
        def walk(v, key=""):
            if key in _TEXT_SKIP or key.startswith("_"):
                return
            if isinstance(v, str):
                words.append(re.sub(r"<[^>]+>", "", v))
            elif isinstance(v, dict):
                for kk, x in v.items():
                    walk(x, kk)
            elif isinstance(v, list):
                for x in v:
                    walk(x)
        walk(sc)
        cap = next((c for s, e, c in caps if s <= T <= e), "")
        shown = " | ".join(w for w in words if w.strip())[:300] or f"(no text: {sc.get('src', 'visual')})"
        lines += [f"{p.name}  scene {i + 1}/{len(prj.scenes)} ({sc['type']}), {rt:.1f}s into a {sc['dur']:.1f}s scene",
                  f"  on screen: {shown}",
                  f"  caption:   {cap[:120] or '(none)'}",
                  f"  narration: {(sc.get('say') or '(none)')[:160]}"] + [f"  {n}" for n in notes] + [""]
    lines.append("No image problems found." if not problems else f"{problems} image problem(s) found: fix them, then run stills again.")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out, problems


def sheet(paths, out, cols=4):
    if not paths:
        return
    ims = [Image.open(p) for p in paths]; w = 480; h = int(w * ims[0].height / ims[0].width)
    S = Image.new("RGB", (w * cols, h * math.ceil(len(ims) / cols)), "white")
    for k, im in enumerate(ims):
        S.paste(im.resize((w, h)), ((k % cols) * w, (k // cols) * h))
    S.save(out, quality=88)


def srt(prj: Project, out: Path):
    def ts(t):
        ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    rows = prj.captions_list() if prj.captions != "none" else [(sc["_start"] + LEAD, sc["_start"] + LEAD + sc["_voice"], sc["say"])
                                                                for sc in prj.scenes if sc.get("say")]
    with open(out, "w", encoding="utf-8") as fh:
        for k, (s, e, text) in enumerate(rows, 1):
            fh.write(f"{k}\n{ts(s)} --> {ts(max(e, s + .8))}\n{text}\n\n")
    return out


def _chunk(job):
    """Worker: render the given frame numbers of a project into the frame cache (each worker has its own headless browser)."""
    folder, ns, keys, outdir, fps = job
    prj = Project(Path(folder)).prepare(synth=False); fr = Frames(prj); cache = {}
    try:
        for n, key in zip(ns, keys):
            compose(fr, n / fps, cache).save(Path(outdir) / f"{key}.jpg", quality=95, subsampling=0)
    finally:
        fr.close()
    return len(ns)


def _engine_sig():
    h = hashlib.sha1()
    for f in (STAGE, KIT, Path(__file__)):
        h.update(f.read_bytes())
    return h.hexdigest()[:12]


def frame_keys(prj: Project, fps, N):
    """One key per frame: everything that frame depends on (its scene, the time in it, the previous scene during a
    transition, the captions on screen, the theme and the engine code). Unchanged frames keep their key, so a new
    version only redraws the scenes that changed."""
    base = json.dumps({"theme": prj.theme, "W": prj.W, "H": prj.H, "brand": prj.spec.get("brand_mark", True), "title": prj.title,
                       "engine": _engine_sig()}, sort_keys=True, default=str)
    def spec(sc):
        d = {k: v for k, v in sc.items() if not k.startswith("_") or k in ("_path", "_hold", "_still", "_pending")}
        d["dur"] = round(sc["dur"], 4)
        if sc.get("_path") and Path(sc["_path"]).exists():
            d["_mtime"] = Path(sc["_path"]).stat().st_mtime
        return json.dumps(d, sort_keys=True, default=str)
    specs = [spec(sc) for sc in prj.scenes]
    caps = prj.captions_list()
    pop = prj.pop_list() if prj.theme.get("caption", {}).get("style") == "pop" else None
    keys = []
    for n in range(N):
        T = n / fps; i, sc, rt = prj.scene_at(T)
        parts = [base, str(i), specs[i], f"{rt:.4f}"]
        if i > 0 and rt < xfade_len(sc, prj):
            parts.append(specs[i - 1])
        if pop is not None:
            parts.append(json.dumps([[round(a - T, 3), round(b - T, 3), [[w, round(x - T, 3), round(y - T, 3)] for w, x, y in ch]]
                                     for a, b, ch in pop if a - 1 <= T <= b + 1]))
        else:
            parts.append(json.dumps([[round(s - T, 3), round(e - T, 3), c] for s, e, c in caps if s - 1 <= T <= e + 1]))
        keys.append(hashlib.sha1("|".join(parts).encode()).hexdigest()[:24])
    return keys


def render(prj: Project, force=False, crf=18, workers=None, draft=False):
    import os
    from multiprocessing import Pool
    fr = Frames(prj)
    try:
        issues = qa(prj, fr)
    finally:
        fr.close()
    for lvl, where, msg in issues:
        print(f"  {lvl:5s} {where}: {msg}")
    if any(l == "ERROR" for l, _, _ in issues) and not force and not draft:
        raise SystemExit("QA errors above. Fix them (or pass --force) before rendering.")
    fps = DRAFT_FPS if draft else FPS
    N = round(prj.total * fps)
    keys = frame_keys(prj, fps, N)
    tmp = WORK / "framecache" / prj.dir.name / str(fps); tmp.mkdir(parents=True, exist_ok=True)
    first = {}
    for n, k in enumerate(keys):
        if k not in first and not (tmp / f"{k}.jpg").exists():
            first[k] = n
    todo = sorted(first.values())
    missing = set(first)
    workers = workers or int(os.environ.get("VS_WORKERS", "2"))   # 2 is the sweet spot: browser screenshots share one compositor, more just stall
    print(f"render{' (draft, ' + str(fps) + ' fps)' if draft else ''}: {N} frames; {sum(1 for k in keys if k not in missing)} reused from "
          f"earlier renders, {len(todo)} to draw with {workers} parallel browser(s)", flush=True)
    if todo:
        size = max(30, math.ceil(len(todo) / (workers * 2)))       # few big chunks: each chunk pays a browser start-up
        jobs = [(str(prj.dir), todo[a:a + size], [keys[n] for n in todo[a:a + size]], str(tmp), fps) for a in range(0, len(todo), size)]
        done = 0
        with Pool(min(workers, len(jobs))) as pool:
            for k in pool.imap_unordered(_chunk, jobs):
                done += k
                print(f"  frames {done}/{len(todo)}", flush=True)
    if draft:
        dd = prj.dir / "renders" / "drafts"; dd.mkdir(parents=True, exist_ok=True)
        out = dd / (re.sub(r"[^A-Za-z0-9]+", "_", prj.dir.name).strip("_") + "_draft.mp4")
    else:
        out = prj.next_out()
    try:
        c = av.open(str(out), "w", options={"movflags": "+faststart"})
        codec, opts = h264_encoder()
        vs = c.add_stream(codec, rate=fps); vs.width, vs.height, vs.pix_fmt = prj.W, prj.H, "yuv420p"
        vs.options = opts(26 if draft else crf)
        ast = c.add_stream("aac", rate=SR); ast.layout = "stereo"; ast.bit_rate = 192000
        thumbs = []
        print(f"encode -> {out}", flush=True)
        for n in range(N):
            img = Image.open(tmp / f"{keys[n]}.jpg").convert("RGB")
            vf = av.VideoFrame.from_image(img); vf.pts, vf.time_base = n, Fraction(1, fps)
            for pk in vs.encode(vf):
                c.mux(pk)
            if n % (fps * 3) == fps:
                thumbs.append(img.resize((480, int(480 * prj.H / prj.W))))
        for pk in vs.encode():
            c.mux(pk)
        mix = soundtrack(prj)
        mix = np.pad(mix, ((0, 0), (0, (-mix.shape[1]) % 1024)))
        for s in range(0, mix.shape[1], 1024):
            af = av.AudioFrame.from_ndarray(np.ascontiguousarray(mix[:, s:s + 1024]), format="fltp", layout="stereo")
            af.sample_rate = SR; af.pts = s
            for pk in ast.encode(af):
                c.mux(pk)
        for pk in ast.encode():
            c.mux(pk)
        c.close()
    except BaseException:                                 # never leave a half-written version behind
        out.unlink(missing_ok=True)
        raise
    keep = set(keys)                                      # keep only this render's frames: the cache never grows past one film
    for f in tmp.glob("*.jpg"):
        if f.stem not in keep:
            f.unlink(missing_ok=True)
    if draft:
        print(f"draft: {out}  ({prj.total:.1f}s at {fps} fps; for checking pacing only, QA not enforced)")
        return out
    cs = out.with_suffix(".contact.jpg")
    if thumbs:
        w, h = thumbs[0].size; cols = 6
        S = Image.new("RGB", (w * cols, h * math.ceil(len(thumbs) / cols)), "white")
        for k, im in enumerate(thumbs):
            S.paste(im, ((k % cols) * w, (k // cols) * h))
        S.save(cs, quality=85)
    srt(prj, out.with_suffix(".srt"))
    (out.with_suffix(".qa.txt")).write_text("\n".join(f"{l} {w}: {m}" for l, w, m in issues) or "no issues", encoding="utf-8")
    try:
        from .workflow import save_score
        save_score(prj, out, issues)
    except Exception as e:                                # the score is a helper; never fail a finished render over it
        print(f"  (score not saved: {e})")
    print(f"done: {out}  ({prj.total:.1f}s)\n  contact sheet: {cs}\n  subtitles: {out.with_suffix('.srt')}")
    return out


def audio_preview(prj: Project):
    out = WORK / f"{prj.dir.name}_audio_preview.wav"; out.parent.mkdir(parents=True, exist_ok=True)
    write_wav(out, soundtrack(prj)); print("audio preview ->", out); return out


def thumbnail(prj: Project, scene=0, at=.75):
    sc = prj.scenes[scene]; fr = Frames(prj)
    try:
        img = fr.raw(sc["_start"] + sc["dur"] * at)
    finally:
        fr.close()
    out = prj.dir / "renders"; out.mkdir(exist_ok=True); p = out / "thumbnail.png"; img.save(p); print("thumbnail ->", p); return p
