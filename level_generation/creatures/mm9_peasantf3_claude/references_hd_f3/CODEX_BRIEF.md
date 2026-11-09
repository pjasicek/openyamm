# Codex brief: HD body and head references for PeasantF3 skin A (MM9 rows 35/40) (mm9_peasantf3_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantf3_claude/references_hd_f3/` (body views)
and `level_generation/creatures/mm9_peasantf3_claude/references_head_f3/` (head views). Do not edit any other file, do not run
builds, do not call Meshy. Use your built-in image generation tool.

## Why this is special
In Might and Magic IX the townswoman "PeasantF3" is the SAME 3D body as "PeasantF1" (same height, same dress cut, same
arms, same face shape) with a different skin and a long veil and two braids. Our HD PeasantF1 model already exists; these
images will be used to REPAINT that existing 3D model as PeasantF3 skin A. So the SHAPE of the figure (silhouette, pose,
proportions, bodice, puffed short sleeves, apron and skirt cut, bare forearms, face structure: nose, cheekbones, chin, mouth
position) must stay exactly as in the approved PeasantF1 HD masters; the COLOURS, MATERIALS, NECKLINE PAINT, JEWELLERY,
HAIR, HEADWEAR and the person change to PeasantF3 skin A.

## Inputs (attached, in order)
1. `references_hd_f3/mm9_views_a.png`: renders of the ORIGINAL MM9 PeasantF3 model with skin A, five views left to right:
   front three-quarter, front, her LEFT side (faces IMAGE LEFT), back, her RIGHT side (faces IMAGE RIGHT). Flat grey is
   background. COLOUR, MATERIAL, COSTUME AND HEADWEAR authority. Low resolution, faceting and dark shading are not the design.
2. `references_hd_f3/mm9_head_views_a.png`: close renders of the same MM9 head (front, left profile, three-quarter): face,
   blonde hair, braids, white veil.
3. `references_hd_f3/mm9_skin_x4_a.png`: her original 256x256 skin texture enlarged 4x: SURFACE MATERIAL, PATTERN AND COLOUR
   ONLY (blue linen dress, red lacing, white chemise lace edge, red bead necklace with gold pendant, bead bracelet, blonde
   braid, white veil linen). Never the shape.
4. `references_hd_f3/f1_shape/01_front_clean.png`, 5. `.../03_left_clean.png`, 6. `.../02_back_clean.png`,
   7. `.../04_right_clean.png`: the approved HD body masters of the SAME 3D body (PeasantF1): SHAPE, POSE, PROPORTION, CAMERA
   AND FRAMING authority for the body views.
8. `references_head_f3/f1_shape/b_01_front.png`, 9. `.../b_00_three_quarter.png`, 10. `.../b_02_profile.png`,
   11. `.../b_03_back.png`: the approved HD head turnaround of the same body (PeasantF1): FACE STRUCTURE, CAMERA AND FRAMING
   authority for the head views (exact nose, mouth position, chin and jaw, neck). Her ochre bonnet is replaced by the veil.

## Deliverables (true transparent RGBA background, unresized returns)
Body views, 1536x1024 landscape, into `references_hd_f3/`; each one matches the framing, pose and silhouette of its PeasantF1
counterpart (inputs 4-7) as closely as you can:
| File | View | Shape input |
|---|---|---|
| `01_front.png` | straight front (generate FIRST) | 4 |
| `03_left.png` | pure profile of her LEFT side, faces IMAGE LEFT | 5 |
| `02_back.png` | straight back | 6 |
| `04_right.png` | pure profile of her RIGHT side, faces IMAGE RIGHT | 7 |

IMPORTANT for the four BODY views only: these paint the body and dress, so nothing may hide the dress. Show her WITHOUT the
veil and WITHOUT the braids: her blonde hair pinned up in a small neat bun at the back of the head, so the whole back of the
dress, the shoulders, the neckline and the chest are fully visible.

Head views, 1254x1254 (or the closest supported square), into `references_head_f3/`; each one matches the framing and face
structure of its PeasantF1 counterpart (inputs 8-11):
| File | View | Shape input |
|---|---|---|
| `01_front.png` | straight front bust (generate first of the heads) | 8 |
| `00_three_quarter.png` | front three-quarter bust as input 9 | 9 |
| `02_profile.png` | pure profile of her LEFT side, faces IMAGE LEFT | 10 |
| `03_back.png` | straight back of the head and shoulders | 11 |
The HEAD views show the full headwear: the white veil and the two blonde braids (see Identity).

Order: body 01, then body 03/02/04 with your selected body 01 as an extra input; then head 01 with the selected body 01 as an
extra input; then head 00/02/03 with the selected head 01 as an extra input. At most ONE corrective regeneration per view;
then select the better and note any residual fault. Keep raw returns in `references_hd_f3/raw/` and `references_head_f3/raw/`.
Write `references_hd_f3/generation_runs.json` (id, view, prompt, inputs with sha256, output path, selected flag, reason,
superseded runs, size) and contact sheets `references_hd_f3/selected_views_review.png` (four body views) and
`references_head_f3/selected_views_review.png` (four head views).

## Common prompt content (adapt per view)
TASK CONTEXT: GAME ASSET RESTORATION. A faithful high-definition repaint reference of an EXISTING Might and Magic IX
townswoman for re-texturing an existing 3D model. Keep EXACTLY the figure, pose, silhouette, proportions, camera and framing
of the matching PeasantF1 HD master (shape input); change only the paint, jewellery, hair and headwear to PeasantF3 skin A
from inputs 1-3. Semi-realistic game materials with sharp fine detail (skin, linen weave, lacing, lace edge, beads, braid
strands). Even soft neutral studio light; no dramatic light, no cast shadows (the image is baked into a texture); genuine
transparent background, no floor, no shadow, no text. Whole figure (or whole bust) inside the frame, never cropped.

## Identity: PeasantF3 skin A (a young townswoman / shopkeeper), from inputs 1-3
- A young woman of about 25, calm and warm, a gentle closed-lip smile (lips together, no teeth), relaxed friendly eyes,
  blue-grey eyes, light warm skin with a soft natural blush, thin natural brows (ONE brow line each); never fierce or cold.
- Hair: golden blonde, parted in the middle and drawn back under the veil; two long golden-blonde PLAITED braids start beside
  the temples in front of the ears and hang down in front of the shoulders to the upper chest.
- Veil: a soft white/off-white linen veil covering the top and back of the head, framing the face and hairline like a hood,
  falling down behind the shoulders to the middle of the back (input 1 back and side views), plain, slightly creased.
- Dress (same cut as PeasantF1): a mid-blue linen dress; the fitted bodice laced up the front with a red cord criss-cross
  lacing; a LOW ROUNDED NECKLINE with a thin white lace chemise edge, showing the bare upper chest and collarbones; puffed
  short sleeves in the same blue ending above the elbow with a narrow white chemise cuff; a long white apron over the front
  of the skirt (as PeasantF1's apron), the skirt blue to the ankles.
- Jewellery: a necklace of red/coral beads with a round gold pendant on the upper chest (input 3); a red bead bracelet on her
  wrist; a small gold ring.
- Bare forearms and hands, light warm skin; brown leather shoes.

Per-image checks (re-run before selecting): silhouette and pose match the shape input; colours as inputs 1-3 (blue dress, red
lacing, white apron, white veil, blonde braids); body views have NO veil and NO braids; head views have the veil and both
braids; the correct side faces the correct image side (03 and 02_profile face IMAGE LEFT; 04 faces IMAGE RIGHT); true
transparent background; requested size.

## Do NOT
- change the shape, pose or proportions from the PeasantF1 HD masters; change the face structure (nose, chin, cheekbones,
  mouth position); add a hat, crown, cloak, basket or weapon; draw a second eyebrow line, heavy make-up or red eye rims; open
  the mouth or show teeth; use a fierce or cold expression; add text, background, floor or shadow; crop.
