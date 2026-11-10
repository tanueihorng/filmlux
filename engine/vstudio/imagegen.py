"""Optional AI images: turn every scene/layer with a "gen" field into an exact request list for the coding
agent's image tool (or any image app the user prefers), then check what came back.

  python studio.py imagegen <project>           write assets/gen/REQUESTS.md + requests.json (what to generate, where to save)
  python studio.py imagegen <project> --check   verify the files exist, have the right shape, and log provenance

The studio never calls an image API itself: generation is done by the agent (or a person) and the files are
saved to the paths listed. Everything else (Ken Burns, parallax, captions, QA) works the same as any image.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from PIL import Image

from .render import IMAGE_TYPES, Project, gen_prompt

TARGET = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1440, 1440), "4:5": (1080, 1350)}
RULES = ("no text, no letters, no logos, no watermarks, no real people or recognisable faces, "
         "no brand names, no UI screenshots; leave calm negative space where a title can sit")


def _jobs(prj: Project):
    fmt = prj.spec.get("format", "16:9"); style = prj.theme.get("imagegen", "")
    jobs = []
    for i, sc in enumerate(prj.scenes):
        if sc["type"] not in IMAGE_TYPES:
            continue
        items = [(sc, "image")] if sc.get("gen") and not sc.get("layers") else []
        items += [(ly, "layer") for ly in sc.get("layers") or [] if ly.get("gen")]
        for k, (obj, kind) in enumerate(items):
            g = obj["gen"] if isinstance(obj["gen"], dict) else {"prompt": obj["gen"]}
            cut = g.get("cutout", kind == "layer" and k > 0)
            if sc["type"] == "split":
                ratio = sc.get("ratio", "16/10"); a, b = (float(x) for x in ratio.split("/")); size = (1600, int(1600 * b / a))
            else:
                size = TARGET.get(g.get("aspect", fmt), TARGET["16:9"])
            prompt = gen_prompt(g)
            full = f"{prompt}. Style: {g.get('style', style)}. {RULES}."
            if cut:
                full += " Isolated subject on a perfectly flat #00ff00 chroma-key green background (no green in the subject), soft even light, no shadow on the background."
            jobs.append({"scene": i + 1, "kind": kind, "file": obj.get("src"), "size": f"{size[0]}x{size[1]}", "cutout": bool(cut),
                         "prompt": full, "exists": Path(obj.get("_path", "")).exists()})
    return jobs


def requests(prj: Project):
    jobs = _jobs(prj)
    gd = prj.dir / "assets" / "gen"; gd.mkdir(parents=True, exist_ok=True)
    (gd / "requests.json").write_text(json.dumps(jobs, indent=2), encoding="utf-8")
    todo = [j for j in jobs if not j["exists"]]
    lines = [f"# Image requests: {prj.title}", "",
             f"{len(jobs)} image(s) in this project, **{len(todo)} still to generate**. For each one below:",
             "1. Generate it with your image tool (a built-in image tool, an image MCP server, or the user in any image app). Use the prompt exactly; request the size shown (or the nearest supported size with the same aspect ratio).",
             "2. Save it to the path shown (relative to the project folder). PNG or JPG.",
             "3. For `cutout: yes`, remove the green background afterwards with `python studio.py cutout <in.png> <save path>` (a transparent PNG).",
             f"4. Run `python studio.py imagegen {prj.dir.name} --check`, then open each image and look at it before using it.", ""]
    for j in jobs:
        lines += [f"## Scene {j['scene']} ({j['kind']}): `{j['file']}`  {'(done)' if j['exists'] else '(TO DO)'}",
                  f"- size: {j['size']}   cutout: {'yes' if j['cutout'] else 'no'}", "", "```", j["prompt"], "```", ""]
    (gd / "REQUESTS.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(todo)} of {len(jobs)} image(s) to generate -> {gd / 'REQUESTS.md'}")
    for j in todo:
        print(f"  scene {j['scene']:2d}  {j['size']:>9s}  {j['file']}")
    return gd / "REQUESTS.md"


def check(prj: Project):
    jobs = _jobs(prj); gd = prj.dir / "assets" / "gen"; gd.mkdir(parents=True, exist_ok=True)
    logf = gd / "provenance.json"
    log = json.loads(logf.read_text(encoding="utf-8")) if logf.exists() else {}
    bad = 0
    for j in jobs:
        p = prj.resolve(j["file"]); tag = f"scene {j['scene']} {j['file']}"
        if not p.exists():
            print(f"  MISSING {tag}"); bad += 1; continue
        try:
            im = Image.open(p); w, h = im.size
        except Exception as e:
            print(f"  BROKEN  {tag}: {e}"); bad += 1; continue
        tw, th = (int(x) for x in j["size"].split("x"))
        msg = []
        if abs(w / h - tw / th) > .04:
            msg.append(f"aspect {w}x{h} differs from {j['size']} (it will be cropped; regenerate or set 'focus')")
        if max(w, h) < 1200:
            msg.append(f"only {w}x{h}: will look soft at full screen")
        if j["cutout"] and im.mode not in ("RGBA", "LA"):
            msg.append("cutout layer has no transparency (remove the green background)")
        print(f"  {'WARN' if msg else 'OK'}    {tag}  {w}x{h}" + ("".join("\n          - " + m for m in msg)))
        rec = log.get(j["file"], {})
        if not rec or rec.get("prompt") != j["prompt"]:
            log[j["file"]] = {"prompt": j["prompt"], "size": f"{w}x{h}", "checked": dt.date.today().isoformat(), "source": "AI-generated"}
    logf.write_text(json.dumps(log, indent=2), encoding="utf-8")
    print("all images present" if not bad else f"{bad} image(s) missing or broken")
    return bad == 0
