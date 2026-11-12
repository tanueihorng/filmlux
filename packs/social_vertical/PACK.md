# Pack: social_vertical

**For:** phone-first clips (9:16): internal comms on mobile, Workplace/Teams stories, LinkedIn, event screens. 15–45 s, usually watched muted.

**Defaults:**
- Format `9:16`.
- Theme `neon` (bold), `aurora` (friendly) or `navy`.
- Caption style `pop`: big words, with the spoken word lit up.
- Music `upbeat`. Voice Ava −4 % or Andrew +0 %.

**Beats** (the story; choose a scene type and a `layout` for each: `python studio.py scenes`):
1. **Hook** in the first 2 seconds
2. **Why care**: one fact
3. **The points**: 3 items
4. **Proof or a face**
5. **One CTA**

**Treatments** (offer the user 2–3 before writing the script; each is a different structure, not only a different look):
- **Pop**: big words, one idea a screen.
  `kinetic` center → `stat` giant → `bullets` big → `quote` huge → `end` band
- **Chat screenshot**: the story told as a conversation.
  `kinetic` stack → `chat` center → `annotate` over → `end` center
- **Photo dump**: prints and notes, like a story post.
  `polaroids` pile → `note` sticky → `stat` left → `end` left

**Signature scenes:** `chat`, `countdown`, `polaroids`. Use at least one; they make this pack look like itself.

**The original Shape** (still a valid treatment, the most conventional one):
1. `kinetic`: the hook in the first 2 seconds (3 lines of 1–3 words)
2. `stat` or `section`: the one fact that makes people care
3. `bullets` (3 items) or `bento` (`cols: 2`, 3–4 tiles)
4. `quote` or `image`: proof, or a face of the change
5. `end`: one CTA

**Craft:**
- Hook first, logo last. Never open on a logo.
- Narration of 6–14 words per scene. Short sentences read best as pop captions.
- Make everything big: titles of 5 words or fewer, one idea per screen.
- Keep text out of the bottom quarter, where the pop captions sit. `qa` checks this.

**Avoid:**
- landscape screenshots shrunk into portrait (crop with `focus`, or use `split`)
- more than 5 scenes
- long caption lines
