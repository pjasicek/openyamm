# Codex brief: HD reference views for the MM9 human townsman PeasantM3 (skin PeasantM3a) (mm9_peasantm3_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantm3_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_a.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter from the character's RIGHT (he faces image right and toward the
   viewer), front, character's LEFT side (faces IMAGE LEFT), back, character's RIGHT side (faces IMAGE RIGHT). Flat
   grey is background. This is the design, costume, POSE, proportions and colour authority. Its faceting, blur and low
   resolution are NOT the design.
2. `references_hd/mm9_head_views_a.png` — close renders of the same model's head (front, left profile, three-quarter,
   right profile, back): the face and hair authority.
3. `references_hd/mm9_skin_x4_a.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, hair, wool, collar, belt, boots). Never the design or shape.
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
detail (skin, face, hair strands, wool weave, leather grain, stitching), as if a high-quality sculpt of the original
model. ONE complete figure from the top of the head to the soles, centred, generous margins, never cropped.

Pose (identical in all views, the model's bind pose as in input 1): standing upright; the arms held out to the sides
as in input 1 (straight, about 30-35 degrees below horizontal), clear air between the arms and the body; hands open
and flat, palms facing DOWN, the four fingers straight and close together with small gaps, the thumb separated; legs
straight and slightly apart with a clear gap between them, feet flat. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; the pose above (arms out,
open flat hands with five fingers, legs apart); the correct side faces the correct image side (03: faces IMAGE LEFT;
04: faces IMAGE RIGHT); whole figure inside the frame with margins; true transparent background; 1536x1024.

## Identity
An ordinary adult HUMAN townsman about thirty-five years old, average sturdy build, upright, a calm, warm and friendly
expression (relaxed face, mouth closed, a hint of a kind smile in the eyes; never fierce, never cold, never frowning).
- Face and head (input 2): fair skin with a light warm tan; a straight nose; blue eyes, open, with visible irises;
  ONE natural light-brown brow over each eye; a short neatly trimmed full beard and moustache, golden-ginger, along the
  jaw and chin (not long); straight golden-blond hair, side-parted and swept back from the forehead, falling
  straight to just below the ears and the nape of the neck, covering the tops of the ears.
- Costume:
  - a long-sleeved deep madder-red (wine-red) velvet tunic with soft vertical folds, sleeves fitted to the wrists,
    reaching to the upper thighs; a round neckline edged with a band of gold and amber brocade (a woven running
    pattern); a narrow vertical gold brocade band down the centre front from the neckline to the belt; a round silver
    knotwork brooch at the throat; narrow gold brocade cuffs at the wrists;
  - a dark brown leather belt at the waist with an oval brass buckle and a small pointed brass strap end hanging
    below it;
  - below the belt the tunic skirt flares a little and ends in a gold brocade hem band;
  - loose breeches of a brown and golden-ochre woven (fine vertical ribbed / tweed) cloth, bloused at the knee and
    tucked into the boots;
  - brown suede leather boots to just below the knee with a wide turned-down cuff at the top (a small strap and
    buckle on the cuff, as input 3), flat soles. Bare hands.

## Do NOT
- add a weapon, apron, bag, hat, cloak, necklace chain, rings or gloves; change colours (the tunic is wine-red velvet
  with gold brocade, the breeches brown-ochre, the boots brown); make the beard long; give him a fierce, cold or angry
  look; paint a light band between brows and eyes, a second brow line, or heavy red eye rims; change the pose; crop;
  stylise as a cartoon.
