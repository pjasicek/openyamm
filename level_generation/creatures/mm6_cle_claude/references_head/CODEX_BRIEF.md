# Codex brief: HD head turnaround for the MM6 Cleric (cle)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_cle_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation, with the record format of
`level_generation/creatures/mm6_cle_claude/references_hd/generation_runs.json`. Attached inputs, in order:
1. `level_generation/creatures/mm6_cle_claude/references_hd/01_front.png` — the SELECTED HD front body master:
   exact face and hair identity authority.
2. `level_generation/creatures/mm6_cle_claude/references_hd/00_three_quarter.png` — the selected three-quarter master.
3. `level_generation/creatures/mm6_cle_claude/references_hd/02_back.png` — the selected back master: back of the hair.

## Deliverables (5 images, 1024 x 1024 SQUARE, true transparent background, unresized returns)

| File | View |
|---|---|
| `00_front.png` | exact straight-on front (primary; generate first) |
| `01_three_quarter.png` | front-right three-quarter (camera 45 degrees toward his right) |
| `02_left.png` | his own LEFT side, pure profile: he faces IMAGE LEFT |
| `03_back.png` | straight from behind |
| `04_right.png` | his own RIGHT side, pure profile: he faces IMAGE RIGHT |

Generate 01–04 with 00 as an additional input so all five show the SAME head. Accept a view as soon as it passes the
checks; at most ONE targeted corrective regeneration per view. Write `generation_runs.json` and a
`selected_views_review.png` contact sheet; keep raw returns under `raw/`.

## Prompt content (adapt per view)

Use case: identity-preserve. Asset: head texture reference turnaround for the existing MM6 Cleric of Baa, not a new
design. The EXACT SAME head as the selected body masters, isolated: ONE HEAD AND NECK ONLY, like a sculpted bust
WITHOUT the collar, shoulders, mantle or chest: the bare neck ends in a clean straight HORIZONTAL cut a little below
the chin. Head centred and level; from the top of the hair to the cut fills about 80% of the frame height, generous
transparent margins, near-orthographic camera at eye height. Do not crop the hair.

Identity (must match the body masters exactly): adult fair-skinned man, clean-shaven narrow long face, straight nose,
calm plain expression, eyes with visible irises, natural eyebrows; light brown / dark-blond slightly wavy hair parted
in the middle, falling to the jaw at the sides and to the nape at the back, ears partly covered. Sharp fine detail:
skin, eyes, eyebrows, lips and hair strands. No beard, no moustache, no stubble.

Even soft neutral studio illumination, no dramatic shadows, no rim light. No floor, cast shadow, glow, background
gradient, checkerboard drawn into the image, scene or text. No collar, mantle, clothing or jewellery. Do not change
colours.

Checks per image: 1024 x 1024; true transparency; only the head and neck with a straight horizontal cut below the
chin; whole hair inside the frame; same face and hair as the body masters; side views facing the stated direction.
