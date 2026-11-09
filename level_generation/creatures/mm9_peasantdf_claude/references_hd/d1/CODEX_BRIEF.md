# Codex brief: HD reference views for the MM9 dwarf townswoman PeasantDF1 (skin PeasantDF1a) (mm9_peasantdf_claude, design 1)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantdf_claude/references_hd/d1/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_pdf1a.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter (she faces image right and toward the viewer; her far arm is cut by the
   frame edge), front, side facing IMAGE LEFT, back, side facing IMAGE RIGHT. Flat grey is background. This is the design,
   costume, POSE, proportions and colour authority. Its faceting, blur and low resolution are NOT the design.
2. `references_hd/mm9_head_views_pdf1a.png` — close renders of the same model's head (front, profile facing left,
   three-quarter, profile facing right, back): the face and hair authority.
3. `references_hd/mm9_skin_x4_pdf1a.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, blonde hair with braids at the back, blue wool dress, laced bodice with gold trim, white linen blouse
   sleeves, white apron, brown boots). Never the design or shape.
4. (run 2 only) the selected `references_hd/d1/00_three_quarter.png`.

## Deliverables (true transparent background, unresized returns, 1536x1024 landscape so the spread arms fit)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, she faces image right and toward the viewer, camera at chest height slightly above (as input 1 view 1, but with BOTH arms fully inside the frame) |
| `01_front.png` | straight front; the character's RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight back; the character's RIGHT arm on IMAGE RIGHT |
| `03_left.png` | pure 90-degree profile of the character's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the character's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as an
additional input so all views are the SAME character, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/` (inside d1/).
Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs)
and, after run 2, a `selected_views_review.png` contact sheet of the five selected views. A hard-edged opaque figure with
no glow, halo or soft fringe around it.

## Common prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and
Magic IX character from the supplied renders of its original 3D model, as a 3D modelling and texturing reference.
Not a new design. A credible, fully three-dimensional character with semi-realistic game materials and sharp fine
detail (skin, face, hair strands, wool weave, linen folds, lacing, leather grain, stitching), as if a high-quality
sculpt of the original model. ONE complete figure from the top of the head to the soles, centred, generous margins,
never cropped.

Pose (identical in all views, the model's bind pose as in input 1): standing upright; the arms held out to the sides,
straight, about 25 degrees below horizontal (hands at about chest-belly height, NOT a 35-45 degree A-pose), clear air
between the arms and the body; hands open and relaxed, palms facing DOWN, the four fingers straight and close together
with small gaps, the thumb separated; legs straight and slightly apart, feet flat. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; dwarf proportions as
input 1; the pose above (arms out ~25 degrees below horizontal, open hands with five fingers, legs apart); the correct
side faces the correct image side (03: faces IMAGE LEFT; 04: faces IMAGE RIGHT); whole figure inside the frame with
margins; true transparent background; 1536x1024.

## Identity
A DWARF townswoman (commoner) about thirty-five, short and sturdy: broad shoulders, a full bust and a solid waist, a
large head, strong arms, short legs (proportions exactly as input 1; the hem of the skirt falls to the ankles).
- Face and head (input 2): fair warm skin, a pleasant calm face with a WARM, gentle expression (soft relaxed eyes,
  calm brows, a faint closed-mouth smile; never fierce, cold or staring), a straight nose, grey-blue eyes OPEN with
  visible irises, natural soft rose lips (not red lipstick), one fine eyebrow line each.
- Hair: thick straight BLONDE (golden-wheat) hair parted in the centre, falling smoothly to the shoulders in a compact
  rounded volume that covers the ears and frames the face (its outline exactly the rounded, hood-like volume of input
  1); at the back, two plaited braids lie flat in the hair and end at the nape with small silver clasps. Keep the hair
  one smooth solid volume close to the head: no loose flyaway strands, no locks standing off the head.
- Costume (input 1 / 3):
  - a dark-blue wool dress: a fitted sleeveless bodice laced up the front with a dark cord, trimmed along the neckline,
    the front edges and the armholes with a narrow yellow-gold braid; two small round silver-grey brooches on the upper
    bodice; a full ankle-length blue skirt with soft vertical folds;
  - under the bodice a cream-white linen blouse with a wide rounded neckline and short puffed sleeves ending just
    ABOVE THE ELBOW with a narrow band; the forearms are BARE, with a thin silver bracelet at each wrist;
  - a cream-white linen apron from the waist to just below the knee, lying FLAT and close against the front of the
    skirt (a thin layer, no gap under it), tied at the waist;
  - a silver chain necklace with a small ornate pendant on the chest;
  - brown leather ankle boots, flat soles; a little brown legging shows between hem and boot.

## Do NOT
- add a hood, hat, headscarf, cloak, shawl, belt pouch, weapon, tool, basket or gloves; give her long sleeves; let the
  apron or skirt flare away from the body; loose hair strands; change colours (the dress is dark blue, the blouse and
  apron cream-white, the hair blonde); change the pose or the dwarf proportions; crop; stylise as a cartoon; a
  fierce, cold, staring or sad expression.
