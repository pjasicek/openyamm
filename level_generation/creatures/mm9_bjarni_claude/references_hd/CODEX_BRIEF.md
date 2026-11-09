# Codex brief: HD reference views for the MM9 Jarl Bjarni Thorvaldssen (skin BJARNI) (mm9_bjarni_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_bjarni_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter from the character's RIGHT (he faces image right and toward the
   viewer), front, character's LEFT side (faces IMAGE LEFT), back, character's RIGHT side (faces IMAGE RIGHT). Flat
   grey is background. This is the design, costume, POSE, proportions and colour authority. Its faceting, blur and low
   resolution are NOT the design.
2. `references_hd/mm9_head_views.png` — close renders of the same model's head (front, left profile, three-quarter,
   right profile, back): the face and hair authority.
3. `references_hd/mm9_skin_x4.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, hair, beard, tunic cloth, yoke, trim, necklace, belt, cuffs, breeches, boots). Never the design or shape.
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
detail (skin, face, beard and hair strands, wool and felt weave, leather grain, stitching, metal), as if a high-quality
sculpt of the original model. ONE complete figure from the top of the head to the soles, centred, generous margins,
never cropped.

Pose (identical in all views, the model's bind pose as in input 1): standing upright; the arms held out to the sides
as in input 1 (straight, about 30 degrees below horizontal), clear air between the arms and the body; hands open
and flat, palms facing DOWN, the four fingers straight and close together with small gaps, the thumb separated; legs
straight and slightly apart with a clear gap between them, feet flat. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; the pose above (arms out,
open flat hands with five fingers, legs apart); the correct side faces the correct image side (03: faces IMAGE LEFT;
04: faces IMAGE RIGHT); whole figure inside the frame with margins; true transparent background; 1536x1024.

## Identity
Bjarni Thorvaldssen, the Jarl (ruler) of Sturmford: a HUMAN Norse nobleman of about fifty-five, sturdy, broad-chested
average build, upright and dignified.
- Face and head (inputs 2, 3): fair weathered skin with ruddy cheeks and nose, a broad strong face with a wide nose,
  deep-set kind eyes under heavy dark brows, fine wrinkles at the eyes and forehead; a FULL short beard and moustache,
  brown streaked with grey, trimmed close to the jaw and chin; thick wavy brown hair (darker at the roots, lighter
  warm brown strands) swept back from the forehead, covering the ears and falling to the nape and the top of the
  shoulders. Mouth closed, calm expression.
- Costume:
  - a long-sleeved mustard-ochre (golden khaki) wool tunic with soft folds, reaching to mid-thigh, its hem edged with a
    narrow rust-red trim band with a fine dotted texture;
  - a wide DARK GREEN felt yoke over the shoulders, front and back: at the front it comes down in two broad pointed
    lapel-like flaps that leave a deep V of tunic cloth between them at the chest; at the back a broad pointed panel
    down to the shoulder blades; every edge of the yoke bordered with the same rust-red dotted trim;
  - a necklace of long curved cream-gold boar tusks / teeth on a cord around the neck, with a round SILVER celtic-knot
    medallion hanging at the centre of the chest;
  - a wide dark red-brown leather belt with silver round studs and a round silver celtic-knot buckle at the front;
  - on each forearm, over the sleeve, a wide dark brown cuff band with fine GOLD celtic scrollwork, edged with gold
    lines, ending at the wrist with a narrow rust-red trim; the sleeve is fitted to the wrist; bare hands;
  - brown wool breeches (each leg with a dark seam strip and small silver studs down the outer side), round olive-green
    leather patches on the knees;
  - shin-high wrappings: dark red-brown leather straps crossed diagonally over cream linen leg wraps, a cream fur trim
    at the ankle, and plain reddish-brown leather shoes with flat soles.

## Do NOT
- add a weapon, cloak, crown, helmet, hat, bag, gloves or rings; drop the necklace, medallion or yoke; change colours
  (the tunic is mustard-ochre, the yoke dark green with rust-red trim); make him young or bald; change the pose; crop;
  stylise as a cartoon.
