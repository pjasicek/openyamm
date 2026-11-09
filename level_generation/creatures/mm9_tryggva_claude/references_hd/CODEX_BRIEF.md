# Codex brief: HD reference views for the MM9 unique NPC Tryggva Ravenlocks (skin TRYGGVA) (mm9_tryggva_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_tryggva_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter from the character's RIGHT (he faces image right and toward the
   viewer), front, character's LEFT side (faces IMAGE LEFT), back, character's RIGHT side (faces IMAGE RIGHT). Flat
   grey is background. This is the design, costume, POSE, proportions and colour authority. Its faceting, blur and low
   resolution are NOT the design.
2. `references_hd/mm9_head_views.png` — close renders of the same model's head (three-quarter, front, left profile,
   back, right profile): the face and hair authority.
3. `references_hd/mm9_skin_x4.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, hair, fur, knitted wool, gold embroidery, belt, trousers, boots). Never the design or shape.
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
detail (skin, face, hair strands, fur, knitted wool, gold embroidery, leather grain, stitching), as if a high-quality
sculpt of the original model. ONE complete figure from the top of the head to the soles, centred, generous margins,
never cropped.

Pose (identical in all views, the model's bind pose as in input 1): standing upright; the arms held out to the sides
as in input 1 (straight, about 25-30 degrees below horizontal), clear air between the arms and the body; hands open
and flat, palms facing DOWN, the four fingers straight and close together with small gaps, the thumb separated; legs
straight and slightly apart with a clear gap between them, feet flat. Head level, looking forward. The long hair
hangs straight down the back and the two thin braids hang down in front of the shoulders onto the chest, both clear of
the arms.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; the pose above (arms out,
open flat hands with five fingers, legs apart); the correct side faces the correct image side (03: faces IMAGE LEFT;
04: faces IMAGE RIGHT); whole figure inside the frame with margins; true transparent background; 1536x1024.

## Identity
Tryggva Ravenlocks, a Norse-style jarl: an adult HUMAN man about forty-five, lean and upright, average height.
- Face and head (input 2): fair weathered skin with a warm ruddy tan, a long lean face with high cheekbones, deep
  smile lines and fine wrinkles, a long straight nose, light blue eyes under straight dark brows, a slight confident
  closed-mouth smile; clean-shaven. Long straight raven-black hair with grey-silver sheen highlights, centre-parted,
  falling past the shoulders and down the back to the shoulder blades, tucked behind normal human ears; one thin
  black braid hangs from each temple down in front of each shoulder to the chest, tied with a small dark bead.
- Costume:
  - a long-sleeved, very dark brown (near black-brown) knitted wool tunic with fine vertical rib texture, sleeves
    fitted to the wrists with a darker ribbed cuff band, reaching to the upper thighs;
  - a short shaggy fur mantle (grey-brown wolf fur with pale cream-gold tips) lying over the shoulders and upper
    arms like a capelet, front and back, open at the chest;
  - on the chest a vertical front panel of old-gold cloth with blue, red and gold Celtic knotwork embroidery from the
    neck to the sternum, ending in a point; a cream-gold banded collar at the neck and a thin gold torc necklace;
  - a dark red-brown leather belt at the waist with a brass rectangular buckle and a brass slide keeper;
  - the tunic skirt below the belt falls straight to the upper thighs;
  - dark red-brown and black vertically striped (ribbed) wool trousers, close fitting, tucked into the boots;
  - soft brown suede calf boots with a wide folded-down cuff and a small crossed lacing on the cuff, flat soles.
  - Bare hands (a small gold ring may show on one finger).

## Do NOT
- add a weapon, cloak below the shoulders, hood, helmet, hat, bag or gloves; add a beard or moustache; make the
  ears pointed; change colours (the tunic is near black-brown, the trousers striped red-brown); change the pose;
  crop; stylise as a cartoon.
