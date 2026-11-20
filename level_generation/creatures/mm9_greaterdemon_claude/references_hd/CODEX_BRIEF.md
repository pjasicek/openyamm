# Codex brief: HD reference views for the MM9 Greater Demon (mm9_greaterdemon_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_greaterdemon_claude/references_hd/`.
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
2. `references_hd/mm9_skin_tier1_x4.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL, FACES
   AND COLOUR ONLY (olive reptile hide, silver-grey armour plates, studded belt, wing membrane). The white areas are
   unused texture space, not part of the creature. Never the design or shape.
3. `references_hd/mm9_top_tier1.png` — top view of the same model (face toward image top), for the wing and arm layout.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the creature's RIGHT, camera slightly above (as input 1 view 1) | 1024x1536 portrait |
| `01_front.png` | front | 1024x1536 |
| `02_back.png` | back | 1024x1536 |
| `03_left.png` | creature's LEFT side: face points to IMAGE LEFT (as input 1 view 3) | 1024x1536 |
| `04_right.png` | creature's RIGHT side: face points to IMAGE RIGHT (as input 1 view 5) | 1024x1536 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME creature, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"Greater Demon" monster from the supplied renders of its original 3D model, as a 3D modelling/texturing reference.
Not a new design. Beautifully detailed, credible fully three-dimensional creature with semi-realistic game materials
and sharp fine detail (reptile scales, ribbed hide, worn metal-like chitin plates), as if a high-quality sculpt of the
original model.

Identity: a huge winged BIPEDAL demon, about twice the height of a man, hunched and top-heavy.
- Head: a reptilian demon skull-face with a long snout and an OPEN jaw lined with small yellow teeth and longer
  fangs; narrow glowing yellow eyes; two big horns curving out sideways and forward from the sides of the head; a
  crest of long spikes along the top of the head and neck.
- Arms: two long heavy arms spread forward and down. Each arm ends NOT in a hand but in a SMALLER SNAKE / DRAGON HEAD
  with glowing yellow eyes and an open jaw with yellow teeth, its mouth pointing forward and down, ringed at the
  wrist by three spikes. No fingers, no hands, no claws on the arms.
- Body: olive / khaki-green reptile hide with darker brown mottling and a ribbed belly; dark silver-grey chitin
  armour plates grown into the hide (layered pointed plates on the chest, the shoulders, the shins and a pointed loin
  plate hanging in front and behind from a dark studded belt). A few short spikes on the upper back and shoulders.
- Wings: two large BAT WINGS from the upper back, raised high and swept back: brown-black leathery membrane with
  olive-gold vein marbling, olive bony wing arms with a spiked claw at the top joint and long spars to the trailing
  points. Opaque membrane, thin and flat.
- Legs: thick digitigrade legs, armour-plated thighs, the lower legs bent backward with a spike at the heel; each
  foot has TWO big clawed toes pointing forward.
- Tail: a long thin scaly tail hanging down behind between the legs to the ground, ending in a three-pronged
  arrowhead spike.

Pose (exactly as input 1, the model's bind pose): standing upright, slightly hunched, knees bent, both arm-heads held
out forward to the sides at hip-to-chest height, both wings raised up and back in a wide V, not folded and not
overlapping the body; the tail hangs to the ground behind.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. Whole creature inside the frame with generous margins (never crop wing tips, horns, feet or the tail tip),
genuine transparent background, no floor, no shadow, no text.

Do NOT: add hands, fingers, weapons, clothing, extra heads, extra limbs or extra wings; do not change the arm-ends
into hands; do not close the jaws; do not change the colours; do not make the membranes transparent; do not crop.

## Per-image checks (re-run before selecting)
Main head with horns and open jaw; both arms end in small open-mouthed snake heads (no hands); two bat wings raised in
a V; olive hide with silver-grey plates and studded belt; two-toed digitigrade feet; thin tail with an arrowhead tip
to the ground; pose as input 1; the correct side faces the correct image side (03: face to image LEFT; 04: face to
image RIGHT); true transparent background; 1024x1536; nothing cropped.
