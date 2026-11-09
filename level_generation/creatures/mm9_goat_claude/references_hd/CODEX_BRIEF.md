# Codex brief: HD reference views for the MM9 Goat (mm9_goat_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_goat_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_wolf_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly goat with its original skin, five views
   left to right: front three-quarter from the goat's RIGHT (head toward image right), front, the goat's LEFT side
   (head faces IMAGE LEFT), back, the goat's RIGHT side (head faces IMAGE RIGHT). Flat grey is background, not
   creature. This is the design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low
   resolution are NOT the design.
2. `references_hd/mm9_skin_tier1_x4.png` — the original 128x128 skin texture enlarged 4x, COAT MATERIAL AND COLOUR
   ONLY (grey-brown hair, paler belly and legs, ridged tan horn, yellow eye). Never the design or shape.
3. `references_hd/mm9_top_tier1.png` — top view of the same model (head toward image top), proportions only.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the goat's RIGHT, camera slightly above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front (head toward the camera) | 1536x1024 |
| `02_back.png` | back (tail toward the camera) | 1536x1024 |
| `03_left.png` | the goat's LEFT side: head faces IMAGE LEFT (as input 1 view 3) | 1536x1024 |
| `04_right.png` | the goat's RIGHT side: head faces IMAGE RIGHT (as input 1 view 5) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME goat, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"Goat" farm animal from the supplied renders of its original 3D model, as a 3D modelling/texturing reference. Not a
new design. A beautifully detailed, credible, fully three-dimensional domestic goat with semi-realistic game materials
and sharp fine short-hair detail, as if a high-quality sculpt of the original model.

Identity: a lean domestic billy goat, slim body, straight back, thin legs.
- Coat: short smooth hair, warm grey-brown (taupe) over the body, slightly paler and greyer on the belly and the inner
  legs, a darker brown head and face; no spots, no long shaggy coat.
- Head: long narrow face, small pale-yellow eyes with horizontal dark pupils, the mouth CLOSED, a short dark BEARD under
  the chin; two long drooping ears sticking out sideways and slightly down; two ridged tan-brown HORNS rising from the
  top of the head in a V, sweeping up and back with slightly outward-curving tips (as input 1 views 1-2).
- Legs: four slim straight legs, small dark cloven hooves.
- Tail: a short upright tuft of a tail sticking up and back at the end of the rump.

Pose (exactly as input 1, the model's bind pose): standing square on all four legs, the legs straight and slightly
apart, all four hooves visible and flat on one level, the neck raised and the head held up and forward, the short tail
pointing up and back. Symmetric left/right in shape.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. The whole goat inside the frame with generous margins (never crop the horns, ears, tail or hooves), genuine
transparent background, no floor, no shadow, no text.

Do NOT: add a bell, a collar, a rope, a saddle, extra horns, extra legs; do not open the mouth; do not make the coat
long or shaggy; do not change the colours to white or black; do not crop.

## Per-image checks (re-run before selecting)
One head with exactly two horns in a V sweeping back, two sideways drooping ears, a short beard, closed mouth; exactly
four legs, all four hooves visible on the same level; one short upright tail; grey-brown coat with a darker head as
input 1; the correct side faces the correct image side (03: head to image LEFT; 04: head to image RIGHT); true
transparent background; 1536x1024; nothing cropped.
