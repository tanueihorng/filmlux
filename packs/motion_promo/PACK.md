# Pack: motion_promo

**For:** launches, announcements, teasers, social clips. Bold, punchy, confident. Usually 20–60 s.

**Defaults:** theme `navy` (or `midnight`); music `upbeat` (or `cinematic` for a vision opener); voice optional (Ava −4 %); captions `narration` if voiced, else `none`.

**Beats** (the story; choose a scene type and a `layout` for each: `python studio.py scenes`):
1. **Hook**: 3 short lines
2. **Promise**: product name and what it does
3. **Features**: 3–4, one each
4. **Proof**: real numbers or a real voice
5. **Before / after** (optional)
6. **CTA**

**Treatments** (offer the user 2–3 before writing the script; each is a different structure, not only a different look):
- **Launch reel**: fast, bold, big type and tiles.
  `kinetic` center → `title` giant → `bento` grid → `stat` giant → `compare` halves → `end` band
- **Product demo**: show it working: a chat and a marked-up screen.
  `countdown` → `chat` side → `annotate` over → `stat` left → `end` center
- **Teaser**: less is more: words, a reveal, a date.
  `wordwall` rows → `kinetic` stack → library `scenes/split_flap` → `end` left

**Signature scenes:** `countdown`, `chat`, library `scenes/split_flap`, `compare` layout `halves`. Use at least one; they make this pack look like itself.

**The original Shape** (still a valid treatment, the most conventional one):
1. `kinetic`: 3 short lines, the hook
2. `title`: product name and promise
3. `bento`: 3–4 features, one tile each
4. `stat` or `quote`: proof (real numbers only)
5. `compare`: before / after (optional)
6. `end`: CTA button

**Craft:**
- one idea per scene
- 3–8 word titles
- one `<em>` accent per title
- in `upbeat`, keep narration short (6–14 words) so the music breathes

**Avoid:**
- more than 6 bento tiles
- paragraphs on screen
- a stat without a source

See `examples/launch_teaser/` for a finished example of this pack.
