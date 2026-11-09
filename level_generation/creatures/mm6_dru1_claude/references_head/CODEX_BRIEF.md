# Codex brief: HD head turnaround for the MM6 Druidess (dru1)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_dru1_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation, with the record format of
`level_generation/creatures/mm6_dru1_claude/references_hd/generation_runs.json`. Attached inputs, in order:
1. `level_generation/creatures/mm6_dru1_claude/references_hd/01_front.png` — the SELECTED HD front body master:
   exact face, hair, choker and hood identity authority.
2. `level_generation/creatures/mm6_dru1_claude/references_hd/00_three_quarter.png` — the selected three-quarter
   master: hood depth and the face inside it.
3. `level_generation/creatures/mm6_dru1_claude/references_hd/02_back.png` — the selected back master: back of the hood.

## Deliverables (5 images, 1024 x 1024 SQUARE, true transparent background with no haze, unresized returns)

| File | View |
|---|---|
| `00_front.png` | exact straight-on front (primary; generate first) |
| `01_three_quarter.png` | front-right three-quarter (camera 45 degrees toward HER OWN RIGHT side) |
| `02_left.png` | her own LEFT side, pure profile: she faces IMAGE LEFT |
| `03_back.png` | straight from behind |
| `04_right.png` | her own RIGHT side, pure profile: she faces IMAGE RIGHT |

Generate 01–04 with 00 as an additional input so all five show the SAME head. Accept a view as soon as it passes the
checks; at most ONE targeted corrective regeneration per view, then stop. Write `generation_runs.json` and a
`selected_views_review.png` contact sheet; keep raw returns under `raw/`.

## Prompt content (adapt per view)

Use case: identity-preserve. Asset: head texture reference turnaround for the existing MM6 Druidess, not a new
design. The EXACT SAME hooded head as the selected body masters, isolated: ONE HOODED HEAD, NECK AND HAIR ONLY, like a
sculpted bust: the hood, the long hair hanging inside it over the front of the shoulders, the neck with its thin gold
choker, ending in a clean straight HORIZONTAL cut at the level where the hair ends on the upper chest. No cloak body,
no arms, no bodysuit. Head centred and level; from the hood top to the cut fills about 85% of the frame height,
generous transparent margins, near-orthographic camera at eye height. Do not crop the hood.

Identity (must match the body masters exactly): slim adult woman, pale natural skin, stern serious face, dark
eyebrows, straight nose, full lips, eyes with visible irises; long thick wavy dark brown hair parted in the middle,
framing the face inside the hood and falling over the front of both shoulders; a thin gold choker on the neck. Deep
forest-green cloth hood, up, soft velvet-like cloth; the face fully visible in the opening. Sharp fine detail: skin,
eyes, eyebrows, lips, hair strands, cloth.

Even soft neutral studio illumination, no dramatic shadows, no rim light. No floor, cast shadow, glow, background
gradient, checkerboard drawn into the image, scene or text. Do not change colours.

Checks per image: 1024 x 1024; true transparency; only the hooded head, hair, neck and choker with a straight
horizontal cut at the hair ends; whole hood inside the frame; same face, hair and hood as the body masters; side
views facing the stated direction.
