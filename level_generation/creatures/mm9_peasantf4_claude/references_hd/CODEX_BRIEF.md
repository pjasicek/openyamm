# Codex brief: HD body and head references for PeasantF4 skin A (MM9 rows 30/37/42) (mm9_peasantf4_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantf4_claude/references_hd/` (body views)
and `level_generation/creatures/mm9_peasantf4_claude/references_head/` (head views). Do not edit any other file, do not run
builds, do not call Meshy. Use your built-in image generation tool.

## Why this is special
In Might and Magic IX the townswoman "PeasantF4" is the SAME 3D body as "PeasantF1" (same height, same skirt cut, same
pose, same face shape) with a different skin, LONG BELL SLEEVES and a longer hood that falls to the shoulders. Our HD
PeasantF1 model already exists; these images will be used to REPAINT that model (with new sleeves and a new hood added) as
PeasantF4 skin A. So the figure's pose, proportions, skirt and apron cut and face structure (nose, cheekbones, chin, mouth
position) stay as in the approved PeasantF1 HD masters; the COLOURS, MATERIALS, SLEEVES, NECKLINE, HAIR, HOOD and the person
change to PeasantF4 skin A.

## Inputs (attached, in order)
1. `references_hd/mm9_views_a.png`: renders of the ORIGINAL MM9 PeasantF4 model with skin A, five views left to right:
   front three-quarter, front, her LEFT side (faces IMAGE LEFT), back, her RIGHT side (faces IMAGE RIGHT). Flat grey is
   background. COLOUR, MATERIAL, COSTUME AND HOOD authority. Low resolution, faceting and dark shading are not the design.
2. `references_hd/mm9_chest_views_a.png`: close renders of her chest and sleeves (front, three-quarter): the round neckline
   with the embroidered keyhole placket, the embroidered band round each upper arm.
3. `references_hd/mm9_head_views_a.png`: close renders of the same MM9 head (front, left profile, three-quarter): face,
   dark hair parted in the middle, the olive-brown hood.
4. `references_hd/mm9_skin_x4_a.png`: her original 256x256 skin texture enlarged 4x: SURFACE MATERIAL, PATTERN AND COLOUR
   ONLY (olive-green wool dress, embroidery, cream apron, dark skirt, belt, hood cloth). Never the shape.
5. `references_hd/f1_shape/01_front_clean.png`, 6. `.../03_left_clean.png`, 7. `.../02_back_clean.png`,
   8. `.../04_right_clean.png`: the approved HD body masters of the SAME 3D body (PeasantF1): POSE, PROPORTION, CAMERA AND
   FRAMING authority for the body views (ignore their colours; their short puffed sleeves become long sleeves, see Identity).
9. `references_head/f1_shape/b_01_front.png`, 10. `.../b_00_three_quarter.png`, 11. `.../b_02_profile.png`,
   12. `.../b_03_back.png`: the approved HD head turnaround of the same body (PeasantF1): FACE STRUCTURE, CAMERA AND FRAMING
   authority for the head views (exact nose, mouth position, chin and jaw, neck). Her short ochre bonnet is replaced by
   PeasantF4's longer olive-brown hood.

## Deliverables (true transparent RGBA background, unresized returns)
Body views, 1536x1024 landscape, into `references_hd/`; each one matches the framing, pose and silhouette of its PeasantF1
counterpart (inputs 5-8) as closely as you can, apart from the long sleeves:
| File | View | Shape input |
|---|---|---|
| `01_front.png` | straight front (generate FIRST) | 5 |
| `03_left.png` | pure profile of her LEFT side, faces IMAGE LEFT | 6 |
| `02_back.png` | straight back | 7 |
| `04_right.png` | pure profile of her RIGHT side, faces IMAGE RIGHT | 8 |

IMPORTANT for the four BODY views only: these paint the body and dress, so nothing may hide the dress. Show her WITHOUT the
hood: her dark brown hair pinned up in a small neat bun at the back of the head, so the shoulders, the upper back, the
neckline and the chest are fully visible.

Head views, 1254x1254 (or the closest supported square), into `references_head/`; each one matches the framing and face
structure of its PeasantF1 counterpart (inputs 9-12):
| File | View | Shape input |
|---|---|---|
| `01_front.png` | straight front bust (generate first of the heads) | 9 |
| `00_three_quarter.png` | front three-quarter bust as input 10 | 10 |
| `02_profile.png` | pure profile of her LEFT side, faces IMAGE LEFT | 11 |
| `03_back.png` | straight back of the head and shoulders | 12 |
The HEAD views show the full hood (see Identity).

Order: body 01, then body 03/02/04 with your selected body 01 as an extra input; then head 01 with the selected body 01 as an
extra input; then head 00/02/03 with the selected head 01 as an extra input. At most ONE corrective regeneration per view;
then select the better and note any residual fault. Keep raw returns in `references_hd/raw/` and `references_head/raw/`.
Write `references_hd/generation_runs.json` (id, view, prompt, inputs with sha256, output path, selected flag, reason,
superseded runs, size) and contact sheets `references_hd/selected_views_review.png` (four body views) and
`references_head/selected_views_review.png` (four head views).

## Common prompt content (adapt per view)
TASK CONTEXT: GAME ASSET RESTORATION. A faithful high-definition repaint reference of an EXISTING Might and Magic IX
townswoman for re-texturing an existing 3D model. Keep the figure, pose, proportions, camera and framing of the matching
PeasantF1 HD master (shape input); change the paint, sleeves, hair and hood to PeasantF4 skin A from inputs 1-4.
Semi-realistic game materials with sharp fine detail (skin, wool weave, embroidery, linen apron, hood cloth, hair strands).
Even soft neutral studio light; no dramatic light, no cast shadows (the image is baked into a texture); genuine transparent
background, no floor, no shadow, no text. Whole figure (or whole bust) inside the frame, never cropped.

## Identity: PeasantF4 skin A (a townswoman / commoner), from inputs 1-4
- A woman of about 45, calm and warm, a gentle closed-lip smile (lips together, no teeth), relaxed friendly eyes, brown eyes,
  light warm skin with a soft natural blush, natural brows (ONE brow line each), a few soft lines at the eyes; never fierce
  or cold, no heavy make-up, natural lip colour (not lipstick red).
- Hair: dark brown, parted in the middle and drawn back under the hood (a little of it shows at the forehead and temples).
- Hood (head views only): a soft olive-brown / khaki wool hood that covers the top and back of the head and the ears, frames
  the face closely at the hairline and cheeks, and falls straight down to the shoulders at the sides and to the upper back
  behind (input 1 side and back views, input 3); its front edges hang beside the jaw down to the shoulders, leaving the
  front of the neck bare. Plain cloth, a few soft folds, no trim.
- Dress: a long-sleeved olive-green wool dress (tunic cut); a ROUND NECKLINE at the base of the neck with a narrow
  embroidered keyhole placket at the front (brown/cream embroidery, input 2); fitted bodice; a narrow cream belt at the
  waist; LONG SLEEVES: the shoulder and upper arm as PeasantF1's sleeve with an embroidered band round the upper arm above
  the elbow, then the sleeve continues to the wrist, widening below the elbow into a BELL SLEEVE whose open end reaches just
  above the wrist (input 1, input 2); a long cream linen apron over the front of the skirt (as PeasantF1's apron), the skirt
  very dark brown-black to the ankles.
- Bare hands (light warm skin) out of the sleeve openings; brown leather shoes.

Per-image checks (re-run before selecting): pose and proportions match the shape input; colours as inputs 1-4 (olive-green
dress, cream apron, dark skirt, olive-brown hood, dark hair); long bell sleeves to the wrists on both arms; body views have NO
hood; head views have the hood falling to the shoulders; the correct side faces the correct image side (03 and 02_profile
face IMAGE LEFT; 04 faces IMAGE RIGHT); true transparent background; requested size.

## Do NOT
- change the pose or proportions from the PeasantF1 HD masters; change the face structure (nose, chin, cheekbones, mouth
  position); add a hat, crown, cloak, basket, jewellery or weapon; draw a second eyebrow line, heavy make-up, lipstick or red
  eye rims; open the mouth or show teeth; use a fierce, cold or staring expression; add text, background, floor or shadow; crop.
