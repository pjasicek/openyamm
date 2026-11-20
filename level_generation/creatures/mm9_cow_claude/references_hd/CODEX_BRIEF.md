# Codex brief: HD reference views for the MM9 Cow (mm9_cow_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_cow_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_wolf_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly cow with its original black-and-white
   skin, five views left to right: front three-quarter from the cow's RIGHT (head toward image right), front, the
   cow's LEFT side (head faces IMAGE LEFT), back, the cow's RIGHT side (head faces IMAGE RIGHT). Flat grey is
   background, not creature. This is the design, anatomy, POSE, proportions and colour authority. Its faceting, blur
   and low resolution are NOT the design.
2. `references_hd/mm9_skin_tier1_x4.png` — the original 128x128 skin texture enlarged 4x, HIDE MATERIAL AND COLOUR
   ONLY (black patches with soft ragged edges on white, pink udder with teats, pink muzzle, black head with an eye).
   Never the design or shape.
3. `references_hd/mm9_top_tier1.png` — top view of the same model (head toward image top), proportions only.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the cow's RIGHT, camera slightly above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front (head toward the camera) | 1536x1024 |
| `02_back.png` | back (tail toward the camera) | 1536x1024 |
| `03_left.png` | the cow's LEFT side: head faces IMAGE LEFT (as input 1 view 3) | 1536x1024 |
| `04_right.png` | the cow's RIGHT side: head faces IMAGE RIGHT (as input 1 view 5) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME cow, SAME pose, SAME proportions and SAME patch layout. At most ONE
corrective regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected
flag, reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"Cow" farm animal from the supplied renders of its original 3D model, as a 3D modelling/texturing reference. Not a
new design. A beautifully detailed, credible, fully three-dimensional dairy cow with semi-realistic game materials and
sharp fine short-hair detail, as if a high-quality sculpt of the original model.

Identity: a black-and-white Holstein dairy cow, long boxy body, straight back, deep barrel.
- Hide: short smooth hair, WHITE with large irregular BLACK patches with soft, slightly ragged edges, laid out as in
  input 1: black over the shoulders and the front of the back, a big black patch on the middle of the flank and back,
  black on the rump and the top of the tail, white chest, white belly, white lower legs below the knees and hocks.
- Head: black head with a WHITE face blaze down the front, a pink-white hairless MUZZLE with two nostrils, dark eyes,
  NO HORNS (only a small tuft of hair on the poll), two ears sticking out sideways, black outside and pink inside.
  The mouth CLOSED.
- Udder: a pink udder between the hind legs with four short teats.
- Legs: four straight legs, slim lower legs, dark grey-brown cloven hooves.
- Tail: a thin tail hanging straight down from the top of the rump almost to the hocks, ending in a small dark tassel,
  clear of the hind legs.

Pose (exactly as input 1, the model's bind pose): standing square on all four legs, the legs straight and slightly
apart, all four hooves visible and flat on one level, the head held forward at back height, the tail hanging straight
down. Symmetric left/right in shape.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. The whole cow inside the frame with generous margins (never crop the tail, ears, muzzle or hooves), genuine
transparent background, no floor, no shadow, no text.

Do NOT: add horns, a bell, a collar, a halter, ear tags, a saddle, extra legs or a second tail; do not open the mouth;
do not make the hair long or shaggy; do not make it brown; do not crop.

## Per-image checks (re-run before selecting)
One head with two sideways ears and NO horns, closed mouth, pink muzzle, white face blaze; exactly four legs, all four
hooves visible on the same level; one thin tail hanging down with a tassel; a pink udder with teats between the hind
legs; black patches on white as input 1; the correct side faces the correct image side (03: head to image LEFT; 04:
head to image RIGHT); true transparent background; 1536x1024; nothing cropped.
