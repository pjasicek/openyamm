# Codex brief: brow/eye-area and mouth/chin repaint of the MM9 Jarl Sven's face texture render (mm9_sven_claude)

Scope: image generation/editing only. Write ONLY into `level_generation/creatures/mm9_sven_claude/references_face/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

## What this image is
`in_face.png` is a flat, UNLIT (albedo) front orthographic render of a game character's 3D head texture, 1254x1254.
The output will be projected back onto the 3D head pixel for pixel, so the framing must not move at all.
The character is MM9's Sven Forkbeard, a hearty, friendly Norse chieftain who SMILES (see input 2). In the input the face
reads stern and angry, which the user has rejected on earlier characters:
- deep vertical frown furrows between the brows and the brows pulled together and down at their inner ends (knitted);
- heavy horizontal forehead creases;
- pale pink, rather full lips that stand out of the beard;
- a pale grey-white streak running down the middle of the chin beard braid, and pale grey patches in the beard at the
  lower left of the face (they read as smudges).

## Inputs (attached, in order)
1. `references_face/in_face.png` — the albedo render to fix.
2. `references_head/01_front.png` — the approved HD front portrait of this man: the friendly expression, the relaxed
   brows, the eyes, lips and beard colour to match.

## Deliverable
`references_face/out_face.png`: 1254x1254, the SAME framing as input 1 (unresized return).

## What to change (only in these two areas)
A. Brow, eye and forehead area (from the hairline down to the top of the cheekbones, temple to temple):
- the same two brows in the same places and the same brown colour, but RELAXED: no frown, the inner ends level or a
  little raised (a friendly look), a small smooth gap of plain skin between them with no vertical furrows;
- the forehead smooth with at most two faint fine lines, no deep creases;
- the eyes stay exactly where they are, the same size, open, light blue irises, dark pupils, natural lashes; keep the
  friendly laugh lines at the outer corners; no red or pink rims, no dark sockets, no pale band under the brows, no
  second brow line.
B. Mouth and chin (moustache, lips and the beard below them, down to the bottom of the image):
- the lips a natural muted dusky rose a little darker than the cheeks, thinner and partly hidden by the moustache, the
  mouth closed with the corners turned up slightly in a gentle smile; the lips must stay in the same place and must not
  look pushed forward or swollen;
- the beard and the chin braid one even warm brown like the rest of the beard (darker brown strands, a few lighter
  strands), with NO grey-white streak or pale patches.
Flat even albedo like the input: no added light, shadows, highlights or reflections.

## Keep EXACTLY as in the input (pixel positions and colours)
Everything else: the hair, hairline and braids at the sides, the nose, the cheeks, the beard on the jaw sides, the neck,
the black background, the face outline. Same image size and framing. No zoom, no shift, no rotation.

## Checks before saving (one corrective regeneration at most)
Overlay the output on the input: the nose tip, the eye centres, the mouth corners (within a few pixels), the hairline
and the face outline must coincide; exactly one pair of relaxed brows; no furrows between the brows; lips muted and
closed, not swollen; no grey streak on the chin. Write `generation_runs.json` (id, prompt, inputs with sha256, output,
selected, reason) and a `review.png` with input and output side by side.
