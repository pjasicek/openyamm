# Codex brief: HD reference views for the MM9 Goose (mm9_goose_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_goose_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_crow_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_goose.png` — renders of the ORIGINAL MM9 low-poly goose with its original white skin,
   five views left to right: front three-quarter from the goose's RIGHT (head toward image right), front, the goose's
   LEFT side (beak points to IMAGE LEFT), back, the goose's RIGHT side (beak points to IMAGE RIGHT). Flat grey is
   background, not creature. This is the design, anatomy, POSE, proportions and colour authority. Its faceting, blur
   and low resolution are NOT the design.
2. `references_hd/mm9_skin_goose_x4.png` — the original 128x128 skin texture enlarged 4x: FEATHER MATERIAL AND COLOUR
   ONLY (white downy plumage, orange-yellow bill, orange webbed feet, small dark eye). Never the design or shape.
3. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the goose's RIGHT, camera slightly above (as input 1 view 1) | 1024x1536 portrait |
| `01_front.png` | front (beak toward the camera) | 1024x1536 |
| `02_back.png` | back (tail toward the camera) | 1024x1536 |
| `03_left.png` | the goose's LEFT side: beak points to IMAGE LEFT (as input 1 view 3) | 1024x1536 |
| `04_right.png` | the goose's RIGHT side: beak points to IMAGE RIGHT (as input 1 view 5) | 1024x1536 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME goose, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"Goose" creature from the supplied renders of its original 3D model, as a 3D modelling/texturing reference. Not a new
design. A beautifully detailed, credible, fully three-dimensional white domestic farm goose with semi-realistic game
materials and sharp fine feather detail, as if a high-quality sculpt of the original model.

Identity: a white domestic goose standing.
- Plumage: pure white with soft light-grey feather shading, clearly readable feathers: small contour feathers on the
  neck and breast, layered folded wing feathers on the flanks/back with visible feather edges, short pointed tail.
  Not glossy.
- Head and bill: smooth rounded goose head, a straight orange-yellow bill about as long as the head, wedge-shaped,
  pointing FORWARD, nearly horizontal, the bill CLOSED (upper and lower mandible together, no gap); a small dark eye
  high on each side of the head. No knob on the bill, no wattle, no dewlap or hanging skin under the chin or throat:
  the underside of the head runs smoothly from the bill base into a slim throat.
- Neck: long and slim, rising nearly vertically from the breast with a gentle S, as in input 1.
- Wings: folded flat against the body (not spread, not raised).
- Legs and feet: two short orange legs; each foot has three forward toes joined by orange webbing, flat on the
  ground, toes pointing FORWARD and slightly outward, as in input 1.

Pose (exactly as input 1, the model's bind pose): standing upright on both feet, feet apart under the body, the body
tilted slightly with the tail lower, neck raised high, head level, bill pointing forward. Symmetric left/right.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. The whole goose inside the frame with generous margins (never crop the bill, tail or feet), genuine transparent
background, no floor, no grass, no shadow, no text.

Do NOT: add grass, a pond, a second goose, a knob on the bill, a wattle or dewlap, spread wings, open the bill,
colours other than white/light grey plumage and the orange bill and feet; do not crop.

## Per-image checks (re-run before selecting)
One goose; white plumage; closed orange bill pointing forward, nearly horizontal; no chin dewlap; long upright neck;
wings folded; two orange legs with webbed three-toed feet pointing forward; the correct side faces the correct image
side (03: beak to image LEFT; 04: beak to image RIGHT); true transparent background; 1024x1536; nothing cropped.
