# Codex brief: HD reference views for the MM9 human townsman PeasantM7 (skin PeasantM7b) (mm9_peasantm7_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantm7_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_b.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter from the character's RIGHT (he faces image right and toward the
   viewer), front, character's LEFT side (faces IMAGE LEFT), back, character's RIGHT side (faces IMAGE RIGHT). Flat
   grey is background. This is the design, costume, POSE, proportions and colour authority. Its faceting, blur and low
   resolution are NOT the design.
2. `references_hd/mm9_head_views_b.png` — close renders of the same model's head (front, left profile, three-quarter,
   right profile, back): the face and hair authority.
3. `references_hd/mm9_skin_x4_b.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
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
An ordinary adult HUMAN townsman (commoner) about thirty years old, lean average build, upright.
- Face and head (input 2): fair skin with a warm tan, an angular lean face with defined cheekbones, a straight nose,
  light blue eyes, dark brows, a serious calm expression with the mouth closed; light dark stubble on the chin and
  jaw (not a full beard); thick short wavy hair, dark chestnut brown with reddish-brown highlights at the back, a
  side parting, swept back from the forehead, covering the tops of the ears and falling to the nape of the neck.
- Costume:
  - a long-sleeved olive-green / khaki-green wool tunic with soft folds, sleeves fitted to the wrists, reaching to the
    upper thighs; a wide slate-blue (grey-blue) cloth collar yoke lying flat over the shoulders front and back with a
    softly scalloped lower edge; a V-shaped front neck opening edged in the same slate blue and laced across with dark
    cords, a glimpse of cream linen undershirt at the neck;
  - a dark brown leather belt at the waist with a plain brass buckle;
  - below the belt the tunic skirt flares a little and ends in a slate-blue hem band (the khaki cloth meets the blue
    band with a slightly jagged edge, as input 3);
  - dark brown (near black-brown) wool breeches, loose, tucked into the boots below the knee;
  - tan-brown leather calf boots with a wide folded-down cuff and a small crossed strap with a brass buckle on the
    cuff, flat soles. Bare hands.

## Do NOT
- add a weapon, apron, bag, hat, cloak, jewellery, necklace or gloves; add a full beard; change colours (the tunic is
  olive-green, the collar slate blue); change the pose; crop; stylise as a cartoon.
