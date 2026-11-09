# Codex brief: HD reference views for the MM9 Winged Oddity / Winged Mutant (harpy) (mm9_wingedmutant_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_wingedmutant_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_dfly_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly model with its original skin, five
   views left to right: front three-quarter from the creature's RIGHT, front, creature's LEFT side (face points to
   image LEFT), back, creature's RIGHT side (face points to image RIGHT). Flat grey is background, not creature.
   This is the design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low resolution are NOT
   the design.
2. `references_hd/mm9_skin_tier1_x4.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL, FACE
   AND COLOUR ONLY (the face at the top left, dark feathers, wing membrane with bony spars, talons). The white areas
   are unused texture space, not part of the creature. Never the design or shape.
3. `references_hd/mm9_top_tier1.png` — top view of the same model (face toward image top), for the wing outline.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the creature's RIGHT, camera slightly above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front | 1536x1024 |
| `02_back.png` | back | 1536x1024 |
| `03_left.png` | creature's LEFT side: face points to IMAGE LEFT (as input 1 view 3) | 1536x1024 |
| `04_right.png` | creature's RIGHT side: face points to IMAGE RIGHT (as input 1 view 5) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME creature, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"Winged Mutant" monster (a harpy) from the supplied renders of its original 3D model, as a 3D modelling/texturing
reference. Not a new design. Beautifully detailed, credible fully three-dimensional creature with semi-realistic game
materials and sharp fine detail (small feathers, fine skin scales, leathery wing membrane), as if a high-quality sculpt
of the original model.

Identity: a HARPY — a monstrous winged woman-bird with NO arms, about the height of a person.
- Head: a fierce female humanoid face with pale cyan / blue-grey skin and fine scale texture, angry brows, narrow
  pale eyes, dark blue-black lips slightly parted showing small fangs (as in input 2, top left). Long thick black hair
  with blue sheen swept straight back from the forehead and hanging down the back of the head in three heavy locks.
  No horns, no ears showing, no crown.
- Torso: slender, hunched forward, a dark indigo / navy-blue body covered ENTIRELY in small dense dark feathers and
  downy plumage, from the neck to the hips (chest fully covered by the feathers, no bare skin below the neck).
- NO ARMS AND NO HANDS. Instead two LARGE BAT WINGS grow from the shoulders: steel-blue / slate-teal leathery
  membrane with a fine pebbled scale texture, held by pale blue-grey bony finger spars that fan out from the wrist,
  a thick bony leading edge; the trailing edge scalloped between the spars. Opaque membrane, thin and flat.
- Legs: bird-like digitigrade legs: thighs in dark indigo feathers like baggy breeches down to the knee, the lower
  legs and feet bare, scaly, blue-grey like a raptor's. Each foot has three long forward talons and one rear toe,
  with long curved dark-teal claws.
- Tail: one thin dark whip tail from the lower back, hanging down and back, ending in a small flat diamond-shaped
  (arrowhead) tip.

Pose (exactly as input 1, the model's bind pose): hovering upright in the air, body slightly hunched forward, head
up looking forward, both wings spread WIDE to the sides in a shallow V, slightly arched, membranes facing forward,
not folded, not overlapping the body; the legs hang below with the knees slightly bent and the talons open and
pointing down; the tail hangs down behind.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. Whole creature inside the frame with generous margins (never crop wing tips, talons or the tail tip), genuine
transparent background, no floor, no shadow, no text.

Do NOT: add arms, hands, a second pair of wings, feathered bird wings, horns, armour, clothing, jewellery or weapons;
do not show bare breasts (the chest is covered by dark feathers); do not change the colours; do not make the
membranes transparent; do not crop.

## Per-image checks (re-run before selecting)
No arms; two bat wings spread wide with bony spars; human female face with pale blue skin and black swept-back hair;
dark feathered torso and thighs; scaly raptor feet with talons; thin tail with a diamond tip; pose as input 1; the
correct side faces the correct image side (03: face to image LEFT; 04: face to image RIGHT); true transparent
background; 1536x1024; nothing cropped.
