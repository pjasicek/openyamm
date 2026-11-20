# Codex brief: HD reference views for the Honk worshipper, female body, MM9 monster (HONKFEMALE.abc, skin HONKF1) (mm9_honkfemale_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_honkfemale_claude/references_hd/`. Do not edit any
other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites
for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views.png`: renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter from the character's RIGHT (she faces image right and toward the
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
A Honk worshipper: a priestess of a harmless goose cult, a slim adult human woman about thirty.
- Face (input 2): a calm, pretty oval face with soft features, a slight closed-mouth smile, blue-grey eyes, thin arched
  brows, light skin. Pale ash-blonde hair parted at the centre, framing the face, under a long plain cream veil.
- Hat (always worn, part of the character, sits level on the head, as tall as the head): a conical helmet-like hat made
  as a sculpted stylised grey-silver goose: a broad ring-shaped brim band in gold with an olive-gold knotwork strip, above
  it the plump grey feathered body of the goose with folded wings embossed on both sides, narrowing upward into a neck,
  and at the very top a small gold goose head with a bead eye and a short pointed gold beak pointing straight FORWARD over
  the face. Rigid, metal and enamel, not cloth.
- Veil: from under the hat brim one smooth cream linen veil falls behind the head and neck down to between the shoulder
  blades, a rounded shape, closed at the back, lying against the back of the neck.
- Two long thin plaited braids of honey-brown hair start at the temples under the hat, hang straight down IN FRONT of
  the shoulders over the upper chest to the level of the sternum, one on each side, clearly separated from the neck with
  a small air gap, thin as a finger.
- Costume: one long, plain, heavy cream linen robe from the neck down to the ankles, closed all round (no slit, no
  opening, one continuous cloth tube around the legs; the legs are not visible), hanging straight in soft vertical
  folds, gently flaring to the hem. Long sleeves widening into large open bell cuffs at the wrists, each trimmed with a
  thin olive-gold woven Celtic knot band. A square yoke collar in the same linen, outlined with an olive-gold Celtic knot
  band (a vertical band down each side of the chest, a horizontal one at the bottom of the chest, a square yoke across the
  back as in input 1), another knot band at the hem. A narrow brown leather belt at the waist with a small bronze buckle.
  A thin silver chain with a round silver knotwork medallion on the upper chest. A small V neckline. Brown leather shoes,
  barely visible under the hem. Bare hands.

## Do NOT
- add a weapon, staff, book, bag, cloak, gloves or a second layer of cloth; change colours; change the pose;
  open the robe at the front or sides; show legs; drop the hat; crop.
