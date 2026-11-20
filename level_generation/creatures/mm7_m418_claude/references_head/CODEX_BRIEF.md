# Codex brief: HD head turnaround for the MM7 Troglodyte (m418)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m418_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Purpose: a 1K head texture set from a head-only retexture (front, three-quarter, profile, back), and, if the body
model's head shape is wrong, a head-only model (the three-quarter view is the single-image 3D modelling input).

Use your built-in image generation, with the record format of
`level_generation/creatures/mm6_ske_claude/references_hd/generation_runs.json`. Attached inputs, in order (paths
relative to `level_generation/creatures/`):
1. `mm7_m418_claude/references_hd/00_three_quarter.png` — the SELECTED HD body master: hood, maw, teeth
   and pattern authority. Only its head matters here.
2. `mm7_m418/native/m418sa0.png` — ORIGINAL native front (maw, teeth, blue rim).
3. `mm7_m418/native/m418sa2.png` — ORIGINAL native right profile (hood shape, spines).

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

Use case: identity-preserve. Asset: an isolated HD HOOD-HEAD for the existing MM7 Troglodyte monster, a texture and
modelling reference, not a new design. The EXACT SAME head as input 1, shown alone: the large rounded armoured hood
with its pointed dorsal spines, the narrow cyan-blue lower rim and the wide maw full of ivory pointed teeth (upper
and lower rows, dark mouth inside), the vivid cyan-blue stripes and purple mottling on olive scales, cut cleanly behind
the hood where it meets the back and below the jaw at the throat (no arms, no body). No eyes. The head is centred and
level and fills about 75% of the frame, generous transparent margins, near-orthographic camera.

Even soft neutral studio illumination, no dramatic shadows, no rim light. No floor, cast shadow, glow halo,
background gradient, checkerboard drawn into the image, scene or text. Do not change the colours or the blue pattern.

Checks per image: 1024 x 1024; true transparency; only the hood-head; whole hood and spines in the frame; maw with
teeth, blue rim and stripes, no eyes; same head as input 1; side views facing the stated direction.
