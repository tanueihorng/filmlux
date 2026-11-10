# Script and storyboard: Orbit 2.0 launch teaser

> **Worked example (creative mode): one good way, not the template.** It shows the thinking behind `project.json` in this folder: the outline, the look options offered to the user, the script, the scorecard and the defaults broken on purpose.

## 1. Outline (the story in one breath)

Scattered notes → one shared plan → what's inside → how the team works with it → what changes → open it.

It follows the viewer's gap from the brief: they think Orbit is "just boards". So the film opens on the pain they recognise, shows the four tools as one, and ends on a single action.

**The moment to remember:** the weekly loop drawing itself (scene 4). It turns "four tools" into "how my team actually works".

## 2. Look options (offered to the user with the script)

| | Theme + motion + captions | Why it fits | Risk |
|---|---|---|---|
| **A (chosen)** | `navy`, the theme's smooth motion, glass captions | Calm and confident; reads as a product launch on a big screen and in Teams | Safe: needs a strong hero moment so it isn't generic (hence the drawn loop) |
| B | `aurora`, `spring` motion, glass captions | Friendlier, "the assistant writes for you" feel | Can look playful for a town hall opener |
| C | `brutal`, `slam` motion, `cut` transitions, bar captions | Loud and memorable; good for a teaser on social | Too loud for the town hall screen |

The user picked A for the town hall. Option C would be the social cut-down.

## 3. Script

| # | Scene type | On screen | Narration (`say`) | Visual notes | ~s |
|---|---|---|---|---|---|
| 1 | title | Orbit · Version 2.0 / From scattered notes to a *shared plan* | "Introducing Orbit, version two. From scattered notes, to a shared plan." | The viewer's pain and the promise in one line | 6 |
| 2 | kinetic | See every project. / Share every update. / *Ship* together. | "See every project. Share every update. And ship together." | Three beats, one per line, rhythm over information | 6 |
| 3 | bento | Four tools, *one workspace*: Boards (hero tile), Assistant, Updates, Inbox | "Four tools work as one: boards, the assistant, updates and the inbox." | Boards is the 2×2 hero because users already know it | 6.5 |
| 4 | process (loop) | Plan → Assign → Build → Review → Share → Learn | "Together, they follow the team's weekly loop, from planning the work to learning from every release." | **Hero moment:** the loop draws itself | 7.5 |
| 5 | compare | Before / With Orbit, three items each | "No more scattered documents and lost comments. Just one view, automatic updates, and every comment tracked." | Mirrors the three key messages | 8.5 |
| 6 | end | See it in *Orbit* / Version 2.0 · available now / [Open Orbit] | "Orbit. Plan together, ship together." | One action only | 5 |

**Total:** 39.5 s (from `python studio.py plan`). **Music:** corporate, −27 dB. **Voice:** Ava −4 %. **Captions:** narration, glass.

## 4. Scorecard (PLAYBOOK.md §7)

| # | Check | Result |
|---|---|---|
| 1 | Knows what it's about in 5 s | ✅ Scene 1 names the product, the version and the promise |
| 2 | Follows on mute | ✅ Stills plus captions tell the whole story |
| 3 | Reads every word in time | ✅ One WARN kept on purpose (below) |
| 4 | One main thing per scene | ✅ |
| 5 | No sloppy frames | ✅ Contact sheet checked |
| 6 | Voice and music suit the purpose | ✅ |
| 7 | Trusts it | ✅ No numbers claimed, nothing invented |
| 8 | Remembers one moment | ✅ The weekly loop drawing itself |
| 9 | Knows what to do next | ✅ "Open Orbit" |
| 10 | Doesn't feel like a template | ✅ The loop scene ties the features to the team's own routine |

## 5. Defaults broken on purpose

This project uses `"mode": "creative"`, so `qa` warnings are advice. In guided mode the warning below would block the render until the bento text was cut.

- **`qa` warns that the bento has 33 words on screen for 6.5 s.** Kept: a bento is scanned, not read, the narration names the four tools, and the small body text on the hero tile is supporting detail. A stricter cut would drop that line.
