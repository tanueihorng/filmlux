# PLAYBOOK.md: the craft of a good product video

These rules come from building a product walkthrough over seven versions, each driven by one sentence of feedback from real viewers and stakeholders. They apply to any video this studio makes.

**How to read this playbook.** Each section gives defaults that reliably produce a good film. They are a floor, not a ceiling. Depart from any of them when the idea is stronger for it, and tell the user what you changed and why. The only things that never bend are the hard rules in `AGENTS.md` §2 and the scorecard in §7: whatever the style, the result has to pass it.

## 1. Story first

- **Start from the viewer's gap.** What do they not know, or not believe, today? Write it as one sentence in the brief.
- **Tell a journey, not a feature list.** Follow one person and one task from problem to result. Each feature appears at the moment it's needed.
- **End where you started, but changed.** Show the result of the journey, the "closed loop", then a clear call to action.
- **Shape (60–90 s):**
  1. hook (title or kinetic, 5 s)
  2. the problem or promise (1 scene)
  3. 3–5 beats of value
  4. proof (stat, quote or demo)
  5. recap (bento or process)
  6. end card with CTA
- **Write the chapter list before anything else.** If the list doesn't read like a story, the video won't either.

## 2. Words

- **On screen:** titles of 3–8 words, bullets of 2–6 words, at most 5 bullets. One idea per scene.
- **Highlight one or two words** per title with `<em>`.
- **Captions:**
  - one line of about 72 characters (longer lines are split automatically)
  - say what is happening and why it matters
  - name the menu item when the viewer should click it

## 3. Voice (natural, never robotic)

- **Write for the ear:**
  - 6–25 words per scene
  - spell out abbreviations ("single sign-on", not "SSO")
  - use full sentences, with punctuation for rhythm ("Step one. Explore.")
- **Describe what the viewer is seeing right now,** not what they saw a scene ago.
- **Voice choice:**
  - Ava (warm, the default)
  - Andrew (calm, for leadership)
  - Emma (bright, for onboarding)
  - Luna or Wayne (Singapore English)
- **Rate:** −4 % is comfortable, −8 % calm for training, 0 % for teasers.
- **The voice is never rushed:** scenes stretch to fit it. If a scene feels slow, shorten its line rather than speeding up the voice.
- **Listen to `python studio.py audio <name>` before every final render.**
- **Translated versions:** translate the `say` lines, pick a matching voice (`zh-CN-…`, `ms-MY-…`, `ta-IN-…`), and render. The timing refits itself.

## 4. Music and sound

- **The music supports the voice and never competes:**
  - the bed sits at about −27 dB
  - it ducks about 8 dB under speech, with 0.3 s fades
  - the master is levelled to about −18 dB RMS with a soft limiter
- **Moods:**
  - `calm`: tutorials, walkthroughs
  - `corporate`: updates, product
  - `upbeat`: promos, social
  - `cinematic`: openers, vision
  - `minimal`: voice-heavy content
- **No bells, dings, ticks or a whoosh on every cut.** Viewers call that "vibe-coded". The only effect is a soft swish into big moments.
- **For training, offer a voice-only edition** (`"music": "none"`), so nothing competes with the narrator. For launches, use voice plus music.

## 5. Visuals and motion

- **Motion with intent:** the default is calm and confident (eased entrances, 0.4 s dissolves, a slow background drift). Energy is a choice: bouncy, slam or glitch motion is right when the film's purpose is fun or hype, as long as the words stay readable and nothing flashes more than three times a second.
- **Hierarchy:** one hero element per scene. Leave space around it (the safe area is 8 % at the sides, 12 % top, 14 % bottom, or 21 % with captions).
- **Colour:** the theme's accent goes on one thing per scene (the key word, the active step, the main bar).
- **Data:** the user's real numbers only. Label anything illustrative as "Sample data". Use one chart per scene and at most 6 bars.
- **Pick the right scene type:**

  | Purpose | Scene types |
  |---|---|
  | Opener | `title`, `kinetic` |
  | Several features | `bento` |
  | Steps or a loop | `process` |
  | Change | `compare` |
  | A number | `stat` |
  | Proof | `quote` |
  | A screenshot | `split`, `image` |
  | A live product | `screen` |
  | Anything bespoke | `html` |

## 5b. Choosing a look (theme × caption style)

Pick the look from the **purpose and audience**, not from habit. The table is a starting point: combine themes, motion and captions in ways it doesn't list, or design a new theme (copy one in `themes/`) when the brand or idea calls for it. Keep one coherent look per film unless a deliberate shift serves the story.

| Purpose | Theme | Captions | Music |
|---|---|---|---|
| Product release / walkthrough | `navy` | glass | calm or corporate |
| Strategy, an announcement with authority | `swiss` | bar | minimal |
| Numbers, results, research | `newsroom` (or `swiss`) | bar | minimal |
| People, culture, onboarding, stories | `warm` | glass | calm |
| Vision, milestone, emotional opener | `cinema` | glass (or none) | cinematic |
| AI assistant or friendly product update | `aurora` | glass | upbeat or calm |
| Hype, tech, security; vertical social | `neon` | pop | upbeat |
| A launch that should feel loud and confident | `brutal` | bar | upbeat |
| Architecture, systems, how it works | `blueprint` (or `terminal` for developers) | bar | minimal or none |
| Training, policies, step-by-step | `whiteboard` | glass | calm (low) or none |
| Team stories, culture, community | `collage` or `riso` | glass | calm |
| Event hype, throwback, gaming | `vhs` or `chrome` | pop or bar | upbeat |
| Strategy or design with personality | `bauhaus` | bar | minimal |
| Friendly onboarding, HR, wellbeing | `clay` | glass | calm |

- **Pop captions** suit muted, phone-first viewing: short lines (6–14 words), big type, one lit word. Don't use them for long training videos.
- **Bar captions** read as editorial and serious. Keep each line under about 70 characters.
- **Film effects are seasoning.** Grain at 0.05–0.12, vignette 0.1–0.5, light leaks only in `cinema`. If a viewer notices the effect before the message, turn it down (`"look": {...}` in project.json).
- **Serif display themes** (`cinema`, `newsroom`, `warm`) look best with short, sentence-case titles and one italic accent word.
- **Condensed uppercase** (`neon`) needs very few words: three to five per title.
- **Motion follows the theme.** Each theme has a default `motion` and `transition` that suit it (see SPEC.md, **Motion and transitions**). Change them only for a reason: `typewriter` for technical or teaching content, `spring`/`bouncy` for friendly, `slam` for hype, `mask` for editorial, `heavy` or `focus` for cinematic weight.
- **One motion family per film.** Override `motion` on a single scene for emphasis (a `slam` on the hero stat), never scene by scene.
- **Transitions:** `fade` or `none` most of the time. Save `flash`, `glitch`, `iris`, `cube` and `clockwipe` for two or three key moments, and never flash more than three times a second.
- **New brand?** Copy the closest theme, change only the colours and logo first, and look at stills before touching type or effects.

## 6. Screen recordings (when the user provides them)

- **Recording tips to give the user:**
  - use a big monitor and a clean test account, one clip per step
  - move the mouse slowly, pause 1 s before each click and 2 s on each result
  - don't scroll sideways
- **Probe first:** `stills` every 1–2 s through each clip, and write down what happens when (page changes, clicks, loading). Most bugs come from not knowing exactly when the page changed.
- **Camera:**
  - new page: `est` 0.5–1.5 s (full screen), then ease in
  - zoom 1.4× or less
  - never zoom before the target is visible
- **Cause and effect:** a callout about 1 s before each click. Keep the click and its result in one scene (don't cut across it), then hold 1–3 s on the result.
- **Pace:** 1.0–1.35× on UI steps; speed up only waiting and typing.

## 7. The quality loop (do this every time)

### The scorecard (any style must pass it)

Score the draft before showing the user. Each line is an outcome, not a method: reach it however suits the film.

| # | The viewer… | How to check |
|---|---|---|
| 1 | knows what this is about within 5 s | the first still alone says it |
| 2 | can follow it on mute | read only the stills and captions: is the story there? |
| 3 | can read every word in time | no `qa` text-density warnings left unexplained; nothing clipped |
| 4 | sees one main thing per scene | each still has a clear focal point |
| 5 | never sees a sloppy frame | contact sheet: no blank, duplicate or broken frames |
| 6 | hears a voice and music that suit the purpose | `audio`: natural pace, music under the voice |
| 7 | trusts it | every number is real or labelled "Sample data"; no fake evidence |
| 8 | remembers one moment | name it; if you can't, strengthen the hero scene (a bolder scene type, an `html` scene, a motion or transition accent) |
| 9 | knows what to do next | the end card has a clear call to action |
| 10 | doesn't feel it's a template | at least one choice made for this film (look, structure, a custom scene, an unexpected line) |

All ten must pass. Report the score, plus anything you weren't sure about, with the stills.

### The loop

1. `plan`: check the total length and per-scene timing against the brief.
2. `stills`: **open the sheet and look.** Check for:
   - clipped or overlapping text
   - empty-looking scenes
   - wrong images
   - zoom too tight
   - captions over important content
3. `audio`: listen to the voice, pauses and music level.
4. `qa`: no ERRORs. For each WARN, fix it or keep the choice on purpose and note why.
5. Score the draft with the scorecard above.
6. `render`, then open the contact sheet. Every scene must appear, with no blank or black frames and no duplicates.
7. Report to the user: the path, the length, the scorecard, any default you broke on purpose, and anything you weren't sure about (with a still).
8. **Feedback:** change one thing per sentence of feedback, re-render (a new version is automatic), and keep a changelog in the project's `brief.md`.

## 8. Feedback, translated (real examples)

| Viewer said | Do this |
|---|---|
| "Zoomed in too much" | Full screen first (`est`), zoom 1.4× or less |
| "Too many bell rings" | Remove effects; keep the music bed only |
| "Too fast" / "too slow" | Change `speed` or `hold`; never cut the content |
| "I never see the click" | Use a continuous take, with a callout before the click |
| "No voiceover" | Add a `voice` and write `say` lines |
| "Voice and music is confusing" | Make a `"music": "none"` edition for comparison |
| "Not wow enough" | A stronger opener (`kinetic`), `bento` for the recap, the `cinematic` mood, an `html` custom scene for a hero moment, or a bolder theme (`aurora`, `neon`, `cinema`) |
| "Looks too corporate" | `warm` or `aurora` theme, the Emma voice, the `calm` mood, `image` scenes with real photos (or AI illustrations if allowed) |
| "Hard to read on my phone" | `9:16` format, `pop` captions, titles of 5 words or fewer, one idea per screen |
| "The effects are distracting" | Lower `grain`, remove `leak`/`glitch`/`scan`/`tracking` in `look` |
| "Too bouncy" / "too childish" | `"motion": "snappy"` (or `smooth`); raise `look.spring.damping` |
| "Feels static" / "more energy" | `"motion": "snappy"` or `"slam"`, `"transition": "slide"`, shorter scenes |
| "Too techy" | Swap `blueprint`/`terminal` for `paper` or `clay`, `"motion": "smooth"` |
| "Make it feel hand-made" | `collage` or `riso` theme, `"motion": "stopmotion"`, real photos |
