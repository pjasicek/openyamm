# Codex brief: HD head turnaround for the MM7 Wight (m430)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m430_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Purpose: a 1K head texture set from a head-only retexture (front, three-quarter, profile, back), and, if the body
model's head shape is wrong, a head-only model (the three-quarter view is the single-image 3D modelling input).

Use your built-in image generation, with the record format of
`level_generation/creatures/mm6_ske_claude/references_hd/generation_runs.json`. Attached inputs, in order (paths
relative to `level_generation/creatures/`):
1. `mm7_m430_claude/references_hd/00_three_quarter.png` — the SELECTED HD body master: face, skin and hair
   authority. Only its head matters here.
2. `mm7_m430/native/m430sa0.png` — ORIGINAL native front (gaunt face, black sockets, hair).
3. `mm7_m430/native/m430sa2.png` — ORIGINAL native right profile (head shape, hair fall).

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

Use case: identity-preserve. Asset: an isolated HD HEAD AND NECK BUST for the existing MM7 Wight monster, a texture
and 3D modelling reference, not a new design. The EXACT SAME head as input 1, shown alone, cut level just below the
throat (no robe, no shoulders): a small gaunt skull-like face with pale desaturated grey-green skin stretched over the
bone, bald high forehead, deep BLACK empty eye sockets, narrow nose, sunken cheeks, thin closed lipless mouth with a
hint of teeth, small ears; long straight thin silver-grey hair hanging from the sides and back of the otherwise bald
head, cut at the throat line in this bust. The head is centred and level and fills about 75% of the frame height,
generous transparent margins, near-orthographic camera.

Even soft neutral studio illumination, no dramatic shadows, no rim light. No floor, cast shadow, glow halo,
background gradient, checkerboard drawn into the image, scene or text. Do not change the skin or hair colour.

Checks per image: 1024 x 1024; true transparency; only the head and neck (no robe); whole head and hair in the frame;
black sockets, grey-green skin, silver hair; same head as input 1; side views facing the stated direction.
