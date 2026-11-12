# Pack: data_story

**For:** results, KPI updates, research findings and business reviews: a story told with the user's real numbers. 45–120 s.

**Defaults:**
- Theme `newsroom` (editorial), `swiss` (bold grid) or `paper`.
- Caption style `bar`.
- Music `minimal` or `calm`. Voice Andrew or Emma −4 %.

**Beats** (the story; choose a scene type and a `layout` for each: `python studio.py scenes`):
1. **Finding**: the headline result, as a sentence
2. **Hero number**: one figure, with its source
3. **Evidence**: the chart that shows it
4. **Why**: what drove it
5. **Next**: what happens now
6. **Decision**: the ask

**Treatments** (offer the user 2–3 before writing the script; each is a different structure, not only a different look):
- **Newsroom**: editorial: a big number, then charts beside their headlines.
  `title` bottom → `stat` giant → `chart` side → `annotate` side on a chart or dashboard → `timeline` vertical → `end` left
- **Analyst's notebook**: the reasoning on paper: notes and marked-up screenshots.
  `note` card → `stat` left → `annotate` over → `compare` halves → `end` center
- **Countdown to the answer**: build suspense, then land the number.
  `kinetic` stack → `countdown` → `stat` center → `chart` full → `end` band

**Signature scenes:** `annotate`, `stat` layouts `giant` / `left`, `chart` layout `side`. Use at least one; they make this pack look like itself.

**The original Shape** (still a valid treatment, the most conventional one):
1. `title`: the headline finding as a sentence ("Replies doubled in four weeks")
2. `stat`: the hero number, with its source in `sub`
3. `chart`: `line` for trends, `column` for periods, `bar` for rankings, `donut` for shares
4. `compare` or a second `chart`: what drove it
5. `timeline`: what happens next
6. `end`: the decision or ask

**Craft:**
- One chart per scene and one message per chart. Put the message in the chart `title` ("Week 4 was the turning point"), not a label like "Replies by week".
- Numbers come only from the user's files. Always fill `note` with the source ("Source: CRM export, 3 Nov").
- Round for speech: say "about forty percent", show "41%".
- At most 6 bars or 8 points. Group the rest into "Other".

**Avoid:**
- 3D charts and dual axes
- decorative charts with no message
- invented numbers (label any illustration `"note": "Sample data"`)
