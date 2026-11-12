# Pack: explainer

**For:** how it works, strategy, results, training, data stories. Calm, clear, trustworthy. Usually 60–150 s.

**Defaults:** theme `navy` or `paper` (light, good for data); music `calm` or `minimal` (or `none` for training); voice Ava or Andrew at −4 % to −8 %; captions `narration`.

**Beats** (the story; choose a scene type and a `layout` for each: `python studio.py scenes`):
1. **Question**: what this answers
2. **Map**: the 2–3 points ahead
3. **How it works**: steps, evidence, a marked-up screenshot
4. **Result**: the headline number or change
5. **Recap**
6. **Next step**

**Treatments** (offer the user 2–3 before writing the script; each is a different structure, not only a different look):
- **Guided tour**: point at the real thing: screenshots with numbered marks.
  `title` left → `bullets` big → `annotate` side ×2 → `stat` left → `end` center
- **Diagram first**: the system as a picture, built up step by step.
  `title` giant → `process` → `chart` side → `compare` halves → `bento` row → `end` left
- **Q&A**: a question and answer between a user and an assistant.
  `chat` center → `split` side → `process` → `note` card → `end` band

**Signature scenes:** `annotate`, `chat`, `note` layout `card`. Use at least one; they make this pack look like itself.

**The original Shape** (still a valid treatment, the most conventional one):
1. `title`: the question this video answers
2. `bullets`: the 3 points we'll cover
3. 3–5 beats: `process` (how it works), `chart` (evidence, real data), `split` (a screenshot with an explanation), `compare` (what changes)
4. `stat`: the headline result
5. `bento` or `process` with `loop`: the recap
6. `end`: what to do next

**Craft:**
- explain one thing per scene
- narration leads, visuals confirm
- charts use the user's real CSV/XLSX numbers; put the source in `note`
- for training, make a voice-only edition too

**Avoid:**
- charts with more than 6 categories
- numbers you can't trace to the user's files
- scenes over 14 s (split them)
