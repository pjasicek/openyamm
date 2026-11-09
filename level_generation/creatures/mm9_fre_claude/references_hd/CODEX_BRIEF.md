# Codex brief: HD body and head references for Fre (MM9 row 256) (mm9_fre_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_fre_claude/references_hd/` (body views) and
`level_generation/creatures/mm9_fre_claude/references_head/` (head views). Do not edit any other file, do not run builds, do not
call Meshy. Use your built-in image generation tool.

## Why this is special
In Might and Magic IX, Fre is a goddess who stands in the Hall of the Gods: a beautiful, dignified woman of about 35 in a rich Norse
costume. Her 3D body is the SAME body as the townswoman "PeasantF4" (same height, pose, skirt cut, long bell sleeves), whose HD model
already exists. These images are used to REPAINT that 3D model as Fre. So the body views keep the pose, proportions, camera and
framing of the PeasantF4 HD masters (inputs 5-8), and the head views keep the EXACT framing and shapes of the renders of our 3D head
(inputs 9-12); the COLOURS, MATERIALS, ORNAMENTS and the person change to Fre (inputs 1-4).

## Inputs (attached, in order)
1. `references_hd/mm9_views.png`: renders of the ORIGINAL MM9 Fre model with her skin, five views left to right: front three-quarter,
   front, her LEFT side (faces IMAGE LEFT), back, her RIGHT side (faces IMAGE RIGHT). Flat grey is background. COLOUR, MATERIAL,
   COSTUME, ORNAMENT AND HAIR authority. Low resolution; faceting and dark shading are not the design.
2. `references_hd/mm9_chest_views.png`: close renders of her chest (front, three-quarter): the cream feather shawl over the shoulders,
   the gold necklace, the two round dark-bronze brooches, the gold bead festoons, the brown-gold brocade front panel, the gold belt.
3. `references_hd/mm9_head_views.png`: close renders of the MM9 head (front, left profile, three-quarter, back): her face, the sleek
   chestnut-auburn hair that covers the ears and frames the face down to the jaw, the gold circlet with a violet-blue jewel on the
   forehead, a gold band over the crown, and one gold-bound braid hanging from the nape down the back.
4. `references_hd/mm9_skin_x4.png`: her original 256x256 skin texture enlarged 4x: SURFACE MATERIAL, PATTERN AND COLOUR ONLY (the
   face, hair, feather shawl, red patterned dress, brocade panel, gold ornaments, golden cuff, ear, hand). Never the shape.
5. `references_hd/f4_shape/01_front_clean.png`, 6. `.../03_left_clean.png`, 7. `.../02_back_clean.png`, 8. `.../04_right_clean.png`:
   HD body masters of the SAME 3D body (PeasantF4): POSE, PROPORTION, SLEEVE SHAPE, CAMERA AND FRAMING authority for the body views
   (ignore their colours, costume and face).
9. `references_head/cur_front.png`, 10. `cur_q34.png` (front three-quarter from her right, from slightly above), 11. `cur_left.png`
   (her LEFT profile, faces IMAGE LEFT), 12. `cur_back.png`: plain grey clay renders of OUR 3D head and shoulders: SHAPE AND
   FRAMING authority for the head views. The smooth shell round the head (rounded over the crown, covering the ears, framing the face
   at the forehead and cheeks and falling to the jaw and the nape) is her HAIR; the tube hanging from the nape down the back is her
   BRAID.

## Deliverables (unresized returns)
Body views, 1536x1024 landscape, true transparent RGBA background, into `references_hd/`; each matches the framing, pose and
silhouette of its PeasantF4 counterpart (inputs 5-8) as closely as you can:
| File | View | Shape input |
|---|---|---|
| `01_front.png` | straight front (generate FIRST) | 5 |
| `03_left.png` | pure profile of her LEFT side, faces IMAGE LEFT | 6 |
| `02_back.png` | straight back | 7 |
| `04_right.png` | pure profile of her RIGHT side, faces IMAGE RIGHT | 8 |
For the four BODY views only: these paint the dress, so nothing may hide it: draw her hair as in PeasantF4's masters, pinned up in a
small neat chestnut bun at the back of the head, with NO braid, so the shoulders, upper back, neckline and chest are fully visible.

Head views, 1254x1254, plain flat light-grey background exactly like the inputs, into `references_head/`; each is a PAINT-OVER of its
input render: keep the EXACT framing, silhouette and feature positions of the input (the same pixels for the outline of the hair
shell and the braid, the eyes, the nose, the mouth, the chin, the neck and the shoulders). Only the paint changes.
| File | From input |
|---|---|
| `01_front.png` | 9 (generate first of the heads, with your selected body 01 as an extra input) |
| `00_three_quarter.png` | 10 |
| `02_profile.png` | 11 |
| `03_back.png` | 12 |

Order: body 01, then body 03/02/04 with your selected body 01 as an extra input; then head 01, then head 00/02/03 with your selected
head 01 as an extra input. At most ONE corrective regeneration per view; then select the better and note any residual fault. Keep raw
returns in `references_hd/raw/` and `references_head/raw/`. Write `references_hd/generation_runs.json` (id, view, prompt, inputs with
sha256, output path, selected flag, reason, superseded runs, size) and contact sheets `references_hd/selected_views_review.png` (four
body views) and `references_head/selected_views_review.png` (four head views beside their input renders).

## Common prompt content (adapt per view)
TASK CONTEXT: GAME ASSET RESTORATION. A faithful high-definition repaint reference of an EXISTING Might and Magic IX character for
re-texturing an existing 3D model. Keep the figure, pose, proportions, camera and framing of the shape input; paint Fre from inputs 1-4.
Semi-realistic game materials with sharp fine detail (skin, hair strands, feathers, wool weave, brocade pattern, gold metalwork).
Even soft neutral studio light; no dramatic light, no cast shadows, no shine or specular highlights (the image is baked into a
texture). Body views: genuine transparent background, no floor, no shadow, no text, whole figure inside the frame, never cropped.

## Identity: Fre, from inputs 1-4
- Face: a beautiful, kind woman of about 35, calm and warm, a gentle closed-lip smile (lips together, corners softly lifted, no teeth,
  no dark line or shadow between or above the lips); relaxed open eyes with clear green-grey irises and clean whites; natural lids with
  NO dark marks, wedges or shadows under or beside the eyes and no red rims; ONE thin natural, softly arched brow per eye; warm fair
  skin with a soft natural blush on the cheeks; natural rose lips (not dark lipstick); no heavy make-up. Even, clean skin over the face,
  cheeks, chin, jaw, under the chin and the neck (no blotches, no patches in front of the ears). The NOSE is painted exactly on the
  render's nose: the same tip, plain skin with soft shading, two small soft nostrils on the underside only, no dark blob.
- Hair (head views): rich chestnut-auburn, sleek and smooth with fine strands, combed back from a centre parting over the whole shell
  (it covers the ears and frames the face down to the jaw, falling to the nape); a thin GOLD CIRCLET across the forehead at the
  hairline with small gold filigree ornaments and one violet-blue jewel at the centre, continuing round the head above the ears; a
  narrow gold band from the circlet back over the crown (input 3, back view). The BRAID: the same chestnut-auburn hair, plaited, bound
  with gold bands every few centimetres, ending in a small tuft.
- Dress: a long-sleeved RED wool dress with a fine darker red swirl pattern (input 4), long to the ankles; the sleeves fitted on the
  upper arm and widening below the elbow into the bell shape of input 5, each ending in a wide GOLDEN embroidered cuff band (gold
  brocade, input 4) above the wrist.
- Over it a Norse apron-dress front panel of BROWN-AND-GOLD BROCADE (ornate scroll pattern, input 2/4) on the front of the bodice and
  hanging as an apron down the front of the skirt to below the knees; a wide ornate GOLD BELT at the waist with a round gold medallion
  buckle at the centre (input 2).
- A soft CREAM-WHITE FEATHER SHAWL over the shoulders and upper chest and upper back (a yoke of short soft feathers, input 2 and the
  back view of input 1); a gold necklace with a gold pendant at the throat; two ROUND dark-bronze brooches with a raised spiral pattern
  on the chest where the brocade panel's straps meet the shawl; three or four festoons of small gold beads hanging between the brooches.
- Bare hands (warm fair skin) out of the sleeve openings; soft brown leather shoes.

## Per-image checks (re-run before selecting)
Body: pose and proportions match the shape input; red dress, brocade front panel, gold belt, feather shawl, brooches and bead festoons,
golden cuffs, both arms; the correct side faces the correct image side (03 faces IMAGE LEFT; 04 faces IMAGE RIGHT); true transparent
background; 1536x1024. Head: overlay each output on its input render: the hair outline, the braid, eyes, nose tip and mouth within a few
pixels; clean eyes and nose, closed lips, one brow per eye, no blotches; the circlet at the hairline; grey background like the input.

## Do NOT
- change the pose or proportions; change the head, hair-shell, braid, nose, lip, chin or neck shapes in the head views; move, resize,
  crop or re-frame a head view; add a crown, veil, cloak, wings, weapon, text, floor or shadow; draw a second eyebrow line, heavy
  make-up, dark lipstick or red eye rims; open the mouth or show teeth; use a fierce, cold or staring expression; paint harsh light,
  shine or specular highlights.
