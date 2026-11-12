# Pack: cinematic_brand

**For:** vision films, brand moments, town-hall openers, and award or milestone celebrations. Emotional, slow and premium. 30–90 s.

**Defaults:**
- Theme `cinema` (letterbox, grain, light leaks, serif) or `warm`.
- Music `cinematic`.
- Voice Ava −8 % (calm) or Brian −6 %.
- Captions `narration`, or `none` if the words are already on screen.

**Beats** (the story; choose a scene type and a `layout` for each: `python studio.py scenes`):
1. **Feeling**: an opening line, no logo yet
2. **Moments**: 2–3 pictures of people or places
3. **Turn**: what changed
4. **Proof**: the one fact that matters
5. **Sting**: the brand, and a tagline

**Treatments** (offer the user 2–3 before writing the script; each is a different structure, not only a different look):
- **Letterbox**: wide pictures and huge type, one line per frame.
  `kinetic` center → `split` stacked ×2 → `section` center → `stat` giant → `logo`
- **Album**: the brand told through prints and a handwritten note.
  `quote` note → `polaroids` row → `title` photo → `bento` list → `logo`
- **Manifesto**: words carry the film; pictures flash between them.
  `wordwall` rows → `image` full → `kinetic` stack → `image` full → `end` band

**Signature scenes:** `wordwall`, `polaroids`, `title` layout `photo`, library `scenes/split_flap`. Use at least one; they make this pack look like itself.

**The original Shape** (still a valid treatment, the most conventional one):
1. `kinetic` or `quote`: an opening line that sets the feeling (no logo yet)
2. `image` (`full: true`) ×2–3: moments, each with a short title. Use the user's photos or AI images (see IMAGEGEN.md).
3. `section`: the turn ("02 · What we built")
4. `stat` or `bento`: the proof
5. `logo`: the brand sting, with a tagline
6. `end` (optional): CTA

**Craft:**
- Go slower: 6–8 s per scene, narration with pauses (commas), fewer words on screen.
- Alternate `move` on images (`in`, `left`, `out`, `right`) so the motion never repeats.
- Use `transition_s: 0.8` for long dissolves between images.
- Serif titles look best when short and in sentence case.

**Avoid:**
- bullets and dense charts
- fast cuts and upbeat music
- more than one accent word per title
