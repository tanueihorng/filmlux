# Pack: release_film

**For:** product walkthroughs and release films built from **screen recordings**: "here's the new feature, here's how to use it". It's the style of a typical software release walkthrough. Usually 2–5 min.

**Defaults:** theme `navy`; music `calm`; voice Ava −4 %; captions `narration`; screen scenes use `frame: true` (a floating window on the brand backdrop).

**Beats** (the story; choose a scene type and a `layout` for each: `python studio.py scenes`):
1. **Release and promise**
2. **Journey map**: the user's 4–6 steps
3. **Each step**: a chapter card, then 2–5 `screen` scenes, one action each
4. **Closing loop**: back where it started, now changed
5. **What's in the release**
6. **Where to start**

**Treatments** (offer the user 2–3 before writing the script; each is a different structure, not only a different look):
- **Walkthrough**: one user's journey through the release, step by step.
  `title` center → `process` loop → per step: `section` side + `screen` ×2–5 → `bento` grid → `end` center
- **Highlights**: the three changes that matter, each explained on a screenshot.
  `title` bottom → `bullets` big → `annotate` side ×3 → `compare` halves → `end` left
- **Ask the product**: a question to the assistant opens each chapter.
  `chat` side → `screen` ×2 → `chat` center → `screen` ×2 → `bento` list → `end` band

**Signature scenes:** `annotate`, `chat`, `section` chapter cards. Use at least one; they make this pack look like itself.

**The original Shape** (still a valid treatment, the most conventional one):
1. `title`: release name and promise
2. `process` with `loop` (or `bullets`): the journey map, e.g. the user's 4–6 steps
3. For each step:
   - a short `title` chapter card (`"chapter": "01 · EXPLORE"`)
   - 2–5 `screen` scenes: one action each, with its own narration line
4. The closing loop, back where the journey started, now changed
5. `bento`: what's in the release
6. `end`

**Screen craft** (see PLAYBOOK §6):
- probe each clip with stills every 1–2 s first
- `est` on every new page
- zoom 1.4× or less
- a callout about 1 s before each click
- speed 1.0–1.35×
- `hold` to let results land
- one click and its result per scene

**No recordings?** Ask for 2× screenshots of each page instead and tour them: `screen` scenes take a `.png` with `cursor`, `clicks`, `typing`, labelled `callouts` and `toasts` (SPEC.md).

**Recording brief to give the user:**
- big monitor, clean test data, one clip per step
- slow mouse, a 1 s pause before clicks, 2 s on results
- no sideways scrolling
