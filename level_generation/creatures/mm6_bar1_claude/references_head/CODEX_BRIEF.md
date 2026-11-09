# Codex brief: HD head turnaround for the MM6 Barbarian (bar1)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_bar1_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Attached inputs, in order (paths relative to `level_generation/creatures/`):
1. `mm6_bar1_claude/references_hd/01_front.png` - the SELECTED HD front body master: face, hair, circlet identity.
2. `mm6_bar1_claude/references_hd/00_three_quarter.png` - the selected three-quarter master.
3. `mm6_bar1_claude/references_hd/03_left.png` - the selected profile master (hair at the back, profile).

## Deliverables (5 images, 1024 x 1024 SQUARE, true transparent background, unresized returns)

| File | View |
|---|---|
| `00_front.png` | exact straight-on front (primary; generate first) |
| `01_three_quarter.png` | front-right three-quarter (camera 45 degrees toward her own right) |
| `02_left.png` | her own LEFT side, pure profile: she faces IMAGE LEFT |
| `03_back.png` | straight from behind (back of the head and hair) |
| `04_right.png` | her own RIGHT side, pure profile: she faces IMAGE RIGHT |

Generate 01-04 with 00 as an additional input so all five show the SAME head. At most ONE corrective regeneration
per view. Write `generation_runs.json` (record format of `../references_hd/generation_runs.json`) and a
`selected_views_review.png` contact sheet; keep raw returns under `raw/`.

## Prompt content (adapt per view)

Use case: identity-preserve. Asset: a portrait-bust texture reference turnaround for an existing fantasy game
character (a warrior woman), not a new design. The EXACT SAME head as the body masters, shown as a sculpted bust:
HEAD, HAIR AND NECK ONLY, cut with a clean straight HORIZONTAL line at the base of the neck, ABOVE the collarbones
(no shoulders, no armour, no chest). Head centred and level; top of the hair to the cut fills about 85% of the frame
height (the long hair may be cut by the same horizontal line), generous side margins, near-orthographic camera at
eye height.

Identity (must match the masters): adult woman with a strong, calm face, tanned skin, dark eyes, defined brows,
straight nose; long thick wavy auburn / dark red hair parted in the middle; a thin gold circlet with a small red gem
on the forehead; a thin gold choker with a small red gem at the neck. Neutral, calm expression, mouth closed.
Sharp fine detail: skin, eyes, brows, lips, hair strands, gold work.

Even soft neutral studio light, no dramatic shadows, no rim light. No background, floor, shadow, text, checkerboard
drawn into the image. Do not add jewellery, make-up changes, earrings, a helmet or clothing.

Checks: 1024 x 1024; true transparency; only head, hair and neck with a straight horizontal cut above the
collarbones; same face, hair, circlet and choker as the masters; side views facing the stated direction.
