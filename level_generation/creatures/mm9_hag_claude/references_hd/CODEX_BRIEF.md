# Codex brief: HD body and head references for the Old Hag (MM9 row 245, "Hjordisa the Hag") (mm9_hag_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_hag_claude/references_hd/` (body views) and
`level_generation/creatures/mm9_hag_claude/v2/references_head/` (head views). Do not edit any other file, do not run builds,
do not call Meshy. Use your built-in image generation tool.

## Why this is special
The Old Hag in Might and Magic IX is the SAME 3D body as Yrsa the Troll (same hunched old woman, same dress cut, same
hood, same face shape), painted with a different skin. Our HD Yrsa model already exists; these images will be used to
REPAINT that existing 3D model as the Hag. So the SHAPE of everything (silhouette, posture, pose, proportions, face
structure: nose, cheekbones, chin, mouth position, hood, braids, dress folds) must stay exactly as in the approved Yrsa HD
masters, and only the COLOURS, MATERIALS, PATTERNS, HAIR COLOUR, FACE PAINTING and the person's look change to the Hag's.
Think of it as the same sculpt, re-painted.

## Inputs (attached, in order)
1. `references_hd/mm9_views.png`: renders of the ORIGINAL MM9 Old Hag model with her original skin, five views left to
   right: front three-quarter (faces image right toward the viewer), front, her LEFT side (faces IMAGE LEFT), back, her
   RIGHT side (faces IMAGE RIGHT). Flat grey is background. COLOUR, MATERIAL AND COSTUME-PAINT authority. Low resolution,
   faceting and dark shading are not the design.
2. `references_hd/mm9_head_views.png`: close renders of the same MM9 Hag head (front, left profile, three-quarter): hair
   colour, face painting, hood colour authority.
3. `references_hd/mm9_skin_x4.png`: her original 256x256 skin texture enlarged 4x: SURFACE MATERIAL, PATTERN AND COLOUR
   ONLY (the golden swirl damask cloth, the navy-black woollen cloth, the dark brown woven cloth, the ginger braids, the
   face). Never the shape.
4. `references_hd/yrsa_shape/01_front.png`, 5. `.../03_left.png`, 6. `.../02_back.png`, 7. `.../04_right.png`: the approved
   HD masters of the SAME 3D body (Yrsa): SHAPE, POSE, PROPORTION, CAMERA AND FRAMING authority for the body views.
8. `v2/references_head/yrsa_shape/01_front.png`, 9. `.../00_three_quarter.png`, 10. `.../02_profile.png`,
   11. `.../03_back.png`: the approved HD head turnaround of the same body: SHAPE, CAMERA AND FRAMING authority for the head
   views (exact face structure, nose, mouth, chin, hood and braid shapes).

## Deliverables (true transparent RGBA background, unresized returns)
Body views, 1536x1024 landscape, into `references_hd/`; each one matches the framing, pose and silhouette of its Yrsa
counterpart (input 4-7) as closely as you can:
| File | View | Shape input |
|---|---|---|
| `01_front.png` | straight front (generate FIRST) | 4 |
| `03_left.png` | pure profile of her LEFT side, faces IMAGE LEFT | 5 |
| `02_back.png` | straight back | 6 |
| `04_right.png` | pure profile of her RIGHT side, faces IMAGE RIGHT | 7 |

Head views, 1254x1254 (or the closest supported square), into `v2/references_head/`; each one matches the framing and head
shape of its Yrsa counterpart (input 8-11):
| File | View | Shape input |
|---|---|---|
| `01_front.png` | straight front bust (generate first of the heads) | 8 |
| `00_three_quarter.png` | front three-quarter bust as input 9 | 9 |
| `02_profile.png` | pure profile of her LEFT side, faces IMAGE LEFT | 10 |
| `03_back.png` | straight back of the head and shoulders | 11 |

Order: body 01, then body 03/02/04 with your selected body 01 as an extra input; then head 01 with the selected body 01 as
an extra input; then head 00/02/03 with the selected head 01 as an extra input. At most ONE corrective regeneration per
view; then select the better and note any residual fault. Keep raw returns in `references_hd/raw/` and
`v2/references_head/raw/`. Write `references_hd/generation_runs.json` (id, view, prompt, inputs with sha256, output path,
selected flag, reason, superseded runs, size) and contact sheets `references_hd/selected_views_review.png` (four body
views) and `v2/references_head/selected_views_review.png` (four head views).

## Common prompt content (adapt per view)
TASK CONTEXT: GAME ASSET RESTORATION. A faithful high-definition repaint reference of an EXISTING Might and Magic IX
character for re-texturing an existing 3D model. Keep EXACTLY the figure, pose, silhouette, proportions, camera and
framing of the matching Yrsa HD master (shape input); change only the paint to the Old Hag's colours and materials from
inputs 1-3. Semi-realistic game materials with sharp fine detail (skin pores and wrinkles, cloth weave, damask swirls,
braid strands). Even soft neutral studio light, brighter than input 1; no dramatic light, no cast shadows (the image is
baked into a texture); genuine transparent background, no floor, no shadow, no text. Whole figure (or whole bust) inside
the frame, never cropped.

## Identity: the Old Hag (Hjordisa), from inputs 1-3
- The same hunched very old village woman as the shape inputs (rounded upper back, head and neck forward and low), a
  calm, warm, kindly old face with a gentle smile (not fierce, not cold, not grotesque).
- Face (input 2, painted onto the SAME face structure as the Yrsa head inputs: same nose, same cheekbones, same chin, same
  mouth position and width): pale, warm, lightly freckled and age-spotted skin, fine wrinkles round the eyes and mouth,
  soft light-brown eyes, thin auburn brows; lips together or barely parted in a warm closed smile, at most a thin hint of
  teeth; a small gold earring.
- Hair: bright GINGER / copper-auburn hair swept back from the forehead under the hood (no white hair anywhere), and the
  two long braids hanging in front of her shoulders are GINGER/copper plaited hair (input 3, the braid strip). NO band of
  beads or teeth across the forehead (the Hag has none; Yrsa's bead band must not appear).
- Hood / headscarf: the same shape as the shape inputs (covering head and back of the head, long pointed tail down the
  back), coloured golden olive-ochre wool with a subtle darker weave (input 3, top-left area round the face).
- Collar necklace of white teeth and gold beads as in inputs 1 and 3 (same shape as Yrsa's); a brass/gold round brooch on
  the chest.
- Dress: the bodice and the upper overskirt / hanging panels are a GOLDEN-OCHRE cloth with a darker brown-orange
  SWIRL DAMASK pattern (input 3, the large swirl areas); the dark brown woven shawl/yoke over the shoulders and chest as in
  input 3 (same as Yrsa's); the long SLEEVES are NAVY-BLACK (very dark blue) wool, widening into bell-shaped cuffs at
  the wrists (input 1 front and side views); the lower skirt to the ankles is the same NAVY-BLACK wool with a faded
  pale embroidered hem border; a braided cord belt at the waist, a cream bead-cord loop across the chest.
- Hands: bony old hands with long fingers, pale warm skin, a gold ring. Feet: dark brown leather boots under the hem.

Per-image checks (re-run before selecting): silhouette and pose match the shape input (overlay it mentally: arms, hood
tail, braids, hem in the same places); colours as inputs 1-3 (ginger hair and braids, golden damask, navy sleeves and
lower skirt); no bead band on the forehead; the correct side faces the correct image side (03 and 02_profile face IMAGE
LEFT; 04 faces IMAGE RIGHT); true transparent background; requested size.

## Do NOT
- change the shape, pose, posture or proportions from the Yrsa HD masters; straighten her back; change the face structure
  (nose, chin, cheekbones) from the head shape inputs; make her young, a monster or a witch with a pointed hat; add a
  staff, broom, basket, cloak or weapon; add a forehead bead band; paint white hair; use a fierce or cold expression;
  add text, background, floor or shadow; crop.
