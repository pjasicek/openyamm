# Codex brief: HD reference views for the MM9 Grey Wolf (mm9_wolf_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_wolf_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_lobber_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly wolf with its original skin, five
   views left to right: front three-quarter from the wolf's RIGHT (head toward image right), front, the wolf's LEFT
   side (head faces IMAGE LEFT), back, the wolf's RIGHT side (head faces IMAGE RIGHT). Flat grey is background, not
   creature. This is the design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low
   resolution are NOT the design.
2. `references_hd/mm9_skin_tier1_x4.png` — the original 256x256 skin texture enlarged 4x, FUR MATERIAL AND COLOUR
   ONLY (fur direction, saddle, face mask). Never the design or shape.
3. `references_hd/mm9_top_tier1.png` — top view of the same model (head toward image top), proportions only.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the wolf's RIGHT, camera slightly above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front (head toward the camera) | 1536x1024 |
| `02_back.png` | back (tail toward the camera) | 1536x1024 |
| `03_left.png` | the wolf's LEFT side: head faces IMAGE LEFT (as input 1 view 3) | 1536x1024 |
| `04_right.png` | the wolf's RIGHT side: head faces IMAGE RIGHT (as input 1 view 5) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME wolf, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"Grey Wolf" monster from the supplied renders of its original 3D model, as a 3D modelling/texturing reference. Not a
new design. A beautifully detailed, credible, fully three-dimensional wolf with semi-realistic game materials and
sharp fine fur detail, as if a high-quality sculpt of the original model.

Identity: a big, lean, long-legged grey wolf.
- Fur: a dark grey-brown, almost charcoal SADDLE over the back, shoulders, neck top and the top of the tail; pale
  cream/buff-grey on the flanks, belly, legs, cheeks and the underside of the tail; a pale cream collar band behind
  the shoulders (visible from above and the sides as in inputs 1 and 3); a pale chest bib. The muzzle and the face
  above the eyes are DARK charcoal (a dark face mask), the cheeks paler. Short dense realistic fur, not long or shaggy.
- Head: long wolf muzzle, two upright pointed ears, small amber eyes; the mouth slightly OPEN in a snarl showing white
  teeth and long fangs in both jaws with dark gums and lips (as input 1). Black nose.
- Body: deep chest, narrow waist, four slim straight legs with pale paws and small dark claws (four toes per paw).
- Tail: long, bushy, hanging down and back in a straight diagonal (as input 1), dark on top, pale beneath, not curled.

Pose (exactly as input 1, the model's bind pose): standing square on all four legs, the legs straight and separated,
all four paws visible and flat, the head held forward and slightly low, the tail hanging back and down clear of the
hind legs. Symmetric left/right.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. The whole wolf inside the frame with generous margins (never crop the tail tip, ears or paws), genuine
transparent background, no floor, no shadow, no text.

Do NOT: add armour, a collar, a saddle, scars, glowing eyes, extra legs or a second tail; do not close the mouth; do
not make the fur long or shaggy; do not change the colours; do not crop.

## Per-image checks (re-run before selecting)
One head with two upright ears and an open snarling mouth with fangs; exactly four legs, all four paws visible on the
same level; one bushy tail hanging back and down; the dark saddle, pale collar band, dark face mask and pale legs as
input 1; the correct side faces the correct image side (03: head to image LEFT; 04: head to image RIGHT); true
transparent background; 1536x1024; nothing cropped.
