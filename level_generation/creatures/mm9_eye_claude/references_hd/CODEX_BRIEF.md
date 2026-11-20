# Codex brief: HD reference views for the MM9 Eye (floating beholder eye with stalks) (mm9_eye_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_eye_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_dfly_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly model with its original skin, five
   views left to right: front three-quarter from the creature's RIGHT, front, creature's LEFT side (face/eye looks
   toward image LEFT), back, creature's RIGHT side (face/eye looks toward image RIGHT). Flat grey is background, not
   creature. This is the design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low
   resolution are NOT the design.
2. `references_hd/mm9_skin_tier1_x4.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND
   COLOUR ONLY (wrinkled leathery hide, veins, the eye's iris and sclera, the teeth). Never the design or shape.
3. `references_hd/mm9_top_tier1.png` — top view of the same model (front toward image bottom), stalk and leg layout.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the creature's RIGHT, camera slightly above (as input 1 view 1) | 1024x1536 portrait |
| `01_front.png` | front (the big eye looks at the camera) | 1024x1536 |
| `02_back.png` | back | 1024x1536 |
| `03_left.png` | creature's LEFT side: the face looks toward IMAGE LEFT (as input 1 view 3) | 1024x1536 |
| `04_right.png` | creature's RIGHT side: the face looks toward IMAGE RIGHT (as input 1 view 5) | 1024x1536 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME creature, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"Eye" monster (a floating beholder-like eye creature) from the supplied renders of its original 3D model, as a 3D
modelling/texturing reference. Not a new design. Beautifully detailed, credible fully three-dimensional organic
creature with semi-realistic game materials and sharp fine detail (wrinkled leathery hide, veins, wet eyeballs), as if
a high-quality sculpt of the original model.

Identity (exactly as input 1):
- Body: a single roundish, slightly heart-shaped fleshy head-body about as wide as it is tall, tan-brown wrinkled
  leathery hide with darker brown folds, paler ochre highlights and faint glossy veins. A heavy overhanging brow ridge
  across the front with a shallow notch in its middle.
- ONE large central eye in a deep fleshy socket under the brow, facing FORWARD: a big wet eyeball with white-cream
  sclera, a blue-grey iris and a black pupil, a red-veined fleshy rim (lower lid) around it.
- Mouth below the eye: a small forward-jutting lower jaw/lip with a row of small pale teeth, a dark mouth slit between
  the eye and the jaw.
- FIVE thin eyestalks grow from the upper body, each a thin brown jointed stalk ending in a small eyeball (cream-white
  with a dark blue-grey iris) set in a pale bony/horny cup: two long stalks rising up and out from the top left and top
  right (the longest, bending outward then forward at the tip), one shorter stalk from the top middle bending forward,
  and two short stalks from the left and right sides of the body at eye height. All small eyes look forward.
- EIGHT long, very thin, jointed legs/tentacles hang DOWN from the underside of the body, about twice the body height
  long, tan-brown like the stalks, tapering to sharp dark points, gently spread like the ribs of a closed umbrella
  (as input 1): the outer ones angle outward, the inner ones hang nearly straight down. They do not touch the ground;
  the creature floats.
- No arms, no wings, no tail, no horns, no extra eyes beyond the six (one large, five on stalks).

Pose (exactly as input 1, the model's pose): floating upright, the big eye looking forward, all five stalks and all
eight legs clear of each other and of the body. Symmetric left/right.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. Whole creature inside the frame with generous margins (never crop stalk tips or leg tips), genuine transparent
background, no floor, no shadow, no text.

Do NOT: add arms, wings, a tail, tentacles with suckers, extra eyestalks, a second big eye, a big fanged maw, horns or
armour; do not shorten or thicken the legs into tentacle roots; do not change the colours; do not crop.

## Per-image checks (re-run before selecting)
One body with ONE big forward eye and a toothed lower jaw below it; exactly FIVE eyestalks (two long top, one short
top middle, two short side), each ending in a small eye; exactly EIGHT thin legs hanging down, long and clear of each
other, none cropped; colours as input 1; the correct side faces the correct image side (03: face to image LEFT; 04:
face to image RIGHT); true transparent background; 1024x1536; nothing cropped.
