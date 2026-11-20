# Codex brief: HD head turnaround for the MM7 Zombie (m438)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m438_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Purpose: a 1K head texture set from a head-only retexture (front, three-quarter, profiles, back).

Use your built-in image generation, with the record format of
`level_generation/creatures/mm7_m438_claude/references_hd/generation_runs.json`. Attached inputs, in order (paths
relative to `level_generation/creatures/`):
1. `mm7_m438_claude/references_hd/01_front.png` — the SELECTED HD body master front: face, skin, hair and headband
   authority. Only its head matters here.
2. `mm7_m438_claude/references_hd/02_back.png` — the selected HD back (headband knot, back of the head).
3. `mm7_m438_claude/references_hd/04_right.png` — the selected HD right profile (ear, headband).
4. `mm7_m438/native/m438sa0.png` — ORIGINAL native front.

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

Refusals (user decision 2026-10-20): if the image service refuses a view, retry that view with these benign
variants in order, one attempt each, and record every attempt and refusal text: R1 "a stylised fantasy-game undead
man's head with weathered grey-green skin and a few small dark reddish-brown stains"; R2 as R1 plus "clean painted
video-game character art, no blood, no wounds". If both are refused for a view, stop and record it.

## Prompt content (adapt per view)

Use case: identity-preserve. Asset: an isolated HD HEAD AND NECK BUST for the existing MM7 Zombie monster, a texture
and modelling reference, not a new design. The EXACT SAME head as input 1, shown alone, cut level just below the
throat (no shoulders): gray-green weathered skin, a narrow gaunt face with hollow cheeks, sunken dark eye sockets with
small pale reddish eyes, a thin grim mouth, prominent ears, short dark cropped hair, a narrow olive-brown cloth
headband around the forehead tied at the back. The head is centred and level and fills about 75% of the frame
height, generous transparent margins, near-orthographic camera.

Even soft neutral studio illumination, no dramatic shadows, no rim light. No floor, cast shadow, glow halo,
background gradient, checkerboard drawn into the image, scene or text. Do not change the skin, hair or headband
colour. No added wounds or blood.

Checks per image: 1024 x 1024; true transparency; only the head and neck; whole head, ears and headband in the
frame; gray-green skin, cropped dark hair, olive headband; same head as input 1; side views facing the stated
direction.
