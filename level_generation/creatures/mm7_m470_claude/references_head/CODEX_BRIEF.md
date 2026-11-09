# Codex brief: HD head turnaround for the MM7 Ghoul (m470)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m470_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Purpose: a 1K head texture set from a head-only retexture (front, three-quarter, profile, back), and, if the body
model's head shape is wrong, a head-only model (the three-quarter view is the single-image 3D modelling input).

Use your built-in image generation, with the record format of
`level_generation/creatures/mm6_ske_claude/references_hd/generation_runs.json`. Attached inputs, in order (paths
relative to `level_generation/creatures/`):
1. `mm7_m470_claude/references_hd/00_three_quarter.png` — the SELECTED HD body master: face, skin and hair
   authority. Only its head matters here.
2. `mm7_m470/native/m470sa0.png` — ORIGINAL native front (grin, eyes, ears, hair).
3. `mm7_m470/native/m470sa2.png` — ORIGINAL native right profile (ears, mane).

## Deliverables (5 images, 1024 x 1024 SQUARE, true transparent background, unresized returns)

| File | View |
|---|---|
| `00_three_quarter.png` | front-right three-quarter (camera 40–45 degrees toward the head's own RIGHT side), slightly above eye level; primary, generate first |
| `01_front.png` | exact straight-on front |
| `02_left.png` | the head's own LEFT side, pure profile: it faces IMAGE LEFT |
| `03_back.png` | straight from behind |
| `04_right.png` | the head's own RIGHT side, pure profile: it faces IMAGE RIGHT |

Generate 01–04 with the selected 00 as an additional input so all five show the SAME head. Accept a view as soon as
it passes the checks; at most ONE targeted corrective regeneration per view. Write `generation_runs.json` and a
`selected_views_review.png` contact sheet; keep raw returns under `raw/`.

## Prompt content (adapt per view)

Use case: identity-preserve. Asset: an isolated HD HEAD AND NECK BUST for the existing MM7 Ghoul monster, a texture
and modelling reference, not a new design. The EXACT SAME head as input 1, shown alone, cut level just below the
throat (no shoulders, no clothes): pale ivory-grey skin, an angular gaunt face with a pointed chin and hollow cheeks,
a stern brow, small bright yellow-green eyes, a wide toothy grin, wide pointed ears sticking out to the sides, coarse
ash-blond hair swept upward at the front and falling as a narrow mane down the back of the neck (cut at the throat
line in this bust). The head is centred and level and fills about 75% of the frame height, generous transparent
margins, near-orthographic camera.

Even soft neutral studio illumination, no dramatic shadows, no rim light. No floor, cast shadow, glow halo,
background gradient, checkerboard drawn into the image, scene or text. Do not change the skin or hair colour.

Checks per image: 1024 x 1024; true transparency; only the head and neck; whole head, ears and hair in the frame;
yellow-green eyes, pale skin, blond hair, grin; same head as input 1; side views facing the stated direction.
