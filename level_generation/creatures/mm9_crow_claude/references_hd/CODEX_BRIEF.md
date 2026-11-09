# Codex brief: HD reference views for the MM9 Bird (crow) (mm9_crow_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_crow_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_dfly_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly crow with its original skin, five
   views left to right: front three-quarter from the bird's RIGHT, front, the bird's LEFT side (head faces IMAGE
   LEFT), back, the bird's RIGHT side (head faces IMAGE RIGHT). Flat grey is background, not creature. This is the
   design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low resolution are NOT the design.
2. `references_hd/mm9_skin_tier1_x4.png` — the original 128x128 skin texture enlarged 4x, FEATHER MATERIAL AND COLOUR
   ONLY (glossy blue-black plumage, the grey beak, the eye). Never the design or shape.
3. `references_hd/mm9_top_tier1.png` — top view of the same model (head toward image top), for the wing and tail
   outline.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the bird's RIGHT, camera slightly above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front (head toward the camera) | 1536x1024 |
| `02_back.png` | back (tail toward the camera) | 1536x1024 |
| `03_left.png` | the bird's LEFT side: head faces IMAGE LEFT (as input 1 view 3) | 1536x1024 |
| `04_right.png` | the bird's RIGHT side: head faces IMAGE RIGHT (as input 1 view 5) | 1536x1024 |
| `05_wings_top.png` | top view straight down, head toward image top, both wings and the tail fully spread and seen face-on (as input 3) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–05 with the selected 00 as
an additional input so all views are the SAME bird, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"Bird" monster (a crow) from the supplied renders of its original 3D model, as a 3D modelling/texturing reference.
Not a new design. A beautifully detailed, credible, fully three-dimensional carrion crow with semi-realistic game
materials and sharp fine feather detail, as if a high-quality sculpt of the original model.

Identity: a large black crow in flight.
- Plumage: glossy black with a subtle blue-violet sheen, clearly readable feathers: contour feathers on the body,
  layered coverts on the wings, long separated primary feathers at the wing tips, a fan of tail feathers. Not matte.
- Head: crow head with a strong slightly curved dark grey-black beak (as long as the head), a small dark eye with a
  faint brown iris; the beak closed.
- Wings: long broad wings spread fully out to the sides, nearly flat and level (as inputs 1 and 3: a straight
  leading edge, the trailing edge sweeping back, the tips slightly swept back), primary feathers fanned at the tips.
- Tail: a wedge-shaped fan of long tail feathers spread behind the body (as input 3).
- Legs: two thin dark scaly legs hanging DOWN below the body, feet with three forward toes and one back toe and dark
  claws, toes loosely curled (as input 1).

Pose (exactly as input 1, the model's bind pose): gliding with the wings spread flat to the sides, the head and neck
reaching forward and bent DOWN so the beak points down and forward, the legs hanging down, the tail spread behind.
Symmetric left/right.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. The whole bird inside the frame with generous margins (never crop the wing tips, tail or feet), genuine
transparent background, no floor, no perch, no shadow, no text.

Do NOT: add a perch, branch, a second bird, extra wings or legs, glowing eyes, colours other than black/blue-black and
the grey beak; do not fold the wings; do not open the beak; do not crop.

## Per-image checks (re-run before selecting)
One crow; two wings spread flat to the sides with separated primaries; one fan tail; two legs hanging down with
feet; head bent down with a closed dark beak; glossy black with a blue sheen; the correct side faces the correct
image side (03: head to image LEFT; 04: head to image RIGHT); 05 seen straight from above with the head toward the
image top and both wings and the tail flat and complete; true transparent background; 1536x1024; nothing cropped.
