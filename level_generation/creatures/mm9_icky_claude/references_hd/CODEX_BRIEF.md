# Codex brief: HD reference views for the MM9 Flying Icky (mm9_icky_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_icky_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_dfly_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly model with its original skin, five
   views left to right: front three-quarter from the creature's RIGHT (camera above), front, creature's LEFT side
   (head faces image LEFT), back, creature's RIGHT side (head faces image right). Flat grey is background, not
   creature. This is the design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low
   resolution are NOT the design.
2. `references_hd/mm9_head_tier1.png` — close-ups of the same model's head and neck, four views: three-quarter from
   the creature's right, front (looking into the round mouth), left side, three-quarter from the creature's left.
   Head detail authority (round lamprey mouth ring, teeth, horns, small red eyes).
3. `references_hd/mm9_skin_tier1_x4.png` — the original 128x128 skin texture enlarged 4x, SURFACE MATERIAL AND
   COLOUR ONLY (scales, wing membrane veins, mouth ring, small red eye, horn tips). Never the design or shape.
4. `references_hd/mm9_top_tier1.png` — top view of the same model (head toward image top), for the wing outline.
5. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the creature's RIGHT, camera above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front (as input 1 view 2) | 1536x1024 |
| `02_back.png` | back (as input 1 view 4) | 1536x1024 |
| `03_left.png` | creature's LEFT side: head faces IMAGE LEFT (as input 1 view 3) | 1536x1024 |
| `04_right.png` | creature's RIGHT side: head faces IMAGE RIGHT (as input 1 view 5) | 1536x1024 |
| `05_wings_top.png` | top view straight down, head toward image top, both wings fully visible face-on (as input 4) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–05 with the selected 00 as
an additional input so all views are the SAME creature, SAME pose, SAME proportions and colours. At most ONE
corrective regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected
flag, reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic IX "Flying Icky" monster from the supplied renders of its original 3D model, as a 3D modelling/texturing
reference. Not a new design. Beautifully detailed, credible fully three-dimensional creature with semi-realistic game
materials and sharp fine detail (small scales, wing membrane veins, mouth ring), as if a high-quality sculpt of the
original model.

Identity: a small, lean, green flying reptile-worm with two bat wings, a long whip tail and a round lamprey mouth.
- Body: slender lizard-like torso, roughly the length of the head and neck together, sea-green / jade scaly hide with
  darker teal mottling and a paler yellow-green underside. A row of three to four short curved cream spikes with
  orange-red tips runs along the spine between the shoulders.
- Neck and head: a short thick neck that bends DOWN at the front so the head hangs below the body line; the head is a
  blunt tube (no snout, no jaw) ending in a ROUND, wide-open LAMPREY MOUTH: a dark-red fleshy ring lined with SIX
  long pointed ivory teeth set around the rim, a dark red throat inside. The mouth opening faces forward and down.
  Two small red eyes with dark pupils on the sides of the head behind the mouth. Two pointed yellow-green horn-like
  ears sweep up and back from the top of the head; a few small cream spikes on the throat and the back of the head.
- Wings: two large bat wings from the shoulders, wingspan about one and a half body-plus-tail lengths. Each wing is
  a thin opaque sea-green leathery membrane with darker green veins radiating from the arm, a slightly darker
  leading edge along the wing arm, a small cream hook claw at the wrist (pointing forward), and a scalloped, gently
  pointed trailing edge, as in input 4.
- Legs: two small thin hind legs tucked back under the rear of the body, each ending in a small foot with three
  slender cream-and-dark striped talons, pointing BACKWARD along the tail.
- Tail: a long thin whip tail, as long as the rest of the body, straight back, with two small paired side barbs near
  the end and a small flat diamond / spade tip.

Pose (exactly as input 1, the model's bind pose): the creature glides level. The wings are spread FLAT and straight
out to the sides, almost horizontal, not raised, not folded, not overlapping the body. The tail extends straight
back; the legs trail back under the body; the neck bends down at the front with the round mouth facing forward-down.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. Whole creature inside the frame with generous margins (never crop the wing tips or the tail tip), genuine
transparent background, no floor, no shadow, no text.

Do NOT: add arms, front legs, a snout, jaws, a beak, extra wings, a second head, armour or a rider; do not close the
mouth; do not raise or fold the wings; do not change the colours (green body, red mouth ring, ivory teeth); do not
make the wings transparent; do not crop.

## Per-image checks (re-run before selecting)
Two bat wings spread flat; round open lamprey mouth with six ivory teeth on a red ring; two small red eyes; two
swept-back horn ears; spine spikes; two small hind legs with three talons trailing back; long thin tail with a small
spade tip inside the frame; green palette; the correct side faces the correct image side (03: head to image LEFT;
04: head to image RIGHT); true transparent background; 1536x1024.
