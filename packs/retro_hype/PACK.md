# Pack: retro_hype

**For:** throwback teasers, hackathons, gaming, events and playful launches that should feel like a tape or a Y2K ad. 20–45 s, often 9:16.

**Defaults:**
- Theme `vhs` (80s/90s tape) or `chrome` (Y2K). Motion `glitch` (vhs) or `slam` (chrome).
- Transition `glitch` (vhs) or `zoom` (chrome); try `flash` on the beat.
- Music `upbeat`. Voice optional (Andrew +0 %). Caption style `pop` for vertical.

**Beats** (the story; choose a scene type and a `layout` for each: `python studio.py scenes`):
1. **Hook**
2. **Marker**: a date or level number
3. **What's in it**: 3–4 items
4. **The number that excites**
5. **Payoff line**
6. **Date, place or link**

**Treatments** (offer the user 2–3 before writing the script; each is a different structure, not only a different look):
- **Arcade**: levels and countdowns.
  `countdown` → `section` center → `bullets` stack → `stat` giant → `end` band
- **Mixtape**: words looping like a tape.
  `wordwall` rows → `kinetic` stack → `polaroids` row → `kinetic` center → `end` left
- **Departure board**: the event as a destination.
  library `scenes/split_flap` → `title` giant → `bento` pinboard → `stat` left → `end` center

**Signature scenes:** `countdown`, `wordwall`, library `scenes/split_flap`. Use at least one; they make this pack look like itself.

**The original Shape** (still a valid treatment, the most conventional one):
1. `kinetic`: the hook ("Press <em>play</em>.")
2. `section`: a date or level number ("01")
3. `bento` or `bullets`: what's in it, 3–4 items
4. `stat`: the number that excites
5. `kinetic`: the payoff line
6. `end`: date, place or link

**Craft:**
- Very short scenes (2–3 s); energy comes from the cuts.
- Glitch and flash are spice: use them on 2–3 key cuts, `cut` everywhere else (set `transition` per scene).
- Chrome titles look best with 2–4 words.

**Avoid:**
- long reading text; glitching body copy
- flashing faster than 3 times a second (photosensitivity)
