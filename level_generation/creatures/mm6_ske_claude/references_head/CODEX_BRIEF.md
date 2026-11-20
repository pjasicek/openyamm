# Codex brief: HD skull turnaround for the MM6 Skeleton (ske)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_ske_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Purpose: the body model came back with a human-looking face instead of a skull. These images are used to model a
SKULL-ONLY replacement (the three-quarter view is the single-image 3D modelling input) and later to texture it.

Use your built-in image generation, with the record format of
`level_generation/creatures/mm6_ske_claude/references_hd/generation_runs.json`. Attached inputs, in order (paths
relative to `level_generation/creatures/`):
1. `mm6_ske_claude/references_hd/01_front.png` — the SELECTED HD front body master: skull identity, bone colour and
   red eye glow authority.
2. `mm6_ske_claude/references_hd/00_three_quarter.png` — the selected three-quarter body master.
3. `mm6_ske_claude/references_hd/03_left.png` — the selected profile body master (skull profile, jaw, teeth).
4. `mm6_ske_claude/references_hd/02_back.png` — the selected back master (back of the skull).

## Deliverables (5 images, 1024 x 1024 SQUARE, true transparent background, unresized returns)

| File | View |
|---|---|
| `00_three_quarter.png` | front-right three-quarter (camera 40–45 degrees toward the skull's own RIGHT side), slightly above eye level; primary, generate first |
| `01_front.png` | exact straight-on front |
| `02_left.png` | the skull's own LEFT side, pure profile: it faces IMAGE LEFT |
| `03_back.png` | straight from behind |
| `04_right.png` | the skull's own RIGHT side, pure profile: it faces IMAGE RIGHT |

Generate 01–04 with the selected 00 as an additional input so all five show the SAME skull. Accept a view as soon as
it passes the checks; at most ONE targeted corrective regeneration per view. Write `generation_runs.json` and a
`selected_views_review.png` contact sheet; keep raw returns under `raw/`.

## Prompt content (adapt per view)

Use case: identity-preserve. Asset: an isolated HD SKULL for the existing MM6 Skeleton monster, a 3D modelling and
texture reference, not a new design. The EXACT SAME skull as the selected body masters, shown alone: ONE COMPLETE
HUMAN SKULL WITH ITS LOWER JAW (mandible) attached and closed, NO neck vertebrae, no spine, no collarbones, nothing
else. The skull is centred and level and fills about 75% of the frame height, generous transparent margins,
near-orthographic camera.

Identity (must match the body masters): an anatomically correct adult human skull, smooth rounded cranium, clear brow
ridges, two large deep round EYE SOCKETS (orbits) that are hollow and dark inside, with one small bright glowing RED
point deep in the centre of each socket; a dark open triangular/pear-shaped NASAL CAVITY with no nose; prominent
cheekbones (zygomatic arches) running back to the ear openings; a full row of separate upper teeth and a full row of
separate lower teeth meeting in a slight grin, no lips, no gums covering them; the lower jaw with its angle and its
rising branch up to just in front of the ear opening. Clean smooth dry bone in the SAME warm ivory/cream colour as the
masters, soft grey shading in the sutures, sockets and crevices, small darker pores. Sharp fine detail: cranial
sutures, tooth edges, socket rims.

NOT A FACE: no skin, no flesh, no eyelids, no eyeballs, no nose, no lips, no ears, no hair, no expression lines.

Even soft neutral studio illumination, no dramatic shadows, no rim light. No floor, cast shadow, glow halo, background
gradient, checkerboard drawn into the image, scene or text. Do not change the bone colour.

Checks per image: 1024 x 1024; true transparency; only the skull and its closed lower jaw (no neck); whole skull in
the frame; hollow eye sockets with red points, open nasal cavity, separate teeth, no flesh or eyeballs; same skull as
the body masters; side views facing the stated direction.
