# Codex brief: HD reference views for the MM9 Hen (mm9_hen_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_hen_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_crow_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly hen with its original skin, five
   views left to right: front three-quarter from the hen's RIGHT (head toward image right), front, the hen's LEFT
   side (head faces IMAGE LEFT), back, the hen's RIGHT side (head faces IMAGE RIGHT). Flat grey is background, not
   creature. This is the design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low
   resolution are NOT the design.
2. `references_hd/mm9_skin_tier1_x4.png` — the original 128x128 skin enlarged 4x, MATERIAL AND COLOUR ONLY (white
   feathers, red comb and wattle, pale yellow beak, yellow-orange scaly legs). Never the design or shape.
3. `references_hd/mm9_top_tier1.png` — top view of the same model (head toward image top), for the body outline.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the hen's RIGHT, camera slightly above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front (head toward the camera) | 1536x1024 |
| `02_back.png` | back (tail toward the camera) | 1536x1024 |
| `03_left.png` | the hen's LEFT side: head faces IMAGE LEFT (as input 1 view 3) | 1536x1024 |
| `04_right.png` | the hen's RIGHT side: head faces IMAGE RIGHT (as input 1 view 5) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME hen, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic
IX "Hen" (a farmyard chicken) from the supplied renders of its original 3D model, as a 3D modelling/texturing
reference. Not a new design. A beautifully detailed, credible, fully three-dimensional white hen with semi-realistic
game materials and sharp fine feather detail, as if a high-quality sculpt of the original model.

Identity: a plump white domestic hen standing.
- Plumage: clean white with soft light-grey shading between feathers, clearly readable feathers: small contour
  feathers on the breast and neck, the folded wing with layered coverts and flight feathers lying flat and tight
  against each side of the body, a short upturned pointed tail of white feathers at the back (as input 1). No other
  colours in the plumage.
- Head: small rounded hen head; a SHORT, DEEP, stout conical pale-yellow beak, closed, pointing FORWARD and only
  slightly down exactly as in input 1 (no long or thin beak, no hook); a small low red single comb on top of the
  head; a small round red wattle directly under the base of the beak, compact and close to the head (not a hanging
  chin or throat pouch); red bare skin around the eye; a small round amber-orange eye with a black pupil.
- Neck: short and full, feathered, flowing smoothly into the breast; the throat is a smooth feathered line, not a
  bulge.
- Legs: two yellow-orange scaly legs, straight, vertical and clearly SEPARATED with a gap of air between them (as
  input 1 front view), feathered thighs ending above the scaly shanks.
- Feet: flat on an invisible ground plane, each with THREE front toes spread FORWARD and slightly outward and ONE
  short hind toe pointing straight BACK, small pale claws. Soles down.

Pose (exactly as input 1, the model's bind pose): standing upright and square, body level and plump, head raised
on the short neck looking forward, both legs straight and apart, wings folded. Symmetric left/right.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. The whole hen inside the frame with generous margins (never crop the tail, comb or toes), genuine transparent
background, no floor, no ground shadow, no straw, no text.

Do NOT: add a second animal, chicks, eggs, straw or a perch; do not spread or raise the wings; do not open the beak;
no long beak, no hooked beak, no hanging throat; no brown, black or speckled plumage; no extra toes or legs; do not
crop.

## Per-image checks (re-run before selecting)
One white hen; short deep closed pale-yellow beak pointing forward; small red comb and compact red wattle; amber eye;
wings folded flat on the sides; short pointed upturned tail; two separated straight legs with three forward toes and
one hind toe each, soles down; the correct side faces the correct image side (03: head to image LEFT; 04: head to
image RIGHT); true transparent background; 1536x1024; nothing cropped.
