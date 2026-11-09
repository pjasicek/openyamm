# Codex brief: HD reference views for the MM9 Lobber Pod (crawling seed pod) (mm9_lobber_claude, pod)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_lobber_claude/references_hd_pod/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_dfly_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd_pod/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly model with its original skin, five
   views left to right: front three-quarter from the creature's RIGHT, front, creature's LEFT side (mouth faces image
   LEFT), back, creature's RIGHT side (mouth faces image RIGHT). Flat grey is background, not creature. This is the
   design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low resolution are NOT the design.
2. `references_hd_pod/mm9_skin_tier1_x4.png` — the original 128x128 skin enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY.
3. `references_hd_pod/mm9_top_tier1.png` — top view of the same model (front toward image bottom), limb layout only.
4. (second run only) the selected `references_hd_pod/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the creature's RIGHT, camera slightly above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front | 1536x1024 |
| `02_back.png` | back | 1536x1024 |
| `03_left.png` | creature's LEFT side: mouth faces IMAGE LEFT (as input 1 view 3) | 1536x1024 |
| `04_right.png` | creature's RIGHT side: mouth faces IMAGE RIGHT (as input 1 view 5) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME creature, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"Lobber Pod" monster from the supplied renders of its original 3D model, as a 3D modelling/texturing reference. Not a
new design. Beautifully detailed, credible fully three-dimensional organic creature with semi-realistic game materials
and sharp fine detail (fine scales, veins, waxy shell), as if a high-quality sculpt of the original model.

Identity: a small crawling carnivorous SEED POD, knee-high, spider-like:
- Body: a pod head shaped like an open beak or flytrap facing FORWARD, made of a large pointed upper shell-lid and a
  smaller pointed lower lid; magenta-pink waxy shell with a fine red scale pattern and violet-purple lid edges; the
  mouth gapes forward between them showing a fibrous interior of teal-blue and dark needle-like tendrils.
- Two long ARMS rise high out of the top-sides of the pod and spread up and outward to the left and right, each with
  one joint, ending in a long hooked spike/claw that bends down; olive-brown with a scale pattern, darker tips.
- Two long thin spider LEGS from the underside reach out forward-left and forward-right and bend down to the ground
  with sharp tips; plus one short single spike pointing straight down under the back. Olive green, darker tips.
  No eyes, no other limbs.

Pose (exactly as input 1, the model's pose): standing on its two legs and the rear spike, arms raised and spread,
mouth open; all limbs clear of the body and of each other. Symmetric left/right.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows.
Whole creature inside the frame with generous margins (never crop the arm or leg tips), genuine transparent
background, no floor, no shadow, no text.

Do NOT: add eyes, a face, leaves, extra legs or arms, a stalk, a tail; do not close the mouth; do not change the
colours; do not crop.

## Per-image checks (re-run before selecting)
Open beak mouth facing the correct way; exactly two raised hooked arms, two spider legs and one rear spike; colours as
input 1; the correct side faces the correct image side (03: mouth to image LEFT; 04: mouth to image RIGHT); true
transparent background; 1536x1024; nothing cropped.
