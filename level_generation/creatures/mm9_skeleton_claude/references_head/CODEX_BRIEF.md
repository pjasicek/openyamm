# Codex brief: skull and head views for the MM9 Skeleton (mm9_skeleton_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_skeleton_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool, with the record
format of `references_hd/generation_runs.json`.

Purpose: `skull_three_quarter.png` is the single-image 3D modelling input for a SKULL-ONLY model (the body model's face is too
coarse). The four `bust_*` views texture the head later.

## Inputs (attached, in order; paths relative to the project)
1. `references_hd/01_front.png` — SELECTED HD front master: skull and colour authority.
2. `references_hd/00_three_quarter.png` — selected three-quarter master.
3. `references_hd/03_left.png` — selected left profile (head faces IMAGE LEFT).
4. `references_hd/02_back.png` — selected back master.
5. `references_hd/mm9_head_views_skel2.png` — close renders of the ORIGINAL MM9 model's head: design authority only; its
   faceting and blur are not the design. Its high, large cranium swelling backward IS the design.

## Deliverables (1254x1254 square, true transparent background, unresized returns)
| File | View |
|---|---|
| `skull_three_quarter.png` | a BARE skull: front-right three-quarter, camera 40-45 degrees toward the skull's own RIGHT, slightly above eye level. Generate first |
| `bust_front.png` | skull and bare neck vertebrae, cut just under the neck, straight front |
| `bust_left.png` | same, pure profile of its own LEFT side: faces IMAGE LEFT |
| `bust_back.png` | same, straight back |
| `bust_right.png` | same, pure profile of its own RIGHT side: faces IMAGE RIGHT |

Generate `skull_three_quarter.png`, then the `bust_*` views with inputs 1-5 and the selected skull. At most ONE targeted corrective
regeneration per view. Write `generation_runs.json` and a `selected_views_review.png` contact sheet; keep raw returns under `raw/`.

## Skull (`skull_three_quarter.png`)
Asset: an isolated HD SKULL for the existing monster, a 3D modelling reference. The EXACT SAME skull as the selected masters,
shown alone: ONE COMPLETE HUMAN SKULL WITH ITS SEPARATE LOWER JAW, the mouth OPEN about 3 cm exactly as in the masters, with a clear
gap of air between upper and lower teeth, no neck vertebrae, no spine, nothing else. Centred and level, filling about 75 % of the frame.
- A real human skull in anatomy (not a human face, not cartoon): brow ridges, deep round EMPTY eye sockets (both dark holes, no eyeball and no glow
  in this image, because the eyes are modelled separately), a triangular nasal hole, cheekbones and zygomatic arches, a real upper tooth row with separate
  teeth, a separate mandible with a chin and two rising rami hinged at the sides of the skull, a separate lower tooth row.
- The cranium is HIGH and LARGE, swelling upward and backward, about 1.3 times a normal skull's height above the brow, as in the masters and input 5.
- Material: aged ochre-ivory bone with fine cracks and pits, even soft neutral light, no drama, no cast shadows.
- Do NOT add a crack so deep it opens the bone; do NOT add a green eye, a helmet, hair, skin, a neck, a floor, a shadow or text.

## Busts (`bust_*.png`)
The same head as the selected skull, in the colour and wear of the masters: ochre-ivory bone with a brownish patina, darker in the cracks. The figure's RIGHT
eye socket holds a glowing GREEN eye; the figure's LEFT socket is an empty dark hole with a crack from the brow through the socket to the cheek. One small gold
upper tooth and one gold lower tooth. Bare neck vertebrae below, cut just under the neck. Near-orthographic, level, the head centred at the same size in all four views, even neutral light,
true transparent background, no shadow, no text. In `bust_left.png` the head faces IMAGE LEFT, and it shows the cracked empty socket; in `bust_right.png` it faces IMAGE RIGHT and shows the green eye.
In `bust_front.png` the green eye is on IMAGE LEFT (the figure's right).

## Per-image checks
High domed cranium; real skull anatomy; open mouth with an air gap; separate mandible; correct side for the green eye and for the cracked socket; complete head inside the frame with margins; true alpha; 1254x1254.
