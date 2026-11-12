# scenes/: the reusable html scene library

Custom `html` scenes that worked in a real film, kept so the next film can use them. List them with `python studio.py scenes`.

**Use one** in `project.json`:

```json
{"type": "html", "src": "scenes/split_flap/scene.html", "props": {"eyebrow": "Now boarding", "lines": ["NEXT STOP", "LAUNCH"]}, "dur": 5, "say": "..."}
```

The engine hands each page `window.FILMLUX = {props, theme: {colors, type, mode}, width, height, dur, fonts}` and calls `window.onFilmlux(FILMLUX)` once before the first frame. Read text from `props` and colours from `theme.colors`, so the scene matches any film.

**Keep one** after the user has approved a film with a custom html scene (creative mode):

```
python studio.py keep <project> <scene#> <name> "<what it is, in one line>" [--guided-ok]
```

It copies the scene's folder to `scenes/<name>/` and writes `scene.json` (about, props, guided_ok). Before keeping it, make sure the page reads its words from `FILMLUX.props` rather than hard-coding them.

**Guided mode** may use a library scene only when its `scene.json` says `"guided_ok": true`. Add `--guided-ok` only when the scene is deterministic (frames depend only on `t`), passed qa in a rendered film, and its props are simple text fields.

Each folder: `scene.html` (deterministic by time: `window.renderAt(t)` or paused GSAP timelines; see SPEC.md `html`), `scene.json`, and any local assets it loads.
