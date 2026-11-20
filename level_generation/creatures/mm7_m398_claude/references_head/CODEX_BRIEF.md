# Codex brief: HD helmeted-skull turnaround for the MM7 Skeleton Warrior (m398)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m398_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Purpose: the body model came back with a flat human-looking face and a loose chin instead of a skull. These images
are used to model a HEAD-ONLY replacement (the three-quarter view is the single-image 3D modelling input) and later to
texture it (front, three-quarter, profile, back).

Use your built-in image generation, with the record format of
`level_generation/creatures/mm6_ske_claude/references_hd/generation_runs.json`. Attached inputs, in order (paths
relative to `level_generation/creatures/`):
1. `mm7_m398_claude/references_hd/00_three_quarter.png` — the SELECTED HD body master: skull, helmet, bone colour
   and stain authority. Only its head matters here.
2. `mm7_m398/native/m398sa0.png` — ORIGINAL native front (skull with hollow dark sockets, teeth, spiked cap).
3. `mm7_m398/native/m398sa2.png` — ORIGINAL native right profile (skull profile, jaw, helmet spike).

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

Use case: identity-preserve. Asset: an isolated HD HEAD for the existing MM7 Skeleton Warrior monster, a 3D modelling
and texture reference, not a new design. The EXACT SAME helmeted skull as input 1, shown alone: ONE COMPLETE HUMAN
SKULL WITH ITS LOWER JAW (mandible) attached and closed, wearing the small rounded dark steel skull-cap HELMET with
its polished brass band around the rim and one short thin spike on top. NO neck vertebrae, no spine, no collar, no
armour, nothing else. The head is centred and level and fills about 75% of the frame height, generous transparent
margins, near-orthographic camera.

Identity (must match input 1): an anatomically correct adult human skull: clear brow ridges under the helmet rim, two
large deep round EYE SOCKETS (orbits) that are HOLLOW and DARK inside (no eyeballs, no glow), a dark open
pear-shaped NASAL CAVITY with no nose, prominent cheekbones (zygomatic arches) running back to the ear openings, a
full row of separate upper teeth and a full row of separate lower teeth meeting in a grin, no lips, no gums covering
them; the lower jaw with its angle and its rising branch up to just in front of the ear opening, firmly joined to the
skull. Aged ochre-ivory bone with rusty dark red stains as in input 1, soft grey shading in the sutures, sockets and
crevices. The helmet sits on the cranium down to just above the brows and the ear openings; the back of the skull
below the helmet rim is bare bone.

NOT A FACE: no skin, no flesh, no eyelids, no eyeballs, no nose, no lips, no ears, no hair.

Even soft neutral studio illumination, no dramatic shadows, no rim light. No floor, cast shadow, glow halo,
background gradient, checkerboard drawn into the image, scene or text. Do not change the bone or metal colour.

Checks per image: 1024 x 1024; true transparency; only the helmeted skull and its closed lower jaw (no neck); whole
head including the spike in the frame; hollow dark eye sockets, open nasal cavity, separate teeth, no flesh or
eyeballs; same head as input 1; side views facing the stated direction.
