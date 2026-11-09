# Codex brief: HD reference views for the Honk worshipper, male body, MM9 monster (HONKMALE.abc, skin HONKM2) (mm9_honkmale_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_honkmale_claude/references_hd/`. Do not edit any
other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites
for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views.png`: renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter from the character's RIGHT (he faces image right and toward the
   viewer), front, character's LEFT side (faces IMAGE LEFT), back, character's RIGHT side (faces IMAGE RIGHT). Flat
   grey is background. This is the design, costume, POSE, proportions and colour authority. Its faceting, blur, dark
   shading and low resolution are NOT the design.
2. `references_hd/mm9_head_views.png`: close renders of the same model's head (front, left profile, three-quarter):
   the face and hair authority. The boxy hair shell is low-poly faceting: read it as real hair.
3. `references_hd/mm9_skin_x4.png`: the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, linen, Celtic knot trim, medallion, belt). Never the design or shape.
4. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, unresized returns, 1536x1024 landscape so the spread arms fit)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the character's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front; the character's RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight back; the character's RIGHT arm on IMAGE RIGHT |
| `03_left.png` | pure 90-degree profile of the character's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the character's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as
an additional input so all views are the SAME character, SAME pose, SAME proportions and colours. At most ONE
corrective regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`.
Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs)
and, after run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT, FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and
Magic IX character from the supplied renders of its original 3D model, as a 3D modelling and texturing reference.
Not a new design. A credible, fully three-dimensional character with semi-realistic game materials and sharp fine
detail (skin, face, linen weave, stitching, knotwork trim), as if a high-quality sculpt of the original model. ONE
complete figure from the top of the head to the soles, centred, generous margins, never cropped.

Pose (identical in all views, the model's bind pose as in input 1): standing, facing straight ahead; the arms held out
to the sides as in input 1 (straight, about 25 degrees below horizontal), clear air between the sleeves and the body;
hands open and flat, palms facing DOWN, the four fingers straight and close together with small gaps, the thumb
separated; feet flat, shoulder width apart, only the shoes showing under the robe hem. Head as in input 1.

Camera and light: near-orthographic, even soft neutral studio light (brighter than input 1, which is dark), no
dramatic light, no strong cast shadows on the body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1-3; the pose above (arms out,
open flat hands with five fingers); the correct side faces the correct image side (03: faces IMAGE LEFT; 04: faces
IMAGE RIGHT); whole figure inside the frame with margins; true transparent background; 1536x1024.

## Identity
A Honk worshipper: a lay priest of a harmless goose cult, a fit adult human man about thirty.
- Face (input 2): a square, friendly, open face with a warm slight smile, green-hazel eyes, heavy brows, a short dark
  brown stubble beard along the jaw and moustache; tanned skin. Thick straight reddish-brown hair parted at the centre,
  falling to the bottom of the neck and hanging behind the ears; bare head, no hat.
- Costume: one long, plain, heavy cream linen robe from the neck down to the ankles, closed all round (no slit, no
  opening, one continuous cloth tube around the legs; the legs are not visible), hanging straight in soft vertical
  folds, very slightly flared to the hem. Long sleeves, narrow at the shoulder, widening gently into open bell cuffs at
  the wrists, each cuff trimmed with a thin olive-gold woven Celtic knot band. An olive-gold Celtic knot band runs across
  the chest and over the shoulders and back as a yoke line (a shallow V across the back, as in input 1), another at the
  hem. A wide dark-brown leather belt at the waist with a square bronze knotwork buckle. A silver chain around the neck
  with a round silver medallion in the middle of the upper chest, embossed with Celtic knotwork. A small V neckline.
  Dark red-brown leather shoes. Bare hands.

## Do NOT
- add a hat, hood, weapon, staff, book, bag, cloak, gloves or a second layer of cloth; change colours; change the pose;
  open the robe at the front or sides; show legs or trousers; crop.
