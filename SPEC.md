# SPEC.md: `project.json` reference

A project is a folder `projects/<name>/` containing `project.json`, plus `brief.md`, `script.md` and `assets/`. Renders go to `renders/`.

```json
{
  "title": "Product launch",
  "format": "16:9",
  "theme": "navy",
  "voice": {"name": "en-US-AvaNeural", "rate": "-4%"},
  "music": {"mood": "corporate", "level_db": -27, "whoosh": true},
  "captions": "narration",
  "brand_mark": true,
  "scenes": [ { "type": "title", "title": "Hello", "say": "Hello and welcome." } ]
}
```

## Top-level fields

| Field | Values | Default |
|---|---|---|
| `mode` | `guided`: every `qa` craft warning blocks the render, and custom `html` scenes are limited to 2, each with a `why` (the user's request it builds), for reliable results with any agent. `creative`: only errors block; warnings are advice the agent may override on purpose. See AGENTS.md | `guided` |
| `format` | `16:9` (1920×1080), `9:16` (1080×1920), `1:1` (1080×1080), `4:5` (1080×1350) | `16:9` |
| `theme` | `navy`, `midnight`, `paper`, `swiss`, `newsroom`, `warm`, `cinema`, `aurora`, `neon`, `brutal`, `riso`, `collage`, `blueprint`, `whiteboard`, `chrome`, `vhs`, `bauhaus`, `clay`, `terminal` (`python studio.py themes`), or a project-relative path to your own theme `.json` | `navy` |
| `motion` | How elements arrive: `smooth`, `snappy`, `spring`, `bouncy`, `heavy`, `mask`, `typewriter`, `stopmotion`, `focus`, `flip`, `slam`, `gentle`, `glitch`. See **Motion and transitions** | theme's (else `smooth`) |
| `transition` | How scenes change: `fade`, `none`, `slide`, `wipe`, `flip`, `clockwipe`, `iris`, `cube`, `zoom`, `dip`, `flash`, `blur`, `glitch`; add a direction with `:`, e.g. `slide:from-bottom`. See **Motion and transitions** | theme's (else `fade`) |
| `transition_timing` | `ease`, `linear` or `spring` | `ease` |
| `look` | Override parts of the theme's look for this project only, e.g. `{"grain": 0.08, "letterbox": true}` (fields under **Themes**) | none |
| `caption_style` | `glass` (frosted pill, centred), `bar` (lower-third bar, left), `pop` (big words, one 1–3 word chunk at a time, the spoken word lit in the accent colour: social/vertical). Overrides the theme | theme's |
| `voice` | `{"name", "rate"}`; `null` for no voice. Names: `python studio.py voices`. Rate: `"-8%"` calm, `"-4%"` default, `"+0%"` brisk. `"name": "local"` uses the computer's own speech engine offline (Windows SAPI, macOS `say`, Linux `espeak-ng`): nothing leaves the machine, but it sounds robotic, so use it for drafts or sensitive scripts | Ava, −4 % |
| `music` | `{"mood"}` with `calm`, `corporate`, `upbeat`, `cinematic` or `minimal`; or `{"file": "assets/track.mp3"}` for a licensed track; or `null` / `"none"`. Optional: `level_db` (bed loudness, default −27), `whoosh` (soft swish into title, stat, bento, kinetic and end scenes, default true) | `calm` |
| `captions` | `narration` (burn in each scene's `say`), `custom` (use each scene's `caption`), `none` | `narration` |
| `brand_mark` | Small logo/name top-left on content scenes (`theme.brand`) | `true` |

## Every scene

| Field | Meaning |
|---|---|
| `type` | One of the types below |
| `layout` | How the scene is composed on screen (see **Layouts**). Each type has a default; the others change the frame, not the content |
| `beat` | Optional note of the story beat this scene plays (e.g. `"hook"`, `"proof"`); not shown on screen |
| `say` | The narration line for this scene (6–25 words). The scene is lengthened automatically to fit it, plus 0.35 s lead and 0.7 s tail |
| `dur` | Minimum length in seconds (defaults per type, e.g. title 4.5, bullets 6). The voice can make it longer, never shorter |
| `caption` | Caption text when `captions` is `custom`; `false` hides the caption for this scene |
| `chapter` | A small label top-right, e.g. `"02 · PLAN"` |
| `transition` | How this scene arrives (see **Motion and transitions**), e.g. `"wipe:from-top"`, `"cut"`. `transition_s` sets the length, `transition_timing` the easing |
| `motion` | Override the motion style for this scene only, e.g. `"slam"` on the hero stat |
| `glow_x`, `glow_y` | Position (0–1) of the soft background glow, to balance the layout |

Text fields accept `<em>word</em>`, which shows the word in the accent colour in italic serif. Use it on one or two words per title, no more.
`<br>` forces a line break.

## Layouts

The same content can be framed in several ways. Set `"layout"` on a scene; leave it out for the default (listed first). `python studio.py scenes` prints this table with each layout's composition family. A gallery of every layout is in `examples/layout_gallery/`.

| Type | Layouts |
|---|---|
| `title` | `center` · `left` (left-aligned) · `bottom` (label top-left, big headline anchored low, poster-like) · `giant` (headline fills the frame) · `photo` (full-bleed `src` picture, white headline low-left; needs `src` or `gen`) |
| `kinetic` | `center` (each line replaces the last) · `stack` (lines build up, earlier ones dim) |
| `bullets` | `split` (heading left, cards right) · `stack` (heading on top, items as columns) · `big` (no cards: big numbered lines between rules) |
| `stat` | `center` · `left` (number on the left, label beside it) · `giant` (label on top, the number huge along the bottom) |
| `quote` | `center` · `side` (a big quote mark, or the speaker's photo with `src`, beside the words) · `note` (handwritten on a taped sticky note) · `huge` (left-aligned, words light up as the voice reads) |
| `chart` | `full` · `side` (headline and source in a column beside the chart) |
| `image` | `frame` · `full` (same as `full: true`) · `polaroid` (a tilted print; `title` becomes its handwritten caption; `tilt` in degrees) |
| `split` | `side` · `overlap` (picture runs off one edge, words on a card over it) · `full` (picture fills the frame, card in a corner) · `stacked` (headline and body on top, a wide band of picture below) · `polaroid` (the picture as a tilted print, `label` is its caption) |
| `bento` | `grid` · `row` (one row of equal tiles) · `pinboard` (cards pinned at angles) · `list` (editorial rows divided by rules) |
| `compare` | `cards` · `halves` (the frame split in two, the "after" half tinted with the accent) |
| `section` | `side` · `center` (the number as a huge watermark behind the title) |
| `timeline` | `line` · `steps` (a staircase climbing to the right) · `vertical` (headline column, milestones down a line) |
| `end` | `center` · `left` (set low-left) · `band` (the closing line on a full-width accent band) |
| `polaroids` | `pile` · `row` |
| `note` | `sticky` · `card` (lined index card) |
| `annotate` | `side` (numbered list beside the picture) · `over` (labels on the picture) |
| `chat` | `center` · `side` (headline column beside the conversation) |
| `wordwall` | `rows` (drifting rows of words) · `stack` (a stacked word list) |

Layouts adapt to portrait formats (side-by-side ones stack). `qa` warns about an unknown layout, about three scenes in a row with the same **composition** (centred, left-type, side-by-side, grid, full-bleed, diagram, objects), and about a film where most scenes are centred text.

## Scene types

### `title`
`eyebrow`, `title`, `sub`, `align` (`center` or `left`). Opens the film or a chapter. Its words rise in one by one.
```json
{"type": "title", "eyebrow": "Release 1", "title": "From insight to a <em>closed loop</em>", "sub": "Everything in one place.", "say": "..."}
```

### `kinetic`
`lines` (2–4 short lines). Each line takes the full screen in turn; the last one holds. Good for punchy promos.
```json
{"type": "kinetic", "lines": ["Know every account.", "Reach the right people.", "<em>Close</em> the loop."]}
```

### `bullets`
`eyebrow`, `heading`, `items` (strings, or `{"title", "body"}`; up to 5), `numbered` (default true; false shows ✓).

### `stat`
`eyebrow`, `value` (e.g. `"3,318"`, `"98%"`, `"S$1.2M"`: the number counts up), `label`, `sub`. Use the user's real figures only.

### `quote`
`text`, `by`, `role`.

### `chart`
`kind` (`bar` horizontal, `column`, `line`, `donut`), `title`, `eyebrow`, `data` (`[["label", value], ...]` or `[{"label", "value"}]`), `unit` (e.g. `"%"`), `prefix` (e.g. `"S$"`), `decimals`, `note` (source or "Sample data"). Bars and columns grow, the line draws, the donut sweeps.

### `process`
`title`, `steps` (strings, or `{"title", "body"}`; 3–7), `loop` (true draws a ring). Steps light up in order as the path draws.

### `image`
`src` (path relative to the project, or `inbox/...`), `title`, `move` (`in`, `out`, `left`, `right` or `up`: slow Ken Burns), `fit` (`cover` or `contain`), `focus` (CSS object-position), `full` (true for full-bleed, no frame; a title gets a soft shade behind it).
- `layers`: `[{"src", "depth", "gen"}]` instead of `src`, for **parallax**. Layer 0 is the background (`depth` 0, slow); later layers are transparent PNG cutouts (`depth` up to 1, faster). They all follow `move`.
- `gen`: an AI image to generate for this scene (or layer). See `IMAGEGEN.md`. Until the file exists, previews show a placeholder and `qa` blocks the render.

### `split`
`eyebrow`, `title`, `body`, `src`, `side` (`right` default, or `left`), `ratio` (default `"16/10"`), `focus`, `gen` (optional AI image, as for `image`). Text on one side, an image or screenshot on the other.

### `bento`
`title`, `cols` (default 4; 2 in portrait), `tiles`: `[{"label", "title", "body", "value", "size": "1x1" | "2x1" | "1x2" | "2x2", "accent": true}]`. An Apple-style grid; tiles pop in one by one, and `value` counts up.

### `compare`
`title`, `left` and `right`: `{"label", "title", "items": [...]}`. Before vs after, or old vs new.

### `section`
`number` (e.g. `"02"`; it counts up and keeps leading zeros), `eyebrow`, `title`, `sub`. A chapter card with a giant accent number. Use between parts of a longer film.

### `timeline`
`title`, `items`: `[{"when", "title", "body"}]` (3–6). The line draws and milestones light up in order; items alternate above and below (stacked in portrait). For roadmaps, history, next steps.

### `logo`
`src` (defaults to the theme logo), `name` (text if there is no logo), `height`, `tagline`. A brand sting: the mark scales in with a glow and a light sweep, then the tagline.

### `end`
`title`, `sub`, `cta` (button text), `logo` (default true: the theme logo).

### Signature scenes
Each pack leans on a few of these (see `packs/<pack>/PACK.md`). They give a film a shape the classic types don't.

**`polaroids`**: `title` (optional), `photos`: `[{"src", "caption", "gen"}]` (2–5), `ratio` (default `"4/3"`). Prints drop onto a pile (or a row) one by one, captions handwritten. Real photos only for people.
```json
{"type": "polaroids", "title": "From the <em>shoot</em>", "photos": [{"src": "assets/a.jpg", "caption": "day one"}, {"src": "assets/b.jpg", "caption": "launch"}]}
```

**`note`**: `title` (optional, accent ink), `text` (handwritten), `items` (optional checklist; boxes tick in turn), `by`, `tilt`. A sticky note or a lined index card; the words write on.
```json
{"type": "note", "layout": "card", "text": "Find the <em>ground truth</em> first.", "by": "the team"}
```

**`countdown`**: `eyebrow`, `from` (default 3), `to` (default 1), `then` (the line it counts down to), `sub`. Numbers slam in inside a closing ring, then the reveal.

**`wordwall`**: `words` (list) or `text`, `highlight` (the lit phrase, may use `<em>`). `rows`: the frame fills with drifting rows of the words and the highlight sits on a plate in the middle. `stack`: the words pile up left-aligned, the highlight last in the accent colour.

**`annotate`**: `src` (screenshot, diagram or chart image), `title`, `notes`: `[{"x", "y", "text", "w"}]`: `x`/`y` are the centre of the mark as 0–1 fractions of the picture, `w` its width (default 0.14). Hand-drawn rings draw on in turn with numbered badges; `side` lists the notes beside the picture, `over` puts labels on it.
```json
{"type": "annotate", "src": "assets/dashboard.png", "title": "What's <em>new</em>", "notes": [{"x": 0.22, "y": 0.3, "text": "Filters remember you"}, {"x": 0.7, "y": 0.62, "text": "Export in one click"}]}
```

**`chat`**: `title`, `eyebrow`, `name` (assistant name in the header), `messages`: `[{"from": "user" | "bot", "text"}]`. Messages arrive in turn; the assistant shows typing dots first; older messages scroll up. Give it a `dur` of about 2 s per message.

### `screen` (footage: screen recordings, product demos, any MP4, or a still screenshot)
| Field | Meaning |
|---|---|
| `src` | The MP4 (project-relative or `inbox/...`), **or a screenshot** (`.png`, `.jpg`, `.webp`): the camera tours the still. Capture screenshots at 2× for sharp close-ups |
| `a`, `b` | Source in and out seconds (MP4 only) |
| `dur` | Screenshot only: how long to show it (the voice can lengthen it) |
| `speed` | Playback speed. 1.0–1.35 for UI steps; up to 2.5 for waiting or typing (QA warns above 1.5 unless `"fast_ok": true`) |
| `hold` | Seconds to freeze on the last frame (added automatically if the voice needs more time) |
| `est` | Seconds to show the full screen before the camera eases in (use 0.5–1.5 on every new page) |
| `cam` | Camera keyframes `[[t, cx, cy, zoom], ...]`. `t` is seconds after `est`; `cx`/`cy` are the centre as 0–1 fractions of the source frame; `zoom` is 1.0–1.4. Moves ease between keys |
| `callouts` | `[[t0, t1, x0, y0, x1, y1], ...]`: a highlight box in 0–1 source fractions, shown from t0 to t1 (after `est`), with the rest of the window dimmed. Add a 7th item for a label chip: `[1.5, 4, 0.2, 0.26, 0.55, 0.29, "12 style packs"]` |
| `cursor` | `[[t, x, y], ...]`: an animated pointer moving between points (0–1 source fractions, `t` after `est`). Use it on screenshots, or on recordings made without a visible cursor |
| `clicks` | `[t, ...]`: a click ripple (and a small press of the cursor) at each time |
| `typing` | `[{"t", "box": [x0, y0, x1, y1], "text", "cps": 14}]`: text typed into an input box (covers the placeholder; colours follow the box). Optional `size` in source pixels. Long text wraps |
| `toasts` | `[[t0, t1, "Saved"], ...]`: a confirmation pill at the bottom of the window |
| `frame` | `true` (default): a floating rounded window on the theme backdrop that grows to full size as you zoom. `false`: full-bleed |

Find coordinates by opening a still (`python studio.py stills <name> <t>`) and reading positions as fractions of the frame. For a screenshot, read them straight off the image: x ÷ width, y ÷ height.

A guided tour of a screenshot (camera, cursor, typing, a labelled callout, a toast):
```json
{"type": "screen", "src": "assets/home.png", "dur": 7, "est": 0.6,
 "cam": [[0, 0.5, 0.5, 1.0], [1.0, 0.38, 0.3, 1.6]],
 "cursor": [[0.8, 0.6, 0.6], [1.6, 0.27, 0.22], [4.6, 0.27, 0.22], [5.4, 0.25, 0.42]], "clicks": [1.8, 5.6],
 "typing": [{"t": 2.0, "box": [0.209, 0.205, 0.55, 0.236], "text": "orbit-launch", "cps": 10}],
 "callouts": [[3.4, 5.0, 0.209, 0.263, 0.55, 0.291, "12 style packs"]],
 "toasts": [[5.8, 7.5, "Project created"]],
 "say": "Type a name, choose a style pack, then click Create project."}
```
Screenshots stay sharp up to zoom 2.0 (QA allows it for stills; recordings stay at 1.4 or less).
```json
{"type": "screen", "src": "inbox/demo.mp4", "a": 12.0, "b": 19.5, "speed": 1.1, "est": 0.8,
 "cam": [[0, 0.5, 0.5, 1.0], [1.2, 0.7, 0.35, 1.35]], "callouts": [[1.5, 4.0, 0.62, 0.28, 0.86, 0.36]],
 "say": "Open Accounts to see your whole book in one view."}
```

### `html` (custom composition: anything the scene library can't do)
`src`: your own HTML page, at the project's resolution. It must be deterministic by time, using **one** of:
- `window.renderAt = t => { ... }`: draw the frame for time `t` seconds (it may return a Promise)
- GSAP timelines created `paused: true` and registered as `window.__timelines = { main: tl }`. The engine calls `tl.seek(t)`. This is the HyperFrames convention, so HyperFrames-style compositions work. Bundle GSAP locally (no network at render time).

Set `window.ready = true` when assets are loaded. Never use `Date.now()`, `requestAnimationFrame` loops or CSS animations that run on wall-clock time: frames must depend only on `t`.

`props`: any data for the page. Before the first frame the engine sets `window.FILMLUX = {props, theme: {colors, type, mode}, width, height, dur, fonts, motion, captions}` and calls `window.onFilmlux(FILMLUX)` if the page defines it. Read words from `props` and colours from `theme.colors` so the scene can be reused.

`why`: the user's request this scene builds (quote them). Required for custom scenes in guided mode (up to 2 per film).

**Start from the template:** `python studio.py scene <project> <name>` writes `scenes/<name>/scene.html` in the project with the **Filmlux kit** wired in. The engine also injects the kit into every html scene, so `window.Kit` is always there inside `onFilmlux` and `renderAt`:

| Kit | What it does |
|---|---|
| `Kit.init()` | the film's theme colours (`--bg0`, `--ink`, `--accent`…) and fonts as CSS variables, plus classes `.kit-title`, `.kit-sub`, `.kit-eyebrow`, `.kit-card`; `<em>` = accent italic |
| `Kit.safe()` | a box inside the safe area, clear of the captions when they are on |
| `Kit.seg(t, a, b)`, `Kit.ease.out/inOut/back`, `Kit.spring(p, name)` | timing: progress between two times, easings, the same spring physics as the built-in scenes |
| `Kit.reveal(el, p, kind)` | an entrance in the film's motion style (`rise`, `left`, `right`, `scale`, `pop`) |
| `Kit.words(el)`, `Kit.fit(el, max, min)`, `Kit.px(n)` | split words for staggered reveals; shrink text to fit; design pixels at 1080p |

**`qa` checks custom scenes like built-in ones:** the page must have `renderAt` or paused timelines; the same `t` must give the same frame (no wall-clock animation); the frame must not be blank; at the last frame no text may overflow, leave the safe area or sit under the captions. Mark full-frame art (backgrounds, big decorative type) with `data-bleed` to exempt it from the safe-area check.

**The scene library** (`scenes/`, listed by `python studio.py scenes`): reusable html scenes, e.g. `{"type": "html", "src": "scenes/split_flap/scene.html", "props": {"eyebrow": "Now boarding", "lines": ["NEXT STOP", "LAUNCH"]}}`. Guided mode may use library scenes whose `scene.json` says `"guided_ok": true`. Save a good custom scene with `python studio.py keep <project> <scene#> <name> "<about>"` (see `scenes/README.md`).

## Motion and transitions

Two settings decide how a film *moves*. Set them in the theme (each theme has a default), for the whole project (top-level fields), or for a single scene (scene fields).

### `motion`: how things arrive

| Motion | Feel | Good with |
|---|---|---|
| `smooth` | Eased rise with a soft blur (the classic look) | Anything; `navy`, `paper`, `midnight` |
| `snappy` | Spring {damping 20, stiffness 200}: quick, minimal bounce | UI, promos, `brutal`, `swiss` |
| `spring` | Spring {damping 10, stiffness 100} (Remotion's default): playful bounce | Friendly, `bauhaus`, `clay` |
| `bouncy` | Spring {damping 8}: more bounce | Kids, social, celebrations |
| `heavy` | Spring {damping 15, stiffness 80, mass 2}: slow and weighty | Big statements, `cinema` |
| `mask` | Slides up from behind an invisible line (editorial) | `newsroom`, `riso`, `swiss` |
| `typewriter` | Text types on, character by character | `whiteboard`, `blueprint`, `terminal` |
| `stopmotion` | On twos, with a little hand-made "boil" | `collage`, `warm`, crafts |
| `focus` | Cinematic focus pull: from big and blurred to sharp | `cinema`, `aurora` |
| `flip` | Tips up towards the viewer | Lists, cards, reveals |
| `slam` | Drops in big and lands with a small shake | `kinetic_type`, `chrome`, hype |
| `gentle` | Slow, calm fade with a tiny rise, no blur | Training, wellbeing |
| `glitch` | Snappy with an RGB-split jitter on titles | `vhs`, `neon` |

Springs are real damped-spring physics, the same model as Remotion's `spring()`. Tune the theme's default spring with `look.spring` (`{"damping": 12, "stiffness": 120, "mass": 1}`) and `look.spring_speed` (1 = normal, 1.5 = faster).

### `transition`: how one scene becomes the next

Set on the scene that is **coming in**. The names follow Remotion's presentations, plus a few film ones.

| Transition | What happens | Default length |
|---|---|---|
| `fade` | Cross-dissolve (the default) | 0.4 s |
| `none` / `cut` | Hard cut | 0 |
| `slide` | The new scene pushes the old one out (`slide:from-left`, `:from-top`, `:from-bottom`; default from the right) | 0.6 s |
| `wipe` | A soft edge sweeps across (`wipe:from-top-right` and any of the 8 directions; default from the left) | 0.6 s |
| `flip` | The old scene turns edge-on and the new one turns in | 0.7 s |
| `clockwipe` | A clock hand sweeps round from 12 o'clock | 0.7 s |
| `iris` | A circle opens from the centre | 0.6 s |
| `cube` | Both scenes on the faces of a turning cube | 0.7 s |
| `zoom` | Push in through the old scene into the new one | 0.5 s |
| `dip` | Dip to black | 0.6 s |
| `flash` | Flash to the theme's light accent colour | 0.45 s |
| `blur` | Blur out, blur in | 0.5 s |
| `glitch` | Torn scanlines and colour split | 0.3 s |

Options: `transition_s` (length in seconds), `transition_timing` (`ease` default, `linear`, or `spring`, like Remotion's `springTiming`), `transition_direction` (instead of the `:direction` suffix).

**Taste:** one transition family per film. Use a special one (`flash`, `glitch`, `iris`, `cube`) on two or three key moments only, and `fade` or `none` elsewhere.

## Themes (`themes/*.json`)

A theme is the whole look: colours, typography, background, film effects and caption style. Any pack works with any theme.

| Theme | Look | Good for |
|---|---|---|
| `navy` | Deep navy, crimson accent, Inter + italic serif accents, particles, glass cards (the default) | Product films, internal launches |
| `midnight` | Neutral dark, violet accent | Brand-free version of the default |
| `paper` | Light grey-white, blue accent | How-tos, friendly explainers |
| `swiss` | Off-white, black grotesk type, one red accent, visible grid, outline cards, lower-third captions | Strategy, editorial, bold statements |
| `newsroom` | Newsprint white, serif headlines, blue accent, flat cards, lower-third captions | Data stories, results |
| `warm` | Cream paper, grain, Fraunces serif, terracotta | Culture, HR, onboarding, human stories |
| `cinema` | Black, warm gold, serif, letterbox, grain, light leaks, vignette | Brand films, vision openers, milestones |
| `aurora` | Drifting colour blobs, heavy sans, frosted glass | AI assistants, friendly product updates |
| `neon` | Near-black, magenta/cyan, condensed uppercase, mono labels, perspective grid, scanlines, glitch entrances, pop captions | Hype, tech, security, vertical social |
| `brutal` | Neo-brutalist: cream, black outlines, hard offset shadows, chunky type, yellow cards. Snappy + slide | Launches, campaigns, hot takes |
| `riso` | Risograph: two fluoro inks, halftone, misregistered titles, grain. Mask + wipe | Culture, zines, research, community |
| `collage` | Cut paper: kraft, taped cards at angles, hand-lettered eyebrows, grain. Stop-motion + slide up | Human stories, onboarding, team spotlights |
| `blueprint` | Technical drawing: cobalt, white linework grid, mono labels. Typewriter + wipe | Architecture, systems, engineering |
| `whiteboard` | Marker on white: hand-lettered titles, sketchy outline cards. Typewriter + wipe | Training, how-tos, policies |
| `chrome` | Y2K: liquid chrome titles, iridescent aurora, glossy cards. Slam + zoom | Hype reels, events, reveals |
| `vhs` | Retro tape: pixel type, chromatic titles, scanlines, tracking band. Glitch + glitch | Throwbacks, gaming, playful teasers |
| `bauhaus` | Modernist poster: cream, primary geometric shapes, bold grotesk. Spring + iris | Strategy, design, education |
| `clay` | Soft 3D: pastel aurora, puffy clay cards, chunky rounded type. Spring + zoom | Onboarding, HR, wellbeing, friendly tours |
| `terminal` | Developer: black, phosphor-green mono, scanlines, glow. Typewriter + cut | Engineering updates, APIs, AI tooling |

| Field | Meaning |
|---|---|
| `name`, `about` | Display name and a one-line description (shown by `studio.py themes` and the app) |
| `mode` | `dark` or `light` |
| `colors` | `bg0`, `bg1`, `bg2` (background gradient), `ink` (text), `muted`, `accent`, `accent2`, `card`, `line`, `glow` |
| `type` | `display`: `sans` (Inter Display), `heavy` (Inter 800), `serif` (Instrument Serif), `fraunces`, `grotesk` (Space Grotesk), `condensed` (Anton, uppercase), `mono` (JetBrains Mono), `chunky` (Bricolage Grotesque 800), `hand` (Caveat, hand-lettered), `pixel` (VT323). Optional: `body`, `eyebrow` (same names), `weight`, `case` (`upper`/`none`), `tracking`, `leading`. `<em>` accents follow the display family |
| `look` | `bg`: `dots`, `aurora` (+ `aurora`: list of colours, `aurora_alpha`), `grid` (+ `grid`: cell px), `horizon` (neon floor), `halftone` (print dots; `halftone_alpha`, `dot`), `blueprint` (technical grid), `iso` (isometric grid), `shapes` (Bauhaus shapes; `shape3` colour, `shapes_alpha`), `waves` (flowing lines), `plain`, `paper`. Effects: `grain` (0–0.2), `vignette` (0–1), `letterbox` (true), `leak` (true or 0–0.4: film light leaks), `scan` (scanlines), `glitch` (RGB-split title entrances), `tracking` (VHS rolling band). Titles: `text` (`shadow` hard offset, `misreg` print misregistration, `glow`, `chroma` colour fringe, `outline` stroked, `chrome` metallic). Motion: `spring` {damping, stiffness, mass}, `spring_speed`. Shape: `cards` (`glass`, `flat`, `outline`, `solid`, `brutal`, `paper` (taped, tilted; `tape` colour), `clay`, `glow`, `sketch`), `radius` (px), `glow` (false hides the soft glow) |
| `brand` | `{"name", "logo"}`: logo path relative to the studio root, e.g. `assets/logos/acme.png` |
| `caption` | `style` (`glass`, `bar`, `pop`), `fill` [r, g, b, a], `chip` [r, g, b] (accent: bar stripe / lit pop word), `ink` [r, g, b]. For `pop`: `font` (a file in `assets/fonts`, default `inter-800.woff2`), `upper` (default true) |
| `imagegen` | The style sentence appended to every AI image prompt in this theme (see `IMAGEGEN.md`) |
| `motion`, `transition`, `transition_timing` | The theme's default motion and transition (see **Motion and transitions**) |

Every effect is a pure function of time, so renders are identical every time.

To add a brand, copy the closest theme to `themes/<brand>.json`, set the colours, type, look and logo, and put the logo in `assets/logos/`. Check it with `python studio.py stills examples/all_scenes` after temporarily setting that example's theme.
