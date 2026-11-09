# Codex brief: HD reference views for the MM9 commoner PeasantM1 (Peasant Human1 MaleA A, skin PeasantM1a) (mm9_peasantm1_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantm1_claude/references_hd/`. Do not edit
any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_a.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter from the character's RIGHT (he faces image right and toward the
   viewer), front, character's LEFT side (faces IMAGE LEFT), back, character's RIGHT side (faces IMAGE RIGHT). Flat
   grey is background. This is the design, costume, POSE, proportions and colour authority. Its faceting, blur, dark
   shading and low resolution are NOT the design.
2. `references_hd/mm9_head_views_a.png` — close renders of the same model's head (front, left profile, three-quarter,
   back): the face and hair authority.
3. `references_hd/mm9_skin_x4_a.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, fabric, knit, leather). Never the design or shape.
4. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, unresized returns, 1536x1024 landscape so the spread arms fit)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the character's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front; the character's RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight back; the character's RIGHT arm on IMAGE RIGHT |
| `03_left.png` | pure 90-degree profile of the character's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the character's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME character, SAME pose, SAME proportions and colours. At most ONE
corrective regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`.
Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs)
and, after run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and
Magic IX character from the supplied renders of its original 3D model, as a 3D modelling and texturing reference.
Not a new design. A credible, fully three-dimensional character with semi-realistic game materials and sharp fine
detail (skin, face, beard, wool weave, knit ribs, stitching, leather), as if a high-quality sculpt of the original
model. ONE complete figure from the top of the head to the soles, centred, generous margins, never cropped.

Pose (identical in all views, the model's bind pose as in input 1): standing upright; the arms held out to the sides
and DOWN as in input 1 (straight, about 35 degrees below horizontal), clear air between the arms and the body; hands
open and flat, palms facing DOWN and slightly back, the four fingers straight and close together with small gaps, the
thumb separated, five fingers on each hand; legs straight and slightly apart with a clear gap between them, feet flat
and pointing forward. Head level, looking straight ahead.

Camera and light: near-orthographic, even soft neutral studio light (brighter than input 1, which is dark), no
dramatic light, no strong cast shadows on the body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; the pose above (arms out
and down, open flat hands with five fingers, legs apart); the correct side faces the correct image side (03: faces
IMAGE LEFT; 04: faces IMAGE RIGHT); whole figure inside the frame with margins; true transparent background; 1536x1024.

## Identity
An ordinary adult human village man (a commoner) in his late thirties, average build, upright.
- Face (input 2): a long face with a straight nose, light blue eyes, fair skin with ruddy cheeks, a slight friendly
  half-smile; a full short dark-brown beard and moustache trimmed close along the jaw; thick wavy dark-brown hair
  covering the ears and falling to the nape of the neck (input 2 profile and back).
- Costume:
  - an olive-brown (khaki/umber) heavy wool jerkin-jacket with long fitted sleeves to the wrists, hip length (to the
    upper thighs), worn OPEN at the front; a wide soft shawl collar that rises behind the neck and folds into lapels on
    the chest (in the back view the collar ends in a point between the shoulder blades); a darker seam line across the
    shoulders; slightly faded, worn wool with a fine weave;
  - under it a loose cream/off-white linen shirt visible down the front, with a laced V neck opening and a dark
    drawstring cord hanging from it; the shirt hem shows below the jacket at the front;
  - dark grey-brown knitted woollen trousers with fine vertical ribs (input 3), loose, tucked into the boots;
  - mid-calf brown leather boots with a folded-down cuff, a small dull brass buckle/clasp on the outer side of the
    cuff, flat soles;
  - bare hands, no gloves, no belt pouch.

## Do NOT
- add a weapon, apron, bag, hat, hood worn up, cloak, belt, gloves or jewellery; change colours (the jacket is
  olive-brown, not red); change the pose; crop; stylise as a cartoon.
