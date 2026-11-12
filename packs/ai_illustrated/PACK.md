# Pack: ai_illustrated

**For:** explainers and stories where you have words but no visuals: concepts, change stories, onboarding, "a day in the life". The coding agent can generate consistent illustrations with its image tool (optional; see IMAGEGEN.md). 45–90 s.

**Defaults:**
- Theme `warm` (illustrated, human), `aurora` (3D glass) or `navy`.
- Music `calm`. Voice Emma or Ava −4 %.
- Captions `narration`.

**Beats** (the story; choose a scene type and a `layout` for each: `python studio.py scenes`):
1. **Hook**: one striking picture and a 3–6 word line
2. **Unfold**: 2–3 ideas, each with its own illustration
3. **Hero moment**: a parallax or full-bleed picture
4. **Takeaway**: the point, built from type or a diagram, not another picture
5. **Ask**: what to do next

**Treatments** (offer the user 2–3 before writing the script; each is a different structure, not only a different look):
- **Picture book**: every beat is an illustration; the words sit on cards over them.
  `title` photo → `split` full ×2 (alternate `side`) → `image` with `layers` → `note` card → `end` left
- **Gallery wall**: illustrations as prints on a table, the story told between them.
  `image` polaroid → `polaroids` pile → `quote` huge → `split` polaroid → `end` center
- **Conversation**: an assistant explains, pictures answer.
  `kinetic` stack → `chat` side → `split` overlap → `annotate` over → `end` band

**Signature scenes:** `polaroids`, `chat`, `split` layouts `full` / `overlap`. Use at least one; they make this pack look like itself.

**The original Shape** (still a valid treatment, the most conventional one):
1. `image` (full) hook: one striking illustration and a 3–6 word title
2. `split` ×2–3: text on one side, an illustration on the other (alternate `side`)
3. `image` with `layers` (a background plus a cutout subject) for a parallax hero moment
4. `process` or `bullets`: the takeaway, built from scene graphics rather than an image
5. `end`

**How the images work:**
- Every image scene has `src` (where the file will be saved) and `gen` (what to draw). Until the file exists, previews show a striped "AI IMAGE PENDING" placeholder, and `qa` blocks the final render.
- `python studio.py imagegen <name>` writes `assets/gen/REQUESTS.md`: exact prompts (your text, plus the theme's style and safety rules), sizes and save paths. The agent generates the images, then runs `imagegen <name> --check`.
- Use one style for the whole film. Keep the theme's `imagegen` style, and describe only the subject and composition in each `gen` prompt.

**Craft:**
- Leave negative space where the title sits ("subject on the right third").
- Describe the same character or props identically in every prompt.
- 4–6 images is plenty.

**Avoid:**
- Text inside images. Models misspell, so put the words in the scene instead.
- Real people or faces, and logos.
- Anything that could be mistaken for a real photo of a real event.
