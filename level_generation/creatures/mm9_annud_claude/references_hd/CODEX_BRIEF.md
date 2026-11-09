# Codex brief: HD reference views for Annud Redeye, MM9 shopkeeper NPC (model PeasantM6, skin PeasantM6b; Isle of Ashes) (mm9_annud_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_annud_claude/references_hd/`. Do not edit any other
file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for
MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter from the character's RIGHT (he/she faces image right and toward the
   viewer), front, character's LEFT side (faces IMAGE LEFT), back, character's RIGHT side (faces IMAGE RIGHT). Flat
   grey is background. This is the design, costume, POSE, proportions and colour authority. Its faceting, blur, dark
   shading and low resolution are NOT the design.
2. `references_hd/mm9_head_views.png` — close renders of the same model's head (front, left profile, three-quarter):
   the face, hair and headwear authority.
3. `references_hd/mm9_skin_x4.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, fabric, trim patterns). Never the design or shape.
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
detail (skin, face, fabric weave, stitching, trims), as if a high-quality sculpt of the original model. ONE complete
figure from the top of the head to the soles, centred, generous margins, never cropped.

Pose (identical in all views, the model's bind pose as in input 1): standing; the arms held out to the sides as in
input 1 (straight, about 15-20 degrees below horizontal), clear air between the arms and the body; hands open and flat,
palms facing DOWN, the four fingers straight and close together with small gaps, the thumb separated; legs straight
and slightly apart with a clear gap between them, feet flat. Head as in input 1.

Camera and light: near-orthographic, even soft neutral studio light (brighter than input 1, which is dark), no
dramatic light, no strong cast shadows on the body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; the pose above (arms out,
open flat hands with five fingers, legs apart); the correct side faces the correct image side (03: faces IMAGE LEFT;
04: faces IMAGE RIGHT); whole figure inside the frame with margins; true transparent background; 1536x1024.

## Identity
Annud Redeye, a sturdy adult human man in his forties, a friendly village shopkeeper, slightly stocky with a modest belly.
- Face (input 2): a broad friendly face, warm smile, brown eyes, a full short dark-brown beard and moustache, tanned
  skin, crow's feet; shoulder-length wavy dark-brown hair falling to the back of the neck (input 2 profile).
- Costume: a long-sleeved reddish-brown (rust/maroon) woven wool tunic to the upper thighs with wide sleeve ends,
  a gold-yellow embroidered geometric trim at the round neck opening (with a short front slit) and at the cuffs;
  a tan rope/cord belt tied at the waist in a knot with hanging ends; dark brown fitted trousers with a fine woven
  texture, wrapped from the ankle to the knee with pale tan cloth leg wraps crossing diagonally; simple brown leather
  shoes. Bare hands.

## Do NOT
- add a weapon, apron, bag, hat, cloak or gloves; change colours; change the pose; crop.
