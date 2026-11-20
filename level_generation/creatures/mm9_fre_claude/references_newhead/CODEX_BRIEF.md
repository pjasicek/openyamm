# Codex brief: HD head masters for Fre's NEW 3D head (MM9 row 256, mm9_fre_claude, pass 7)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_fre_claude/references_newhead/`. Do not edit any
other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

## What these images are for
Fre is a goddess in Might and Magic IX: a beautiful, dignified woman of about 35. Her 3D body exists; she gets a NEW 3D HEAD made
by an image-to-3D service from YOUR images: the face and the hair are modelled together as ONE head, which is then cut at the neck
and joined to the body. So each image is a modelling reference of ONE bust (head, neck and the top of the shoulders), not a
painting: clean readable forms, the same person, pose, proportions and framing in all five views.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views.png`: renders of the ORIGINAL MM9 Fre model with her native skin, four views left to right: front,
   her LEFT profile (faces IMAGE LEFT), front three-quarter, back. Flat grey is background. IDENTITY, HAIR, CIRCLET AND COLOUR
   AUTHORITY (low resolution: faceting and dark shading are not the design).
2. `references_head/01_front.png`, 3. `references_head/00_three_quarter.png`, 4. `references_head/02_profile.png`,
   5. `references_head/03_back.png`: earlier approved HD paint-overs of her head (front; three-quarter; her LEFT profile, faces
   IMAGE LEFT; back). FACE, EXPRESSION, SKIN, EYES, HAIR COLOUR AND CIRCLET authority: this is the face the user approved. Their
   head SHAPE was painted over an old 3D shell; use them for the look, not for the outline. IGNORE their feather shawl, necklace,
   jewellery below the chin, and their BRAID.

## Deliverables (unresized returns, 1024x1024 square, plain flat light-grey background (about RGB 190,190,190), no floor, no shadow,
## no text)
| File | View | Notes |
|---|---|---|
| `00_three_quarter.png` | front three-quarter, her face turned toward IMAGE RIGHT exactly as in input 3, camera at eye level or very slightly above | PRIMARY: generate FIRST (run 1) |
| `01_front.png` | straight front, camera at eye level | run 2, with your selected 00 as an extra input |
| `02_back.png` | straight back, camera at eye level | run 2 |
| `03_left.png` | pure profile of HER LEFT side: the face points to IMAGE LEFT, we see her left cheek and left ear area | run 2 |
| `04_right.png` | pure profile of HER RIGHT side: the face points to IMAGE RIGHT, we see her right cheek | run 2 |

Framing, the SAME in all five: a bust from the top of the head to just below the collarbones, centred; the head (crown to chin)
about 45 % of the image height, the top of the hair about 8 % below the image top; the bust cut straight and level across the
upper chest just below the collarbones (like a classical portrait bust), shoulders included, nothing cropped at the sides.

## The bust (identity from inputs 1-5)
- **Pose**: head upright and level, looking straight ahead along the view direction of the pose (no tilt, no turn of the head
  relative to the shoulders), neck straight and vertical, shoulders level and relaxed. Calm, symmetric face.
- **Face**: the approved face of inputs 2-4: a beautiful, kind woman of about 35, calm and warm, a gentle closed-lip smile (lips
  together, corners softly lifted, no teeth, no dark line between the lips); relaxed open eyes with clear green-grey irises and
  clean whites; natural lids, no dark marks under or beside the eyes, no red rims; one thin, softly arched auburn brow per eye;
  warm fair skin with a soft natural blush; natural rose lips; no heavy make-up. A well-formed nose with small soft nostrils on the
  underside only. Even, clean skin over the forehead, temples, cheeks, the sides of the face in front of the hair, the jaw, under
  the chin and the whole neck. Symmetric face.
- **Neck and shoulders**: a long, slender, clearly visible BARE neck from the jaw down to the collarbones, smooth skin, nothing
  around it; bare skin shoulders and upper chest down to the cut, smooth and simple (a portrait bust: no clothing, NO necklace, NO
  collar, NO shawl, NO feathers, NO jewellery below the chin).
- **Hair (one real hairstyle, modelled with the head)**: rich chestnut-auburn (inputs 2-5), sleek and smooth with fine strands,
  parted in the centre and combed back and down close to the head into a neat smooth BOB that COVERS THE EARS COMPLETELY and frames
  the face: it meets the forehead and temples along a clean, soft natural hairline (no hard edge cut into the skin, no strands
  pasted on the cheek), falls past the ears to about the level of the jaw at the sides and ends at the NAPE at the back, the ends
  turned slightly under in a clean, rounded edge that stands just clear of the neck. The volume is moderate and close to the skull
  (sleek, like input 1), not a big fluffy helmet. The neck below the hair is bare skin all round. NO BRAID, NO ponytail, NO bun
  (her braid is a separate 3D piece added later), no loose strands.
- **Circlet**: a thin GOLD CIRCLET across the forehead at the hairline with fine gold filigree ornaments and ONE violet-blue oval
  jewel at the centre of the forehead, running round the head over the hair above the ears and round the back; a narrow gold band
  from the circlet back over the top of the head to the back (input 1, back view; input 5). Low-relief, lying on the hair.

## Render style
Semi-realistic game character reference: sharp fine detail (skin, hair strands, gold filigree). Even, soft, neutral, front-on
studio light: NO dramatic light, NO cast shadows, NO strong shine or specular highlights on skin or hair, no dark vignetting (the
image is turned into a texture). Near-orthographic camera.

## Per-image checks (re-run before selecting)
- the five views show the same person, the same hair shape and the same framing (overlay them: crown, chin and shoulders at the
  same heights);
- ears fully covered by hair in every view; clean soft hairline at the temples and beside the cheeks; the hair edge at the nape
  clean and rounded; no braid;
- bare neck all round, no necklace or collar; bust cut level below the collarbones;
- closed lips, one brow per eye, clean eyes and nose, symmetric face; the circlet's violet jewel at the forehead centre;
- 03_left faces IMAGE LEFT, 04_right faces IMAGE RIGHT, 01/02 straight on; the 00 face turned toward IMAGE RIGHT as input 3;
- 1024x1024, plain light-grey background, nothing cropped.
At most ONE corrective regeneration per view; then select the better and note any residual fault.

## Records
Keep every raw return in `references_newhead/raw/`. Write `references_newhead/generation_runs.json` (id, view, prompt, inputs with
sha256, output path, selected flag, reason, superseded runs, size). After run 2, write a contact sheet
`references_newhead/selected_views_review.png` (all five selected views in one row).

## Do NOT
- add a braid, ponytail, bun, veil, hood, crown, earrings, necklace, collar, shawl, clothing, text, floor or shadow;
- show the ears; leave a gap or a hard line between hair and skin; paste strands onto the cheeks or forehead;
- tilt or turn the head relative to the body; crop the head or the shoulders; change the framing between views;
- open the mouth, show teeth, use a fierce, cold or staring expression, heavy make-up or dark lipstick;
- paint harsh light, shine, specular highlights or strong shadows.
