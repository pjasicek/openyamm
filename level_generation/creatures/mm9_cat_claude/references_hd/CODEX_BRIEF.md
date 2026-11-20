# Codex brief: HD reference views for the MM9 cat (mm9_cat_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_cat_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_wolf_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views.png` — renders of the ORIGINAL MM9 low-poly cat with its original skin, five views left
   to right: front three-quarter from the cat's RIGHT (head toward image right), front, the cat's LEFT side (head
   faces IMAGE LEFT), back, the cat's RIGHT side (head faces IMAGE RIGHT). Flat grey is background, not creature.
   This is the design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low resolution are
   NOT the design. Its tail is a stiff stick hanging down to one side: draw a real cat tail instead (see Pose).
2. `references_hd/mm9_head_views.png` — close renders of the same model's head (front, the cat's left profile,
   three-quarter): the FACE authority (white muzzle blaze, orange forehead patch, eyes, pink nose).
3. `references_hd/mm9_skin_x8.png` — the original 128x128 skin texture enlarged 8x, FUR MATERIAL AND COLOUR ONLY
   (the photo of a fluffy calico kitten it was painted from). Never the design, shape or fur length.
4. `references_hd/mm9_top.png` — top view of the same model (head toward image top), proportions only.
5. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the cat's RIGHT, camera slightly above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front (head toward the camera) | 1536x1024 |
| `02_back.png` | back (tail toward the camera) | 1536x1024 |
| `03_left.png` | the cat's LEFT side: head faces IMAGE LEFT (as input 1 view 3) | 1536x1024 |
| `04_right.png` | the cat's RIGHT side: head faces IMAGE RIGHT (as input 1 view 5) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME cat, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"cat" (a town cat) from the supplied renders of its original 3D model, as a 3D modelling/texturing reference. Not a
new design. A beautifully detailed, credible, fully three-dimensional domestic cat with semi-realistic game materials
and sharp fine fur detail, as if a high-quality sculpt of the original model.

Identity: a slim adult domestic short-haired cat, a dark tortoiseshell / calico tabby ("tortie-and-white").
- Fur: mostly very dark brown-black with dark tabby marbling and small rusty orange flecks over the back, flanks,
  head top, ears and tail (as input 1 and the colours of input 3); WHITE chest bib, throat and underside of the neck;
  WHITE muzzle, chin and a white blaze up the middle of the face between the eyes; a small ORANGE patch on the
  forehead above the blaze (input 2); WHITE paws (all four feet white up to the wrist/ankle). Short dense realistic fur,
  NOT long or fluffy (input 3's fluffiness is not the design).
- Head: rounded cat head, two upright triangular ears (dark outside, pale pink inside with a few white ear hairs),
  large yellow-green eyes with vertical dark pupils, small PINK nose, closed mouth, short white whiskers.
- Body: slim, long-legged, level back; four slim legs, front legs straight, hind legs in the cat's natural zig-zag
  (thigh, shin, long hock) with the heel raised; small round paws with soft toes.
- Tail: long and slender, same diameter to a rounded tip, dark with faint rings.

Pose (as input 1, the model's bind pose, standing): standing on all four legs, the four legs separated with air gaps,
all four paws visible and flat on one level; back level; head held forward at back height looking ahead; the TAIL
hanging back and DOWN in a smooth gentle curve from the rump, in the body's midline (not to one side), clear of the
hind legs, its tip above the floor level. Symmetric left/right.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. The whole cat inside the frame with generous margins (never crop the tail tip, ears or paws), genuine
transparent background, no floor, no shadow, no text.

Do NOT: add a collar, a bell, clothes, scars, glowing eyes, extra legs or a second tail; do not open the mouth; do not
make the fur long or fluffy; do not change the colours (no grey tabby, no ginger cat); do not crop.

## Per-image checks (re-run before selecting)
One head with two upright ears, closed mouth, white muzzle blaze, orange forehead patch, yellow-green eyes, pink nose;
exactly four legs with four WHITE paws on the same level; one slender tail hanging back and down in the midline,
clear of the legs; very dark tortoiseshell body with white chest; the correct side faces the correct image side (03:
head to image LEFT; 04: head to image RIGHT); true transparent background; 1536x1024; nothing cropped.

## Run 3 and 4 (2026-10-30): square standing pose

The first set (`superseded_v1/`) shows the cat mid-stride with its head turned; the 3D fit needs a SYMMETRIC standing
pose. Regenerate all five views (same identity, colours, fur, camera and canvas rules as above; use
`superseded_v1/00_three_quarter.png` as an additional identity/colour input, never its pose):
- Pose: the cat STANDING SQUARE, NOT walking: all four legs straight and vertical, the two front paws side by side and
  level, the two hind paws side by side and level (hind legs in the cat's natural zig-zag, heels raised), the left and
  right legs mirror images with a clear air gap between them; back level; head held STRAIGHT forward along the body
  axis (not turned, not tilted), looking ahead; the tail hanging down and back from the rump in the midline in a
  smooth gentle curve, clear of the hind legs, tip above the floor. Strictly left/right symmetric.
- Run 3: `00_three_quarter.png` only, then stop. Run 4: `01_front.png`, `02_back.png`, `03_left.png`, `04_right.png`
  with the selected new `00` as an input. Keep records in a fresh `generation_runs.json` (mention the superseded set)
  and a new `selected_views_review.png`.
