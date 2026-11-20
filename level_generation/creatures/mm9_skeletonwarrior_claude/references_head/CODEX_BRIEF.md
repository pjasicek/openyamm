# Codex brief: skull and helmeted head views for the MM9 Skeleton Master (mm9_skeletonwarrior_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_skeletonwarrior_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool, with the record
format of `references_hd/generation_runs.json`.

Purpose: the body model came back with a human-looking face instead of a skull. `skull_three_quarter.png` is the
single-image 3D modelling input for a SKULL-ONLY replacement. The four `bust_*` views texture the whole head (helmet and
skull) later.

## Inputs (attached, in order; paths relative to the project)
1. `references_hd/01_front.png` — SELECTED HD front master: skull, helmet and colour authority.
2. `references_hd/00_three_quarter.png` — selected three-quarter master.
3. `references_hd/03_left.png` — selected left profile (head faces IMAGE LEFT).
4. `references_hd/02_back.png` — selected back master.
5. `references_hd/mm9_head_views.png` — close renders of the ORIGINAL MM9 model's head: design authority only; its
   faceting and blur are not the design.

## Deliverables (1254x1254 square, true transparent background, unresized returns)
| File | View |
|---|---|
| `skull_three_quarter.png` | a BARE skull, no helmet: front-right three-quarter, camera 40-45 degrees toward the skull's own RIGHT, slightly above eye level. Generate first |
| `bust_front.png` | helmeted head and bare neck, cut just under the neck, straight front |
| `bust_left.png` | same, pure profile of its own LEFT side: faces IMAGE LEFT |
| `bust_back.png` | same, straight back |
| `bust_right.png` | same, pure profile of its own RIGHT side: faces IMAGE RIGHT |

Generate `skull_three_quarter.png`, then the `bust_*` views with inputs 1-5. At most ONE targeted corrective regeneration
per view. Write `generation_runs.json` and a `selected_views_review.png` contact sheet; keep raw returns under `raw/`.

## Skull (`skull_three_quarter.png`)
Asset: an isolated HD SKULL for the existing monster, a 3D modelling reference. The EXACT SAME skull as the selected
masters, shown alone: ONE COMPLETE HUMAN SKULL WITH ITS SEPARATE LOWER JAW, the mouth OPEN about 3 cm exactly as in the
masters, no neck vertebrae, no spine, no helmet, no insignia, nothing else. Centred and level, filling about 75 % of the
frame height, generous transparent margins, near-orthographic.

Identity: an anatomically correct adult human skull: smooth rounded cranium, heavy brow ridges, two large deep round EYE
SOCKETS that are hollow and dark inside (NO eyeballs, no glow: the eyes are modelled apart), a dark open pear-shaped
NASAL CAVITY with no nose, prominent cheekbones (zygomatic arches) running back to the ear openings, a full row of separate
upper teeth and a full row of separate lower teeth with a dark gap between them, no lips, no gums covering them; the lower
jaw with its chin, its angle and its rising branch up to just in front of the ear opening. Aged ivory-olive bone as the
masters, dark in the crevices, with cracks and pits. Soft even light, no dramatic shadow.

NOT A FACE: no skin, no flesh, no eyelids, no eyeballs, no nose, no lips, no ears, no hair, no expression lines.

## Bust views (`bust_*`)
The EXACT SAME helmeted head as the selected masters, enlarged: helmet with its three horn spikes, gold-beaded collars, brow
insignia, the long lamellar cheek and neck guards, the skull inside with its glowing red eyes and open mouth, the bare neck
vertebrae. Head level, filling about 80 % of the frame, nothing cropped. Near-orthographic, even soft light, true
transparent background, no shoulders, no cuirass, no text.

## Per-image checks
Skull: no helmet; open mouth with two rows of separate teeth; hollow sockets, no eyes; nasal cavity; not a face.
Busts: three horns; same colours and plate pattern as the masters; correct side faces the correct image side (`bust_left`:
faces IMAGE LEFT; `bust_right`: faces IMAGE RIGHT); nothing cropped; 1254x1254; true alpha.
