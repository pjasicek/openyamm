# Codex brief: HD reference views for the MM9 dog (mm9_dog_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_dog_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_wolf_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views.png` — renders of the ORIGINAL MM9 low-poly dog with its original skin, five views left
   to right: front three-quarter from the dog's RIGHT (head toward image right), front, the dog's LEFT side (head
   faces IMAGE LEFT), back, the dog's RIGHT side (head faces IMAGE RIGHT). Flat grey is background, not creature.
   This is the design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low resolution are
   NOT the design.
2. `references_hd/mm9_head_views.png` — close renders of the same model's head (front, the dog's left profile,
   three-quarter): the FACE authority (dark muzzle, hanging ears, slightly open mouth with a pink tongue).
3. `references_hd/mm9_skin_x8.png` — the original 128x128 skin texture enlarged 8x, FUR MATERIAL AND COLOUR ONLY
   (the photo of a black-and-tan mixed-breed dog it was painted from). Never the design or shape.
4. `references_hd/mm9_top.png` — top view of the same model (head toward image top), proportions only.
5. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the dog's RIGHT, camera slightly above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front (head toward the camera) | 1536x1024 |
| `02_back.png` | back (tail toward the camera) | 1536x1024 |
| `03_left.png` | the dog's LEFT side: head faces IMAGE LEFT (as input 1 view 3) | 1536x1024 |
| `04_right.png` | the dog's RIGHT side: head faces IMAGE RIGHT (as input 1 view 5) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME dog, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"dog" (a town dog) from the supplied renders of its original 3D model, as a 3D modelling/texturing reference. Not a
new design. A beautifully detailed, credible, fully three-dimensional dog with semi-realistic game materials and
sharp fine fur detail, as if a high-quality sculpt of the original model.

Identity: a medium-large, athletic black-and-tan mixed-breed dog (shepherd/hound type).
- Fur: a glossy BLACK saddle over the back, the top of the neck, the flanks and the top of the tail; rich TAN /
  chestnut brown on the head, cheeks, the four legs, the paws and the underside of the tail; a CREAM-WHITE chest bib
  on the front of the chest and throat; the MUZZLE is dark (black-brown) toward the nose. Short smooth dense coat,
  not long or shaggy.
- Head: broad skull, medium-long muzzle with a black nose; two soft HANGING ears (dropped flaps folding down beside
  the head, dark brown), small dark brown eyes; the mouth SLIGHTLY OPEN (a narrow relaxed gap) showing a pink tongue
  and a few white teeth (as inputs 2 and 3), dark lips.
- Body: deep chest, tucked belly, four straight sturdy legs with tan paws and small dark claws (four toes per paw).
- Tail: medium length, held straight out BACK, almost horizontal, tapering to a point (as input 1), black on top,
  tan beneath.

Pose (exactly as input 1, the model's bind pose): standing square on all four legs, the legs straight and separated
with air gaps, all four paws visible and flat on one level, head held up and forward, the tail straight back clear
of the hind legs. Symmetric left/right.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. The whole dog inside the frame with generous margins (never crop the tail tip, ears or paws), genuine
transparent background, no floor, no shadow, no text.

Do NOT: add a collar, a harness, clothes, scars, glowing eyes, extra legs or a second tail; do not close the mouth
fully and do not open it wide; no upright ears; do not make the fur long or shaggy; do not change the colours; do not
crop.

## Per-image checks (re-run before selecting)
One head with two hanging ears, a narrow open mouth with pink tongue, black nose; exactly four legs, all four tan
paws on the same level; one tail straight back; black saddle, tan legs and head, cream chest bib; the correct side
faces the correct image side (03: head to image LEFT; 04: head to image RIGHT); true transparent background;
1536x1024; nothing cropped.
