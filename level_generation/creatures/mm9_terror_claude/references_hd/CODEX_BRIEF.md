# Codex brief: HD reference views for the MM9 Terror (two-legged tentacled tunnel monster) (mm9_terror_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_terror_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_dfly_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly model with its original skin, five
   views left to right: front three-quarter from the creature's RIGHT, front, creature's LEFT side (face toward
   IMAGE LEFT), back, creature's RIGHT side (face toward IMAGE RIGHT). Flat grey is background, not creature. This is
   the design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low resolution are NOT the
   design.
2. `references_hd/mm9_skin_tier1_x4.png` — the original skin texture enlarged, SURFACE MATERIAL AND COLOUR ONLY
   (scales, mottling, eyes, teeth). Never the design or shape.
3. `references_hd/mm9_top_tier1.png` — top view of the same model (face toward image BOTTOM), tentacle layout only.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the creature's RIGHT, camera slightly above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front | 1536x1024 |
| `02_back.png` | back | 1536x1024 |
| `03_left.png` | creature's LEFT side: face toward IMAGE LEFT (as input 1 view 3) | 1536x1024 |
| `04_right.png` | creature's RIGHT side: face toward IMAGE RIGHT (as input 1 view 5) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME creature, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"Terror" (tunnel terror) monster from the supplied renders of its original 3D model, as a 3D modelling/texturing
reference. Not a new design. Beautifully detailed, credible fully three-dimensional organic creature with
semi-realistic game materials and sharp fine detail (wet amphibian/reptile skin, fine scales), as if a high-quality
sculpt of the original model.

Identity: a squat monster a little taller than a man, which is mostly a huge head-mouth on two legs, with NO ARMS:
- Legs and body: two thick short digitigrade-looking legs, each foot with three thick forward toes ending in pale
  curved claws (and a small rear claw), feet flat on the ground. A short stout torso with a teal-blue finely scaled
  belly/chest; green-olive back with dark mottling. NO arms, NO hands.
- Head: a very large wide head sitting directly on the torso (no neck), the front split by an enormous gaping mouth,
  open wide, ringed with long pale curved fangs, dark red throat and a pink tongue. A bulging lobe on each side of the
  mouth carries one big round ORANGE eye with a black slit pupil (two eyes, one per side, facing forward). Two small
  heavy-lidded half-closed eyes sit on the top of the head. Skin green with yellow-olive mottling.
- SIX tentacles grow from the head, all with blue-grey knobbly scale bands along their undersides and dark tips:
  (a) two long straight HORN-like tentacles from the top corners of the head, pointing straight out sideways and
      slightly up, tapering to sharp points;
  (b) two very long thick arching tentacles from the sides of the head that sweep out, down and then FORWARD at waist
      height, each ending in a small open round mouth with a red inside;
  (c) two shorter thin tentacles from under the cheek lobes, pointing out sideways and slightly forward, tapering to
      points.

Pose (exactly as input 1, the model's pose): standing upright on both feet, mouth wide open, all six tentacles held
spread clear of the body and of each other as in input 1. Symmetric left/right.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. Whole creature inside the frame with generous margins (never crop tentacle tips or feet), genuine transparent
background, no floor, no shadow, no text.

Do NOT: add arms or hands, a tail, wings, a neck, extra eyes beyond the four described, extra tentacles (exactly
six), armour; do not close the mouth; do not change the colours; do not crop.

## Per-image checks (re-run before selecting)
Two legs with three clawed toes each, no arms; huge open fanged mouth with an orange eye on each side lobe; exactly six
tentacles (two horn tentacles out sideways from the top, two long arching mouth-tipped tentacles reaching forward,
two short thin ones under the cheeks); colours as input 1; the correct side faces the correct image side (03: face to
image LEFT; 04: face to image RIGHT); true transparent background; 1536x1024; nothing cropped.
