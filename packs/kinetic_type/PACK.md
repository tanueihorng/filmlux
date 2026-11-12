# Pack: kinetic_type

**For:** type-only films where the words are the visuals: manifestos, announcements, values, event openers, "why we exist". Works muted on social. 20–60 s.

**Defaults:**
- Theme `brutal` (loud), `swiss` (clean), `chrome` (hype) or `neon`.
- Motion `slam`, `snappy` or `mask`. Transition `cut` or `slide`.
- Music `upbeat` or `cinematic`. Voice optional; with a voice, captions `none` (the type already says it).

**Beats** (the story; choose a scene type and a `layout` for each: `python studio.py scenes`):
1. **Hook**: 2–3 punchy lines
2. **Turn**: a big number or word
3. **Core message**: one phrase per line
4. **Proof**: the single number
5. **Payoff**
6. **Call to action**

**Treatments** (offer the user 2–3 before writing the script; each is a different structure, not only a different look):
- **Drumbeat**: full-screen lines that replace each other.
  `kinetic` center → `section` center → `kinetic` center → `stat` giant → `end` band
- **Wall of words**: the words are the picture; one phrase lights up.
  `wordwall` rows → `kinetic` stack → `countdown` → `wordwall` stack → `end` left
- **Poster series**: each scene a typographic poster.
  `title` giant → `quote` huge → `stat` left → `title` bottom → `end` left

**Signature scenes:** `wordwall`, `countdown`, `kinetic` layout `stack`, library `scenes/split_flap`. Use at least one; they make this pack look like itself.

**The original Shape** (still a valid treatment, the most conventional one):
1. `kinetic`: 2–3 punchy lines, one idea each ("Stop searching." / "Start <em>knowing</em>.")
2. `section`: a big number or word that marks the turn
3. `kinetic`: the core message, one phrase per line
4. `stat`: the single number that proves it
5. `kinetic`: the payoff
6. `end`: the call to action

**Craft:**
- Three to five words per line. Put the one important word in `<em>`.
- Cut on the beat: keep scenes 2–4 s, and let `motion` carry the energy.
- One motion style per film; switch it for a single scene only for emphasis (`"motion": "slam"`).
- Try `look.text`: `shadow` (hard offset), `outline` (stroked) or `chrome`.

**Avoid:**
- paragraphs; more than one idea per screen
- mixing more than two fonts
