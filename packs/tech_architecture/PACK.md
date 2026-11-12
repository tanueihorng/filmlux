# Pack: tech_architecture

**For:** how a system works: architecture walkthroughs, platform explainers, data flows, design reviews and engineering onboarding. 60–120 s.

**Defaults:**
- Theme `blueprint` (technical drawing), `terminal` (developer) or `midnight`.
- Motion `typewriter` or `mask`. Transition `wipe`.
- Music `minimal` or `none`. Voice Andrew or Brian −6 %. Captions `bar`.

**Beats** (the story; choose a scene type and a `layout` for each: `python studio.py scenes`):
1. **The system in one line**
2. **Problem vs with the system**
3. **The diagram**
4. **Data flow**: 4–6 steps, one verb each
5. **Building blocks**
6. **Rollout**
7. **Where to learn more**

**Treatments** (offer the user 2–3 before writing the script; each is a different structure, not only a different look):
- **Blueprint**: the diagram leads; every part is marked and explained.
  `title` left → `compare` halves → `annotate` side on the diagram → `process` → `bento` list → `timeline` steps → `end` left
- **Request trace**: follow one request through the system.
  `chat` side (the question) → `process` → `annotate` over ×2 → `stat` left → `end` center
- **Field notes**: an engineer's notebook: decisions and trade-offs.
  `note` card → `split` stacked → `compare` cards → `bullets` big → `timeline` vertical → `end` band

**Signature scenes:** `annotate`, `chat`, `compare` layout `halves`, `timeline` layout `steps`. Use at least one; they make this pack look like itself.

**The original Shape** (still a valid treatment, the most conventional one):
1. `title`: the system in one line ("How the context engine <em>remembers</em>")
2. `compare`: the problem today vs with the system
3. `split` or `image`: the user's architecture diagram (zoom with `move: "in"`)
4. `process`: the data flow, 4–6 steps (one verb each: Capture, Resolve, Govern, Serve)
5. `bento`: the building blocks, one tile each
6. `timeline`: rollout or roadmap
7. `end`: where to learn more

**Craft:**
- Use the user's own diagram for the overview, then rebuild the important part as a `process` or `bento` so it reads on screen.
- One concept per scene; name components exactly as the user's documents do.
- Code or API names go in mono eyebrows; keep titles plain English.

**Avoid:**
- full-resolution diagrams with tiny labels shown for 3 seconds: crop, zoom or rebuild them
- inventing components, numbers or timelines the documents don't contain
