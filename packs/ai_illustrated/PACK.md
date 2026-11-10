# Pack: ai_illustrated

**For:** explainers and stories where you have words but no visuals: concepts, change stories, onboarding, "a day in the life". The coding agent can generate consistent illustrations with its image tool (optional; see IMAGEGEN.md). 45–90 s.

**Defaults:**
- Theme `warm` (illustrated, human), `aurora` (3D glass) or `navy`.
- Music `calm`. Voice Emma or Ava −4 %.
- Captions `narration`.

**Shape (60 s):**
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
