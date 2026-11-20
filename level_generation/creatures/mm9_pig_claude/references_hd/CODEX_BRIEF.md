# Codex brief: HD reference views for the MM9 Pig (mm9_pig_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_pig_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_crow_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_pig.png` — renders of the ORIGINAL MM9 low-poly pig with its original skin, five views
   left to right: front three-quarter from the pig's RIGHT (snout toward image right), front, the pig's LEFT side
   (snout points to IMAGE LEFT), back, the pig's RIGHT side (snout points to IMAGE RIGHT). Flat grey is background,
   not creature. This is the design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low
   resolution are NOT the design.
2. `references_hd/mm9_skin_pig_x4.png` — the original 128x128 skin texture enlarged 4x: SKIN MATERIAL AND COLOUR ONLY
   (pale pinkish-white skin, pink ears and snout, dark hooves). Never the design or shape.
3. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the pig's RIGHT, camera slightly above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front (snout toward the camera) | 1536x1024 |
| `02_back.png` | back (tail toward the camera) | 1536x1024 |
| `03_left.png` | the pig's LEFT side: snout points to IMAGE LEFT (as input 1 view 3) | 1536x1024 |
| `04_right.png` | the pig's RIGHT side: snout points to IMAGE RIGHT (as input 1 view 5) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME pig, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"Pig" creature from the supplied renders of its original 3D model, as a 3D modelling/texturing reference. Not a new
design. A beautifully detailed, credible, fully three-dimensional domestic farm pig with semi-realistic game materials
and sharp fine skin detail (fine sparse bristles, subtle skin creases), as if a high-quality sculpt of the original
model.

Identity: a pale pink-white domestic pig (like a Large White / Yorkshire), long straight body, straight back.
- Skin: pale pinkish-white with soft pink flush on the ears, snout, eyes and belly; fine short pale bristles. Clean,
  not muddy.
- Head: wedge-shaped head with a flat round pink snout disc with two nostrils at the front, the mouth CLOSED; small
  eyes with a pinkish rim; two pointed upright-forward ears that stick out sideways and forward as in input 1 (pink
  inside), thin flaps.
- Legs: four fairly slim straight legs, the front pair under the shoulders, the hind pair under the hips, each ending
  in a dark grey-brown cloven hoof flat on the ground.
- Tail: a short thin curly tail raised above the rump, curling once as in input 1.

Pose (exactly as input 1, the model's bind pose): standing square on all four legs, all four legs separate and
visible with air gaps between them, head level and slightly lowered, snout forward, tail clear of the body. Symmetric
left/right.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. The whole pig inside the frame with generous margins (never crop the snout, ears, tail or hooves), genuine
transparent background, no floor, no mud, no shadow, no text.

Do NOT: add mud, straw, a pen, a second pig, tusks, a collar, spots or patches, colours other than the pale
pinkish-white skin, pink ears/snout and dark hooves; do not open the mouth; do not crop.

## Per-image checks (re-run before selecting)
One pig; pale pink-white skin with no spots; closed mouth; flat snout disc with nostrils; two thin pointed ears out
to the sides; four separate legs with dark cloven hooves; short curly tail raised; the correct side faces the correct
image side (03: snout to image LEFT; 04: snout to image RIGHT); true transparent background; 1536x1024; nothing
cropped.
