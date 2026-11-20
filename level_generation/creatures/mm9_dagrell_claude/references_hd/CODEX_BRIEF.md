# Codex brief: HD reference views for the MM9 Dagrell (spiked bone beast) (mm9_dagrell_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_dagrell_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_dfly_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly model with its original skin, five
   views left to right: front three-quarter from the creature's RIGHT, front, creature's LEFT side (head faces image
   LEFT), back, creature's RIGHT side (head faces image RIGHT). Flat grey is background, not creature. These renders show the model in its MM9 "Stand" clip pose. This is the
   design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low resolution are NOT the design.
2. `references_hd/mm9_skin_tier1_x4.png` — the original 256x256 skin enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (the beige-grey background between the painted parts is unused texture space, not a creature colour).
3. `references_hd/mm9_top_tier1.png` — top view of the same model (head toward image bottom), limb and tail layout only.
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
"Dagrell" monster from the supplied renders of its original 3D model, as a 3D modelling/texturing reference. Not a
new design. Beautifully detailed, credible fully three-dimensional creature with semi-realistic game materials and
sharp fine detail (weathered bone, cracks, polished dark horn), as if a high-quality sculpt of the original model.

Identity: a gaunt SKELETAL reptilian predator made of dark grey-black bone and horn that stands and walks on all four
long thin limbs, about horse length including its tail:
- Head: a long narrow dragon-like skull pointing forward and slightly down, open jaws with rows of sharp pale teeth
  and two long downward fangs, small glowing red eyes under a heavy brow, a few short backward spikes on the skull.
- Neck: thin and bony, running forward and down from the shoulders to the head, which hangs low in front.
- Torso: a narrow horizontal spine with an open RIBCAGE of thin curved ribs visible beneath it; a row of tall sharp
  dorsal SPIKES fanning up and back from the shoulders and spine, plus long spikes sticking backward from the
  elbows, knees and hips (as input 1). Small pelvis bone at the back.
- Two long thin bony FRONT LIMBS (arms) from the shoulders, reaching down to the ground like front legs, each
  ending in a hand of THREE very long thin curved claws resting on the ground.
- Two long thin bony HIND LEGS from the hips, knees bent, each foot with THREE long thin forward-pointing toe claws.
- TAIL: a very long thin segmented bony tail rising from the pelvis up and back in an S-curve (as input 1), ending in
  a flat pointed spear-head blade.
- Colour: dark charcoal grey to black bone with pale grey highlights and faint blue-grey sheen on the limb bones and
  claws (as input 2), red eyes. Not green, not brown, no flesh, no skin, no fur.

Pose (exactly as input 1, the model's pose): standing on all four limbs, back roughly level, head low in front,
tail raised behind; all limbs and claws clear of each other and of the body. Symmetric left/right.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows.
Whole creature inside the frame with generous margins (never crop the tail tip, spikes or claws), genuine transparent
background, no floor, no shadow, no text.

Do NOT: add wings, skin membranes, flesh, armour, fire, glow other than the eyes, extra limbs, extra claws; do not
shorten the tail; do not stand it upright like a human or on two legs; do not change the colours; do not crop.

## Per-image checks (re-run before selecting)
Two arms with three claws each, two legs with three toes each, one long tail with a blade tip, visible ribcage,
dorsal spikes, open toothed jaws, red eyes; standing on all four limbs; the correct side faces the correct image side
(03: head to image LEFT; 04: head to image RIGHT); true transparent background; 1536x1024; nothing cropped
(the raised tail is tall: leave room for it).
