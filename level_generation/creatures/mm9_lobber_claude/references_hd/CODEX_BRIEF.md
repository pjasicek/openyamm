# Codex brief: HD reference views for the MM9 Lobber (carnivorous stalk plant) (mm9_lobber_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_lobber_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_dfly_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model (turned upright: in OpenYAMM the plant grows from the ground).

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly model with its original skin, five
   views left to right: front three-quarter from the creature's RIGHT, front, creature's LEFT side (head/mouth faces
   image LEFT), back, creature's RIGHT side (head/mouth faces image RIGHT). Flat grey is background, not creature.
   This is the design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low resolution are NOT
   the design.
2. `references_hd/mm9_skin_tier1_x4.png` — the original 128x128 skin texture enlarged 4x, SURFACE MATERIAL AND
   COLOUR ONLY (scale pattern, veins). Never the design or shape.
3. `references_hd/mm9_top_tier1.png` — top view of the same model (front toward image bottom), limb layout only.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the creature's RIGHT, camera slightly above (as input 1 view 1) | 1024x1536 portrait |
| `01_front.png` | front | 1024x1536 |
| `02_back.png` | back | 1024x1536 |
| `03_left.png` | creature's LEFT side: mouth faces IMAGE LEFT (as input 1 view 3) | 1024x1536 |
| `04_right.png` | creature's RIGHT side: mouth faces IMAGE RIGHT (as input 1 view 5) | 1024x1536 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME creature, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"Lobber" monster from the supplied renders of its original 3D model, as a 3D modelling/texturing reference. Not a new
design. Beautifully detailed, credible fully three-dimensional organic creature with semi-realistic game materials
and sharp fine detail (fine scales, veins, waxy plant flesh), as if a high-quality sculpt of the original model.

Identity: a carnivorous stalk PLANT-creature, about the height of a person, three parts from bottom to top:
- Root bulb (on the ground): a squat, wide, rounded faceted bulb/tuber like an upturned fleshy flower cup, about a
  third of the creature's width, pink-red waxy flesh with paler mottling and dark red veins.
- Stalk: ONE thin, smooth, slightly S-curved stalk rising from the top centre of the bulb, as thick as a finger relative
  to the body, brown-olive with a fine snake-scale pattern. No leaves on the stalk.
- Head (on top of the stalk): a pod-like carnivorous head shaped like an open beak or flytrap, facing FORWARD: a pointed
  upper lid and a pointed lower lid, both pink-red/salmon with a fine scale pattern and yellow-green toward the back;
  the mouth gapes forward between them showing a fibrous interior of teal-blue and dark tendril-like teeth.
  SIX long thin jointed limbs grow from the head, olive green with a tan scale pattern, darkening to sharp reddish
  tips, each bent once like a spider leg or mantis claw: two pairs spread out to the left and right sides of the head
  and curve UP, and one pair rises straight up from the top of the head like two horns. No eyes, no stalk leaves.

Pose (exactly as input 1, the model's pose): standing upright, the stalk vertical, the head on top facing forward with
the mouth open, all six limbs spread clear of the head and of each other (as input 1). Symmetric left/right.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. Whole creature inside the frame with generous margins (never crop limb tips or the bulb), genuine transparent
background, no floor, no shadow, no text.

Do NOT: add eyes, a face, leaves, flowers, roots spreading on the ground, extra limbs, a second head or a pot; do not
close the mouth; do not thicken the stalk into a trunk; do not change the colours; do not crop.

## Per-image checks (re-run before selecting)
Bulb at the bottom, one thin stalk, head on top facing the correct way with an open beak mouth; exactly six limbs
(two side pairs curving up, one pair of horn-like limbs straight up), all clear; colours as input 1; the correct side
faces the correct image side (03: mouth to image LEFT; 04: mouth to image RIGHT); true transparent background;
1024x1536; nothing cropped.
