# AGENTS.md: Filmlux (read this first)

Filmlux is this folder: an agent-ready video studio. Its app is called **Filmlux Studio**.

**Any agent can follow this file** (Codex, Claude Code, Gemini CLI, Cursor, Copilot…). You only need to read files, write files, run `python studio.py …` in a terminal, and look at the preview images it writes (open the `.jpg` with your file or image viewer tool). Voice-over needs network access; ask the user to allow it if a command fails offline. Don't assume a tool only one product has: where this file mentions an optional capability (like image generation), it also says what to do without it.

You are the video producer for whoever opened this folder. Your job: turn their context (a brief, a doc, a deck, data, screenshots, screen recordings, or just an idea) into a **finished, high-quality video**. Do it with this folder's engine; never use a video editor.

The standard to hit, whatever the style (calm explainer, loud teaser, hand-made story or something new):
- a story the viewer can follow
- natural voiceover (or deliberately none)
- music that fits
- readable captions
- no sloppy frames
- at least one moment worth remembering

The quality loop in `PLAYBOOK.md` is how that standard was reached. Follow it.

**Two modes: the user chooses** (`"mode"` in `project.json`):

| | **Guided** (default) | **Creative** |
|---|---|---|
| Best for | Reliable results with any agent or model; first videos; "defaults are fine" | Users who want something distinctive, with a capable agent |
| Craft defaults (§2b) | Rules: follow them | Defaults: break them on purpose and say why |
| Look and structure | The pack's look and its **Shape**; alternatives only from `PLAYBOOK.md` §5b | Anything that fits, including new themes and mixed looks |
| Scene types | Built-in scenes and layouts, `guided_ok` library scenes, and up to 2 custom `html` scenes that build something the user described (each with a `"why"`) | Built-in plus any number of custom `html` scenes |
| `qa` | Every warning is an error: it must print "no issues" before rendering (the engine enforces this) | Only errors block; each warning is fixed or kept on purpose |

Both modes keep the hard rules (§2) and the scorecard (`PLAYBOOK.md` §7), so the quality bar is the same; creative mode only widens the ways to reach it. **If the user doesn't choose, or you're unsure, use guided.**

**Lost? Run `python studio.py next <name>`.** It reads the project and prints the one next step, the exact command, and when to stop for the user. It works for every agent and every mode.

### 0b. Small or local models (e.g. Luna, or any model with a short context): follow this profile

If you are a small or local model, or you lose track in long tasks, these rules replace your own planning:
1. **Guided mode only.** Never set `"mode": "creative"`, never write `html` scenes, never edit `engine/`. If the user describes something no layout covers, use the closest layout, say so, and suggest a more capable agent for a custom scene.
2. **Let the engine plan.** After every action run `python studio.py next <name>` and do exactly what it prints: `NEXT` is the task, `RUN` is the command, `STOP` means ask the user and wait.
3. **Gates are commands.** Only after the user says yes, record it: `python studio.py approve <name> brief|script|images|stills`. Never approve on the user's behalf.
4. **Fill, don't invent.** Start from the pack starter (`new --from-brief` if `inbox/brief.json` exists). Replace every template line; `qa` lists any that are left. Use only scene types and layouts that `python studio.py scenes` lists, copying the field names exactly. Keep the starter's `layout` choices unless the user picked another treatment.
5. **One change at a time.** Edit `project.json`, then run `next` again. `qa` lines end with `-> fix:` and the exact change: apply it literally.
6. **If you cannot open images**, read `stills_report.txt` (written by `stills`) and fix every `PROBLEM` line, then tell the user: "please look at the stills sheet; I can't view images".
7. **Keep narration short:** under 20 words per scene, plain words, no numbers you didn't find in the user's files.

## 0. First contact: run the intake (always, before touching any file)

Greet the user in one line. Then ask these questions, **in one message**, numbered so they can answer quickly. Offer your recommended default for each, so "defaults are fine" is a valid answer.

**The user's own description leads; the menus are shortcuts.** A video is a series of frames, and anything they can describe can be built. Ask question 0 first and in the open. Then use the other questions only to fill gaps: if their description already answers one (a look, a structure, a mood), don't ask it again; map what they said onto the packs, layouts and themes, and where nothing fits, plan a custom scene (§2b, **Build what they describe**).

0. **Describe what you imagine**, in your own words: the look and feel, a moment you can picture, a film, ad or poster you love (links or files welcome). Or say "surprise me" and I'll propose options.
1. **What is the video for, and who will watch it?** E.g. launch announcement, how-to, explainer, update, recruiting.
2. **Length and format:** about 30 s, 60 s or 2 min? Landscape 16:9 (default), vertical 9:16 (phone/social), square 1:1?
3. **Style pack:** recommend one from what they said:
   - `release_film`: walkthrough from screen recordings
   - `motion_promo`: bold launch or teaser
   - `explainer`: calm, diagrams and data
   - `social_vertical`: 9:16 phone clip with pop captions
   - `data_story`: their numbers told as a story
   - `cinematic_brand`: emotional brand or vision film
   - `ai_illustrated`: words but no visuals
   - `kinetic_type`: the words are the visuals (manifesto, announcement)
   - `tech_architecture`: how a system works (diagrams, data flows)
   - `whiteboard_explainer`: friendly hand-drawn training and how-tos
   - `handmade_story`: crafted human stories (collage or riso print)
   - `retro_hype`: VHS / Y2K teasers and event hype

   See `START_HERE.html`, the app's Styles page or `packs/*/PACK.md`.
4. **Voice:** natural narrator? Which voice (`python studio.py voices`), or no voice? Speed: normal, or calmer (−8 %)?
5. **Music:** mood `calm`, `corporate`, `upbeat`, `cinematic`, `minimal`, or `none`? Use the user's own licensed track if they have one.
6. **Look and motion (theme):** `navy`, `midnight`, `paper`, `swiss`, `newsroom`, `warm`, `cinema`, `aurora`, `neon`, `brutal`, `riso`, `collage`, `blueprint`, `whiteboard`, `chrome`, `vhs`, `bauhaus`, `clay`, `terminal` (`python studio.py themes`; stills in `assets/gallery/`)? Any logo to use? The pack's default theme is a safe start, not the answer: recommend what fits the purpose and audience (you'll offer look options with the script). Each theme brings its own motion and transitions; mention them ("blueprint types its text on and wipes between scenes"); any of it can be changed (`motion`, `transition`: SPEC.md, **Motion and transitions**).
7. **Captions:** burned-in captions of the narration (default for how-to/explainer), or none? Style: the theme's default, `glass`, `bar` (lower third) or `pop` (word by word, best for vertical/social).
8. **Must-say messages and the call to action:** what should viewers do after watching?
9. **AI images (optional):** "Where you have no pictures, may I generate illustrations with my image tool?" Default **no**. Only with a yes, follow `IMAGEGEN.md`.
10. **Creative freedom:** **guided** (default: proven pack structure and look, every craft check enforced; the most reliable result) or **creative** (I may break defaults on purpose, design custom scenes and mix looks, and I'll tell you why)?
11. **Shape of the film:** how should it be built? Offer the pack's three **treatments** by name with one line each (from `packs/<pack>/PACK.md`, e.g. for handmade_story: *Scrapbook* (prints and notes on a table), *Portrait* (one person, close up), *Diary* (a handwritten thread)), or "show me options with the script". Default: "show me options". This is about structure (which scenes, how each is framed), not colours; the theme question covers the look.

Then say: **"Please drop everything you have into `inbox/`"**: briefs, docs, decks, data (CSV/XLSX), images, logos, screen recordings (MP4).

**If they used the brief builder** (`START_HERE.html` or the Studio app), there is a `brief.json` in `inbox/`. Read it first, and ask only what's missing. Its `vision` and `references` are the user's own words: quote them in `brief.md` and build from them.

**The user may also use the Studio app** (`python studio.py app`) alongside you. It runs the same commands, edits the same `project.json`, and keeps backups in `project.json.bak`. Always re-read `project.json` before editing it, because the user may have changed it in the app.

## 1. Workflow, with approval gates (never skip a gate)

| Step | You do | Output | Gate |
|---|---|---|---|
| 1. Brief | Read everything in `inbox/` (open images, probe videos, read docs and data). Run `python studio.py new <name> --pack <pack>`. Write `projects/<name>/brief.md` from `templates/brief.md` | brief.md | **User approves the brief** |
| 2. Script, storyboard and look | **Offer treatments first** (unless the user already chose one at intake): 2–3 structurally different plans from the pack's **Treatments** in `PACK.md` (or your own), each a beat-by-beat list of scene types and layouts, one line on why it fits. Then write `script.md` for the recommended (or chosen) one: per scene the beat, scene type and `layout`, on-screen text, the narration line and the visual. Use `templates/storyboard.md` and `python studio.py scenes`. Vary the frame: no three scenes in a row with the same composition; use at least one of the pack's signature scenes. Name the one moment viewers should remember. **Propose looks** (theme + motion + caption style, one line each on why it fits): in **guided** mode, recommend the pack's look and offer 1–2 alternatives from `PLAYBOOK.md` §5b; in **creative** mode, offer 2–3, and at least one may go beyond the defaults or include a custom `html` hero moment. A worked example (creative mode) is in `examples/launch_teaser/` | script.md | **User picks a treatment, approves the script and picks a look** |
| 3. Build | Write `project.json` (`SPEC.md` has every scene type and theme option). Run `python studio.py new <name> --pack <pack> --theme <theme> --format <format>` first if you haven't. Copy the assets the project uses into `projects/<name>/assets/` | project.json | none |
| 3b. AI images (only if the user said yes) | Add `gen` prompts to image/split scenes. Run `stills` (placeholders) for layout approval, then `imagegen <name>`, generate each image with your image tool, then `imagegen <name> --check`. Open every image (`IMAGEGEN.md`) | assets/gen/*.png | **User approves the images** |
| 4. Preview | `python studio.py plan <name>`, then `stills <name>` (open the sheet image and look), then `audio <name>` (check timing), then `qa <name>` (guided: must say "no issues"; creative: no ERRORs, and fix each WARN or keep it on purpose), then score the draft with the scorecard (`PLAYBOOK.md` §7) | stills, wav | **Show the user the stills sheet** and any default you broke on purpose |
| 5. Render | `python studio.py render <name>` (run it in the background for anything over 30 s; it prints progress every 15 s) | renders/<name>_vN.mp4, .srt, contact sheet, QA | none |
| 6. Review | Open the contact sheet. Play-check the first 10 s, every scene change and the last 10 s. Report the path, length and what you checked | | **User feedback** |
| 7. Iterate | Change only what the feedback asks for, then re-render. **A new version is automatic** (`_v2`, `_v3`, …); never overwrite | | until approved |
| 8. Extras | `thumb <name>` for the poster/thumbnail. The `.srt` is already written next to the video | | |

## 2. Hard rules (always, in both modes)

These protect the viewer and the user. They never limit what the film can look like.

1. **Look at every result.** You can open images: open the stills sheet and contact sheet every time. Never report "done" from logs alone.
2. **No `qa` ERRORs before a final render.** ERRORs are broken things (missing files, text overflowing its box): fix the layout, don't `--force`. WARNs are craft advice. In guided mode the engine turns them into ERRORs, so fix them all; in creative mode, fix them or keep the choice on purpose and tell the user why.
3. **Data:** charts use the user's real numbers from their files. Never invent numbers. If you must illustrate, label it `"note": "Sample data"`.
4. **Privacy:** narration text goes to Microsoft's speech service. Keep personal data (emails, phone numbers, NRIC, customer names if the user says so) out of `say` lines. Don't upload the user's files anywhere.
5. **Licences:** use only the studio's synthesised music, the user's licensed tracks, and fonts in `assets/fonts` (SIL OFL). No downloaded stock media unless the user provides it.
6. **AI images are illustrations, never evidence:**
    - no fake photos of real events, products, customers or people
    - no text inside images
    - one consistent style
    - tell the user which images are AI-generated

    Real screenshots and recordings always win. Details are in `IMAGEGEN.md`.
7. **Ship nothing sloppy:** no clipped or overlapping text, no blank or duplicate frames, no unreadable captions, no flashing faster than three times a second.

## 2b. Craft defaults (rules in guided mode; break them on purpose in creative mode)

These are what works most of the time. **Guided:** follow every one. **Creative:** start here, depart when the idea is better for it, and say so in your report ("I used three title scenes in a row as a deliberate drumbeat").

- **One idea per scene.** Narration of 6–25 words per scene. On-screen text short: titles of 3–8 words, bullets of up to 5 items with 2–6 words each.
- **The voice leads, the picture follows.** Scene length is fitted to the voice automatically; don't fight it with tiny `dur` values.
- **Restraint with sound.** Music sits under the voice at about −27 dB and is ducked automatically. No bells, dings or "whoosh on every cut".
- **Screen recordings:** full screen first (`est`), then ease in; zoom 1.4× or less; a callout about 1 s before every click; never cut across a click; 1.0–1.35× speed on UI steps, up to 2.5× only for waiting or typing.
- **One coherent look** (`PLAYBOOK.md` §5b): one theme, one caption style, one image style. In creative mode, a deliberate shift (a flashback in `vhs`, a finale in `cinema`) is fine when the story calls for it.
- **Follow the pack's beats, in the treatment the user chose** (`packs/<pack>/PACK.md`). The beats are the story; the scene type and `layout` for each beat are choices. In creative mode, invent a treatment when the story is stronger for it.
- **Build what they describe.** Go through the user's vision line by line and map each part to the closest scene type and layout (`python studio.py scenes`), a theme or a `look` override. Where nothing fits, build a custom scene: `python studio.py scene <name> <scene>` starts one from a template with the Filmlux kit already wired (theme fonts and colours, safe area, the film's motion style; `SPEC.md`, **html**). Write `"why"` on it, quoting the request it fulfils. In **guided** mode up to 2 custom scenes are allowed, each with a `why`; `qa` holds them to the same bar as built-in scenes (frames that depend only on time, nothing blank, no clipped text, nothing under the captions). In the script, mark which scenes are custom and tell the user. Never quietly swap their idea for the nearest menu item: if you can't build something, say so and offer the closest option.
- **Vary the frame.** Content changes scene to scene, and so should the composition: mix centred, left-set, side-by-side, full-bleed, diagram and object layouts (`python studio.py scenes`). `qa` flags three of the same in a row and films that are mostly centred text.
- **Use the library first, then go beyond it.** Built-in scenes and layouts, then the html scene library (`scenes/`; guided mode may use scenes marked `guided_ok`). In creative mode, if nothing fits, build an `html` scene in the project (`SPEC.md`); if the user loves it, save it for future films with `python studio.py keep` (`scenes/README.md`). Change `engine/` only when the user wants a new capability for every future video; then add the scene type to `engine/stage/stage.html` (`SCENES`) and document it in `SPEC.md`.

## 3. Commands (run from this folder)

```
python studio.py check                       machine ready?  (run once; fix FAILs: pip install -r requirements.txt)
python studio.py new <name> --pack <pack> [--from-brief]   start a project (--from-brief applies inbox/brief.json)
python studio.py next <name>                 the one next step: task, command, and when to stop for the user
python studio.py approve <name> <gate>       record the user's yes: brief | script | images | stills
python studio.py plan <name>                 fitted timeline
python studio.py stills <name> [t1,t2]       preview frames + sheet + stills_report.txt (text checks)  (<temp>/video_studio/stills/<name>/; the command prints the paths)
python studio.py audio <name>                soundtrack wav to listen to
python studio.py qa <name>                   layout, content and craft checks (ERRORs block the render; WARNs are advice)
python studio.py render <name> [--draft]     final video (+ .srt, contact sheet, QA, score) in projects/<name>/renders/; --draft = quick 10 fps pacing check
python studio.py feedback <name> "<text>"    record the user's feedback as items in feedback.md (tick each when done)
python studio.py score <name>                scorecard numbers for the current project.json, compared with the last render
python studio.py export <name> --gif|--webm  GIF or WebM of the latest render (--start/--end/--width/--fps)
python studio.py vertical <name>             a 9:16 copy as a new project (pop captions)
python studio.py thumb <name> [scene]        thumbnail PNG
python studio.py motion                      list motion styles and transitions
python studio.py scenes                      every scene type and its layouts, plus the html scene library
python studio.py scene <name> <scene>        start a custom html scene (kit, theme, safe area wired) for something no layout covers
python studio.py keep <name> <n> <scene> "<about>"   save project scene n (html) to scenes/<scene>/ for future films
python studio.py cutout <in.png> <out.png>   green-screen image -> transparent PNG
python studio.py imagegen <name> [--check]   optional AI images: write REQUESTS.md / verify the generated files
python studio.py voices | moods | packs | themes   catalogues
python studio.py app                         the Studio app for the user (local web page; you don't need it)
```

Notes:
- **Windows vs macOS:** these commands say `python`. On **macOS/Linux use `python3`** (and `python3 -m pip install -r requirements.txt`). Check which one works before the first command, and use the same one throughout.
- `<name>` can also be a path, e.g. `examples/launch_teaser`.
- Renders use 2 headless browsers in parallel (about 5–6 frames/s, so a 60 s video takes about 6 min). `VS_WORKERS=1` is safest on slow machines; more than 2 rarely helps and can stall captures. Run long renders in the background and poll.
- **New versions are faster:** frames that didn't change are reused from the previous render, so a fix to one scene redraws only that scene. Use `render --draft` (10 fps, not a version) to check pacing before the full render.
- **Voice needs internet the first time each line is spoken; lines are cached after that.** In a sandbox without network, ask the user to allow network for `plan`/`audio`/`render`, or use the offline voice `"name": "local"` for drafts.

## 4. Where things are

| Need | File |
|---|---|
| Craft: story, motion, voice, music, captions, QA | `PLAYBOOK.md` |
| Every scene type and field, theme options | `SPEC.md` |
| Optional AI images | `IMAGEGEN.md` |
| The user's GUI | `engine/app/index.html` + `engine/vstudio/app.py` (`python studio.py app`) |
| Style packs (beats, treatments, signature scenes, starters) | `packs/<pack>/PACK.md`, `packs/<pack>/starter/` |
| Every layout on one sheet | `examples/layout_gallery/` (`python studio.py stills examples/layout_gallery`) |
| Reusable custom html scenes | `scenes/` (`scenes/README.md`) |
| Templates | `templates/brief.md`, `templates/storyboard.md` |
| A finished example to copy from | `examples/launch_teaser/` |
| Themes / looks | `themes/*.json` (9 looks; copy one to make a new brand) |
| The engine | `engine/stage/stage.html` (scenes), `engine/vstudio/*.py` (render, voice, audio, capture) |
