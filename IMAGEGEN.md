# IMAGEGEN.md: optional AI-generated images

Use this when the user has words but no visuals. Your coding agent can draw illustrations if it has an image tool; if not, the user can make them in any image app. The studio never calls an image service itself. It tells you exactly what to generate and where to save it, then animates the result like any other image (Ken Burns, parallax, split layouts, captions, QA).

**Only if the user says yes.** Intake question 9 asks this. Without a yes, use the user's own images, screenshots or the studio's graphic scenes (title, bento, chart, process, timeline…). Those are often better anyway.

## 1. Mark the scenes

Give any `image` or `split` scene a `gen` field next to its `src`:

```json
{"type": "image", "src": "assets/gen/01_hook.png", "full": true, "move": "in",
 "gen": {"prompt": "a lighthouse on a calm sea at dawn, lighthouse on the right third, open sky on the left"},
 "title": "Guiding every <em>conversation</em>", "say": "..."}
```

| `gen` field | Meaning |
|---|---|
| `prompt` | What to draw: the subject, composition and mood. **Not** the style; the theme adds that |
| `style` | Optional override of the theme's `imagegen` style (keep one style per film) |
| `aspect` | Optional: `16:9`, `9:16`, `1:1`, `4:5`. Defaults to the project format (`split` scenes use their `ratio`) |
| `cutout` | `true` for a subject on a transparent background (a parallax foreground layer) |

`gen` can also be a plain string (it is used as the prompt).

**Parallax:** an `image` scene with `layers` stacks a background and one or more cutouts, which move at different speeds:

```json
{"type": "image", "full": true, "move": "left", "title": "The moment it <em>clicks</em>",
 "layers": [{"src": "assets/gen/04_bg.png", "gen": {"prompt": "a wide empty office at golden hour"}, "depth": 0},
            {"src": "assets/gen/04_fg.png", "gen": {"prompt": "a glowing paper plane, centred", "cutout": true}, "depth": 1}]}
```

Until a file exists, `stills` shows a striped **AI IMAGE PENDING** card with the prompt. The user can approve the layout before anything is generated. `qa` reports each pending image as an ERROR, so a final render can't go out with placeholders.

## 2. Write the requests

```
python studio.py imagegen <name>
```

This writes `projects/<name>/assets/gen/REQUESTS.md` (and `requests.json`). Each image gets:
- the **full prompt**: your text, plus the theme's style, plus safety rules (no text, logos, real people or faces)
- the **size**, matching the project format (for example 1920×1080 for 16:9)
- the **save path**

## 3. Generate (any agent, any image tool)

Pick whichever route your setup has:

| Your setup | How to generate |
|---|---|
| The agent has a built-in image tool (for example Codex's `image_gen`, used by its `$imagegen` skill) | Generate each image with it |
| The agent has an image MCP server or extension installed (Claude Code, Gemini CLI, Cursor and others support these) | Call that tool with the prompt and size |
| No image tool | Hand `REQUESTS.md` to the user: they paste each prompt into any image app they are allowed to use (ChatGPT, Gemini, Copilot, Firefly, Midjourney…) and save the result to its save path, or drop it in `inbox/` for you to move |

For each image marked TO DO:
1. Use the prompt **exactly as written**. Request the size shown, or the nearest supported size with the same aspect ratio. (Sizes up to about 2K are reliable; don't ask for 4K.)
2. **Save or copy each image to its save path** in the project. (Many tools save to their own folder first.)
3. For `cutout: yes`: the prompt asks for a flat `#00ff00` green background, because most image models can't make transparency reliably. Remove it with the studio's own helper:
   ```
   python studio.py cutout <downloaded.png> projects/<name>/assets/gen/04_fg.png
   ```
4. Generate each image once, and regenerate only those the user rejects. Image generation is slow and costs more than text.

## 4. Check, look, then use

```
python studio.py imagegen <name> --check
```

The check reports missing or broken files, the wrong aspect ratio (the image would be cropped), files too small for full screen, and cutouts without transparency. It also logs each prompt in `assets/gen/provenance.json`.

Then **open every image and look at it**. Reject and regenerate if you see:
- any text or letters (models misspell them)
- extra limbs or broken hands
- a logo-like mark
- a real-looking person
- a different style from the other images
- a subject that collides with where the title sits

Then run `stills` → `qa` → `render` as usual.

## Rules

1. **Illustrations, not evidence.** Never generate anything that could pass for a real photo of a real event, a real product screen, a real customer or a real person. Product UI must come from real screenshots or screen recordings.
2. **No text in images.** Put words in the scene (`title`, `body`). That keeps them crisp, translatable and spelled right.
3. **One style per film.** Keep the theme's `imagegen` style. Describe the same character or prop identically in every prompt so it stays consistent.
4. **No logos or brand marks** in generated images; the real logo comes from the theme.
5. **Say it is AI.** Tell the user which images are AI-generated (provenance.json lists them). If their organisation requires a label, add one in the end card `sub`.
6. **The user's files win.** If the user has a real photo or screenshot for a scene, use it instead of generating one.
7. **Prompts are sent to the image service.** Keep confidential names, numbers and customer details out of prompts.

## No image tool at all?

Any image source works: the user's photos, stock they licensed, or images made in another tool and saved to the same paths. `--check` and the placeholders behave the same.
