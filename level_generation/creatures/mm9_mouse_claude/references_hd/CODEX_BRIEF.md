# Codex brief: HD reference views for the MM9 mouse (mm9_mouse_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_mouse_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_wolf_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9, and MM9 never shipped the mouse's skins (`mouse1.dtx`, `mouse3.dtx` are missing
from the game data). The authority is the ORIGINAL Might and Magic IX 3D mouse model, shown untextured in renders,
for POSE and PROPORTIONS only; the colours below are the design.

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly mouse (54 triangles, no texture, no
   legs, ears or eyes modelled), five views left to right: front three-quarter from the mouse's RIGHT (head toward
   image right), front, the mouse's LEFT side (head faces IMAGE LEFT), back, the mouse's RIGHT side (head faces IMAGE
   RIGHT). Flat grey is background, not creature. Use it for proportions only: a low, long, teardrop body with a
   pointed snout, the body about as long as the tail, the back low and rounded, the belly on the ground.
2. `references_hd/mm9_top_tier1.png` — top view of the same model (head toward image top), proportions only (the body
   is broad at the hips and tapers to the snout). Its zig-zag tail is NOT the design: the tail lies straight back.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the mouse's RIGHT, camera slightly above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front (head toward the camera) | 1536x1024 |
| `02_back.png` | back (tail toward the camera) | 1536x1024 |
| `03_left.png` | the mouse's LEFT side: head faces IMAGE LEFT (as input 1 view 3) | 1536x1024 |
| `04_right.png` | the mouse's RIGHT side: head faces IMAGE RIGHT (as input 1 view 5) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME mouse, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
ambient "mouse" from the supplied renders of its original 3D model, as a 3D modelling/texturing reference. A
beautifully detailed, credible, fully three-dimensional mouse with semi-realistic game materials and sharp fine fur
detail, as if a high-quality sculpt of the original model.

Identity: a common brown house/field mouse.
- Fur: short, dense, smooth; warm grey-brown on the back, head top and flanks with fine darker ticking; the belly,
  chin and throat pale cream-grey; a soft transition along the flanks. No stripes, no spots.
- Head: pointed snout with a small pink nose and fine whiskers kept short and close to the face (no long free
  whiskers); two round black beady eyes; two large thin rounded ears, pink-grey inside, standing up and slightly out
  to the sides.
- Body: low, rounded, teardrop body, broad at the hips, as input 1.
- Legs: four short legs with small pink paws and fine pink toes, the legs mostly tucked under the body (a mouse
  crouched low on all fours), all four paws visible and flat on the same level.
- Tail: long, thin, naked pink-grey tail with fine rings, as long as the body, lying STRAIGHT back along the ground
  behind the mouse (not curled, not raised, not zig-zag), tapering to a fine tip.

Pose (as input 1, the model's bind pose): crouched low on all four paws, belly almost touching the ground, head
level and pointing straight forward, tail straight back. Symmetric left/right.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. The whole mouse inside the frame with generous margins (never crop the tail tip, ears or paws), genuine
transparent background, no floor, no shadow, no text.

Do NOT: add clothing, a collar, cheese or props; do not make it a rat (no big rat head, no thick tail); no red or
glowing eyes; no long free whiskers sticking far out; no extra legs; do not curl the tail; do not make it cartoonish
(no huge head, no big cartoon eyes); do not crop.

## Per-image checks (re-run before selecting)
One mouse with two round ears and two black eyes; exactly four short legs, all four paws visible on the same level;
one thin straight tail lying back and fully in frame; grey-brown back and cream belly; the correct side faces the
correct image side (03: head to image LEFT; 04: head to image RIGHT); true transparent background; 1536x1024; nothing
cropped.
