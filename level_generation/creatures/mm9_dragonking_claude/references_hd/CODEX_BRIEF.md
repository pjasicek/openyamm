# Codex brief: HD reference views for the MM9 Dragon King (green great dragon, final boss) (mm9_dragonking_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_dragonking_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_dfly_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly model with its original skin, five
   views left to right: front three-quarter from the creature's RIGHT, front, creature's LEFT side (head faces image
   LEFT), back, creature's RIGHT side (head faces image right). Flat grey is background, not creature. This is the
   design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low resolution are NOT the design.
2. `references_hd/mm9_head_tier1.png` — close renders of the same model's head (three-quarter, front, left side):
   horns, crest, side frills, eyes, teeth. Same authority as input 1, for the head.
3. `references_hd/mm9_skin_tier1_x4.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND
   COLOUR ONLY (scale pattern, belly plates, yellow eye, red mouth). Never the design or shape.
4. `references_hd/mm9_top_tier1.png` — top view of the same model (head toward image bottom), for the wing layout.
5. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the creature's RIGHT, camera slightly above (as input 1 view 1) | 1024x1536 portrait |
| `01_front.png` | front | 1024x1536 |
| `02_back.png` | back | 1024x1536 |
| `03_left.png` | creature's LEFT side: head faces IMAGE LEFT (as input 1 view 3) | 1024x1536 |
| `04_right.png` | creature's RIGHT side: head faces IMAGE RIGHT (as input 1 view 5) | 1024x1536 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME creature, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"Dragon King" monster (the final boss of the Dragon's Lair) from the supplied renders of its original 3D model, as a 3D
modelling/texturing reference. Not a new design. A majestic, credible, fully three-dimensional great dragon with
semi-realistic game materials and sharp fine detail (small overlapping scales, belly plates, horn ridges, membrane
veins), as if a high-quality sculpt of the original model.

Identity: a GREEN great dragon with four legs and two large bat-like wings.
- Body: lean and muscular, long S-curved neck, deep chest, slim waist. Olive/moss-green scaly hide with darker green
  mottling and fine yellow-green highlights; a ventral stripe of transverse yellow-green belly plates runs from the
  throat down the chest and belly to the tail. A row of short dark spikes runs along the back of the tail.
- Head: long, narrow reptilian head with a long snout; TWO long horns sweeping up and back from the top of the head
  plus one central crest spike between them; a large spiky membrane FRILL fanning out on each side of the head behind
  the jaw (fin-like, dark green with spine ribs), small spiky fins under the chin; glowing YELLOW eyes with black
  vertical slit pupils; mouth slightly open showing rows of white pointed teeth and a red interior.
- Forelegs: slender arms held forward at chest height, each hand with THREE clawed fingers (dark claws).
- Hind legs: strong digitigrade legs, each foot with THREE long forward toes ending in dark claws.
- Tail: long, tapering, hanging down to the ground behind and below the feet, ending in a pointed spear/arrowhead tip.
- Wings: two LARGE bat-like wings rooted on the upper back behind the shoulders, each with a strong arm bone and
  three long finger spars; the membrane is very dark green-black, glossy, with lighter green veins and a few lighter
  green patches, a scalloped trailing edge between the spars. Thin membranes, a clawed thumb at the wing wrist.

Pose (exactly as input 1, the model's bind pose): the dragon REARS UPRIGHT on its hind legs, torso nearly vertical,
neck curving up with the head looking forward, forelegs reaching forward, tail hanging down behind. Both wings are
RAISED and swept BACK above and behind the body, spread wide (seen from the side as a large near-vertical sheet behind
the neck; from the front as two tall narrow panels on either side of the body), not folded, not overlapping the
body or head. Symmetric left/right.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body, no fire, no smoke. Whole creature inside the frame with generous margins (never crop wing tips, horns, toes or
the tail tip), genuine transparent background, no floor, no shadow, no text.

Do NOT: add armour, a crown, jewellery, a rider, extra limbs, extra heads, extra wings or extra horns; do not change
the colours (no red/gold dragon); do not close the wings or fold them against the body; do not change the pose to
four-legged walking; do not add breath fire; do not crop.

## Per-image checks (re-run before selecting)
Green dragon; upright rearing pose as input 1; two big raised, swept-back wings with three finger spars each, dark
green-black membrane; two long horns + central crest; side frills; yellow slit eyes; open mouth with white teeth;
three claws per hand and per foot; yellow-green belly plates on the ventral side; tail hanging down with spear tip
inside the frame; the correct side faces the correct image side (03: head to image LEFT; 04: head to image RIGHT);
true transparent background; 1024x1536.
