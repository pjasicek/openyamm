# Codex brief: eye-area repaint of the MM9 jarl Tryggva Ravenlocks face texture render (mm9_tryggva_claude, face fix)

Scope: image generation/editing only. Write ONLY into `level_generation/creatures/mm9_tryggva_claude/references_face/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

## What this image is
`in_face.png` is a flat, UNLIT (albedo) front orthographic render of a game character's 3D head texture, 1254x1254. The
output will be projected back onto the 3D head pixel for pixel, so the framing must not move. Faults to fix: the two eyes
sit at different heights (his right eye, IMAGE LEFT, centre about x 490 y 432; his left eye, IMAGE RIGHT, about x 838
y 490) and look small and staring (round irises with white all round); the brows are faint and uneven (a diagonal dark
smudge over the image-right eye); a pale skin-coloured notch sits at the top centre between the hair (x 520-920,
y 90-190).

## Inputs (attached, in order)
1. `references_face/in_face.png` — the albedo render to fix.
2. `references_head/01_front.png` — the approved HD front portrait of this man: the eyes, brows, lids and hairline to match.
3. `references_hd/mm9_skin_x4.png` — the original game skin (his face at top left): the eye shape and expression to match.

## Deliverable (1254x1254, same framing as input 1, unresized return)
`out_face.png`: input 1 repainted in the two areas below, identity from input 2.

## What to change
A. Eye area (from just above the brows down to the top of the cheekbones, temple to temple, about y 300-560):
- Both eyes at the SAME height, centre line y 462, placed symmetrically about the nose centre (x about 662): eye centres
  near x 495 and x 830. Same eye size for both, a little larger than input 1 (about 105 px wide), almond shaped.
- Eyes open and relaxed as in input 2: the upper lid covers the top of the light blue iris a little (no white above the
  iris), visible whites at the sides, dark pupils, natural thin dark lashes, soft natural lid crease. No red rims, no
  dark sockets, no bags, no outline or band round the eyes.
- ONE pair of straight, fairly thick dark brown-black brows, level and symmetric, about 50-60 px above each eye, with
  natural soft edges; remove the diagonal smudge. The skin between brows and eyes is ordinary skin of the same tone as
  the forehead and cheeks. Keep fine crow's-feet lines at the outer corners.
B. The top-centre notch (x 520-920, y 80-200): paint it as the dark hair of the centre parting continuing the hair
   beside it (raven-black with a cool grey sheen, strands running down and outward from the parting), so the hairline
   reads as hair framing the forehead from about y 190 down at the sides.

- Flat even albedo like the input: no added light, shadows, highlights or reflections in the eyes.

## Keep EXACTLY as in the input (pixel positions and colours)
Everything else: hair outside the notch, forehead wrinkles above the brows, ears, nose, cheeks, smile lines, mouth, chin,
neck, collar, the black background, the face outline. Same image size and framing. No zoom, no shift.

## Checks before saving (one corrective regeneration at most)
Overlay the output on the input: nose tip, mouth corners, ears and face outline must coincide; both eye centres at y 462
within a few pixels; exactly one pair of brows; no band or outline round the eyes; no red rims; irises visible with the
upper lid covering their top a little. Write `generation_runs.json` (id, prompt, inputs with sha256, output, selected,
reason) and `review.png` with input and output side by side.
