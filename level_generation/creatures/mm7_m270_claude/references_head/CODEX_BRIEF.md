# Codex brief: HD crowned-skull turnaround for the MM7 Lich (m270)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m270_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Purpose: a 1K head texture set from a head-only retexture (front, three-quarter, profile, back), and, if the body
model's skull comes back as a face, a head-only model (the three-quarter view is the single-image modelling input).

Use your built-in image generation, with the record format of
`level_generation/creatures/mm6_ske_claude/references_hd/generation_runs.json`. Attached inputs, in order (paths
relative to `level_generation/creatures/`):
1. `mm7_m270_claude/references_hd/00_three_quarter.png` — the SELECTED HD body master: skull, crown, coif and bone
   colour authority. Only its head matters here.
2. `mm7_m270/native/m270sa0.png` — ORIGINAL native front (skull, crown, coif).
3. `mm7_m270/native/m270sa2.png` — ORIGINAL native right profile (coif and crown profile).

## Deliverables (5 images, 1024 x 1024 SQUARE, true transparent background, unresized returns)

| File | View |
|---|---|
| `00_three_quarter.png` | front-right three-quarter (camera 40–45 degrees toward the skull's own RIGHT side), slightly above eye level; primary, generate first |
| `01_front.png` | exact straight-on front |
| `02_left.png` | the skull's own LEFT side, pure profile: it faces IMAGE LEFT |
| `03_back.png` | straight from behind |
| `04_right.png` | the skull's own RIGHT side, pure profile: it faces IMAGE RIGHT |

Generate 01–04 with the selected 00 as an additional input so all five show the SAME head. Accept a view as soon as
it passes the checks; at most ONE targeted corrective regeneration per view. Write `generation_runs.json` and a
`selected_views_review.png` contact sheet; keep raw returns under `raw/`.

## Prompt content (adapt per view)

Use case: identity-preserve. Asset: an isolated HD HEAD for the existing MM7 Lich monster, a texture and 3D modelling
reference, not a new design. The EXACT SAME head as input 1, shown alone and cut level at the bottom of the coif: a
bare ivory-grey human SKULL (empty dark eye sockets, dark nasal opening, full rows of teeth, closed lower jaw) wearing a
gold pointed open CROWN of tall points, inside a dark blue-violet grey CHAINMAIL COIF of distinct fine rings that
covers the top, sides and back of the head and the neck and frames the open skull face. No shoulders, no armour. The
head is centred and level and fills about 75% of the frame height, generous transparent margins, near-orthographic
camera.

NOT A FACE: no skin, no flesh, no eyelids, no eyeballs, no nose, no lips, no hair.

Even soft neutral studio illumination, no dramatic shadows, no rim light. No floor, cast shadow, glow halo,
background gradient, checkerboard drawn into the image, scene or text. Do not change the bone, chain or gold colours.

Checks per image: 1024 x 1024; true transparency; only the crowned skull in its coif (no shoulders); whole crown in
the frame; dark sockets, teeth, no flesh; same head as input 1; side views facing the stated direction.
