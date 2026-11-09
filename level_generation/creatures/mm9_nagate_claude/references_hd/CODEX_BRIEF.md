# Codex brief: HD reference views for the MM9 Nagate (giant beetle) (mm9_nagate_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_nagate_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_dfly_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly model with its original skin, five
   views left to right: front three-quarter from the creature's RIGHT, front, creature's LEFT side (head faces image
   LEFT), back, creature's RIGHT side (head faces image RIGHT). Flat grey is background, not creature. This is the
   design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low resolution are NOT the design.
2. `references_hd/mm9_skin_tier1_x4.png` — the original 128x128 skin enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY.
3. `references_hd/mm9_top_tier1.png` — top view of the same model (head toward image bottom), leg layout only.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the creature's RIGHT, camera slightly above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front | 1536x1024 |
| `02_back.png` | back | 1536x1024 |
| `03_left.png` | creature's LEFT side: head faces IMAGE LEFT (as input 1 view 3) | 1536x1024 |
| `04_right.png` | creature's RIGHT side: head faces IMAGE RIGHT (as input 1 view 5) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME creature, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"Nagate" monster from the supplied renders of its original 3D model, as a 3D modelling/texturing reference. Not a
new design. Beautifully detailed, credible fully three-dimensional giant beetle with semi-realistic game materials
and sharp fine detail (glossy chitin, fine pitting, segment seams), as if a high-quality sculpt of the original model.

Identity: a GIANT BEETLE about the size of a large dog, low and wide:
- Body: one large high-domed oval shell (two elytra wing-cases meeting in a straight centre seam along the back),
  smooth rounded dome with soft edges, about 1.4x longer than wide. Glossy near-black chitin; the top of each wing-case
  carries a dense pattern of dark red-brown speckled pebbled texture (as input 2, the two long red panels), fading to
  dark olive-brown and black on the sides and toward the front.
- Head: small, black, glossy, set low at the front under the shell rim; two round glossy dark-red/crimson eyes, one on
  each side of the head; two short curved golden-yellow mandible pincers pointing forward-down at the mouth; two
  thin black segmented antennae rising forward-up from the top of the head.
- Legs: exactly SIX thin black jointed insect legs (three per side: front pair reaching forward, middle pair sideways,
  rear pair backward), each with a raised knee and a lower segment bending down to the ground, ending in a sharp
  golden-yellow claw tip. Legs come out from under the shell, not from its top.

Pose (exactly as input 1, the model's pose): standing on all six legs, body level and clear of the ground, mandibles
slightly open; all legs clear of the body and of each other. Symmetric left/right.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows.
Whole creature inside the frame with generous margins (never crop leg tips or antennae), genuine transparent
background, no floor, no shadow, no text.

Do NOT: add wings, horns, spikes, extra legs, extra eyes, a tail or a stinger; do not open the wing-cases; do not
change the colours; do not crop.

## Per-image checks (re-run before selecting)
Exactly six legs (three per side) with golden claw tips; two red eyes, two golden mandibles, two antennae; domed shell
with a centre seam and the red speckled panels on top; the correct side faces the correct image side (03: head to
image LEFT; 04: head to image RIGHT); true transparent background; 1536x1024; nothing cropped.
