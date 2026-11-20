# Codex brief: eye, brow and mouth repaint of the MM9 dwarf PeasantDM2's face texture renders (mm9_peasantdm2_claude)

Scope: image generation/editing only. Write ONLY into `level_generation/creatures/mm9_peasantdm2_claude/references_face/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

## What these images are
`in_face_a.png` and `in_face_b.png` are flat, UNLIT (albedo) front orthographic renders of a game character's 3D head
texture, 1254x1254, for two variants (A and B) of the same old dwarf townsman from Might and Magic IX. Each output is projected
back onto the 3D head pixel for pixel, so THE FRAMING MUST NOT MOVE AT ALL: the eyes, nose, mouth, beard, hair and face outline
stay exactly where they are. The black background is not part of the character.

The original MM9 dwarf (inputs 3 and 6, low-resolution renders of the original game model) has a KIND, WARM, SMILING face:
eyes open and crinkled with laugh lines, light blue irises clearly visible, relaxed brows, a broad gentle smile. Our renders
read stern and tired, which the user has rejected on similar characters:
- the eyes are small slits sunk under heavy brows, with a dark shadow band between brow and eye, the irises barely showing;
- the brows are pulled down and together (frowning), with dark furrows between and above them;
- the mouth is a thin flat line (A) or a pouting pink patch (B), the corners turned down;
- small flat orange patches and dark specks on the cheeks beside the nose and under the eyes (texture faults);
- (B) the irises are near black.

## Inputs (attached, in order)
1. `references_face/in_face_a.png` — variant A render to fix.
2. `references_head/01_front.png` — approved HD front portrait of variant A (identity, beard, hair, skin to keep).
3. `references_face/mm9_face_a.png` — the ORIGINAL MM9 variant A face (expression authority; its blur is not the design).
4. `references_face/in_face_b.png` — variant B render to fix.
5. `references_head_b/01_front.png` — approved HD front portrait of variant B.
6. `references_face/mm9_face_b.png` — the ORIGINAL MM9 variant B face (expression authority).

## Deliverables
`references_face/out_face_a.png` (from input 1) and `references_face/out_face_b.png` (from input 4): 1254x1254 each, the SAME
framing as their input (unresized returns). Keep raw returns in `references_face/raw/`.

## What to change (only inside the face: brows, eyes, cheeks beside the nose, moustache-mouth area)
A. Brows and eyes (from just above the brows down to the top of the cheekbones, temple to temple):
- the same white bushy brows in the same places, RELAXED and slightly raised at the inner ends (kind, not frowning); smooth
  skin between them, no vertical furrows, no dark band under the brows;
- the eyes centred exactly where the input's eyes are, OPEN and smiling: visible upper lids, light blue irises (BOTH variants:
  light grey-blue for B, not dark) with dark pupils and a small white of the eye showing, crinkled laugh lines at the outer
  corners as in input 3/6; no red or pink rims, no dark sockets, no second brow line, no pale band around the eyes.
B. Cheeks beside the nose: plain warm skin of the surrounding tone; remove the flat orange patches and dark specks.
C. Mouth (inside the moustache and beard): a warm closed-mouth SMILE, the corners turned up, the lips a muted dusky rose a
   little darker than the cheeks, thin and partly hidden by the white moustache; the mouth stays exactly where it is and must
   not look swollen or pushed forward.
Flat even albedo like the input: no added light, shadows, highlights or reflections. Skin the same warm tone as the input's
forehead and cheeks.

## Keep EXACTLY as in the input (pixel positions and colours)
Everything else: hair, braids, headband (B), ears, nose shape, forehead and scalp, the beard and moustache outline, the
neck and tunic, the black background, the face outline. Same image size and framing. No zoom, no shift, no rotation.

## Checks before saving (one corrective regeneration per variant at most)
Overlay each output on its input: the nose tip, eye centres, mouth corners (within a few pixels), the hairline/headband and
the face outline must coincide; one pair of relaxed brows; eyes open with light blue irises; a gentle smile; no orange patches
on the cheeks. Write `generation_runs.json` (id, prompt, inputs with sha256, output, selected, reason) and `review.png` with
inputs and outputs side by side.
