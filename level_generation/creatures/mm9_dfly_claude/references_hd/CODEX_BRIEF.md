# Codex brief: HD reference views for the MM9 Dragonfly Mite (serpentine dragonfly) (mm9_dfly_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_dfly_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm6_bld_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly model with its original skin, five
   views left to right: front three-quarter from the creature's RIGHT, front, creature's LEFT side (head faces image
   left), back, creature's RIGHT side (head faces image right). Flat grey is background, not creature. This is the
   design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low resolution are NOT the design.
2. `references_hd/mm9_skin_tier1_x4.png` — the original 128x128 skin texture enlarged 4x, SURFACE MATERIAL AND
   COLOUR ONLY (scale pattern, belly plates, wing spots). Never the design or shape.
3. `references_hd/mm9_top_tier1.png` — top view of the same model (head toward image top), for the wing outline.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the creature's RIGHT, camera slightly above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front | 1536x1024 |
| `02_back.png` | back | 1536x1024 |
| `03_left.png` | creature's LEFT side: head faces IMAGE LEFT (as input 1 view 3) | 1536x1024 |
| `04_right.png` | creature's RIGHT side: head faces IMAGE RIGHT (as input 1 view 5) | 1536x1024 |
| `05_wings_top.png` | top view straight down, head toward image top, all four wings fully visible face-on (as input 3) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–05 with the selected 00 as
an additional input so all views are the SAME creature, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"Dragonfly Mite" monster from the supplied renders of its original 3D model, as a 3D modelling/texturing reference.
Not a new design. Beautifully detailed, credible fully three-dimensional creature with semi-realistic game materials
and sharp fine detail (small scales, belly plates, wing veins), as if a high-quality sculpt of the original model.

Identity: a SERPENTINE dragonfly — a long, slender snake-like body with NO legs and NO arms, and four dragonfly wings.
- Body: slender serpent, roughly even thickness through the upper body, then tapering steadily into a long thin tail
  ending in a sharp needle tip (pale bone/green-tinted spike). Cobalt / steel-blue scaly hide with darker blue mottled
  small scales; a violet-purple segmented belly stripe (transverse plates) runs down the FRONT (ventral side).
- Head: snake-like, elongated with a long tapered snout; two LARGE glossy BLACK bulbous compound insect eyes sitting
  high on the sides of the head, behind the snout; the mouth OPEN with rows of long thin white needle teeth on the upper
  and lower jaw and a pink interior. No horns, no ears, no antennae.
- Wings: FOUR long narrow leaf/blade-shaped dragonfly wings at the top of the back just behind the head: a long FRONT
  pair spreading out to the sides, and a shorter REAR pair angled backward. Opaque iridescent violet/lavender membrane
  with pink sheen, fine darker veins, scattered dark elongated spots, darker leading edge. Thin flat membranes.

Pose (exactly as input 1, the model's bind pose): the creature hovers UPRIGHT. The neck arches up and forward with
the head pointing forward and slightly down; the body hangs down in a smooth S-curve (seen from the side: neck curves
back, the body curves forward, then the tail curves back and hangs down ending in the needle tip). From the front the
body is a straight vertical line. All four wings are raised in a wide V above the shoulders, spread, not folded, not
overlapping the body.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. Whole creature inside the frame with generous margins (never crop wing tips or the tail tip), genuine transparent
background, no floor, no shadow, no text.

Do NOT: add legs, arms, claws, horns, antennae, a second head, armour or a rider; do not close the mouth; do not
straighten the S-curve; do not change the colours; do not make the wings transparent glass; do not crop.

## Per-image checks (re-run before selecting)
No legs; two big black eyes; open mouth with white needle teeth; slender blue body with violet belly plates on the
ventral side; four wings (long front pair, shorter rear pair) raised in a V; S-curve as input 1; needle tail tip
inside the frame; the correct side faces the correct image side (03: head to image LEFT; 04: head to image RIGHT);
true transparent background; 1536x1024.
