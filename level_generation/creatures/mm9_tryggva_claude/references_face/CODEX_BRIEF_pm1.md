# Codex brief: eye-area repaint of the MM9 commoner PeasantM1 face texture renders (mm9_peasantm1_claude, face fix)

Scope: image generation/editing only. Write ONLY into `level_generation/creatures/mm9_peasantm1_claude/references_face/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

## What these images are
`in_face_a.png` and `in_face_b.png` are flat, UNLIT (albedo) front orthographic renders of a game character's 3D head
texture, 1254x1254. Each output will be projected back onto the 3D head pixel for pixel, so the framing must not move.
The user's review: "looks like he has 2 eyebrows? and like weird eye area?". In both inputs the eye area is wrong: a
lighter, sharply outlined goggle-shaped band between the brows and the eyes whose lower dark edge reads as a second pair
of eyebrows; the eyes are narrow slits; on B the eyes have heavy red rims and look dark and empty.

## Inputs (attached, in order)
1. `references_face/in_face_a.png` — tier A albedo render to fix (bearded dark-haired man).
2. `references_head/01_front.png` — the approved HD front portrait of man A: the eyes, brows and lids to match.
3. `references_face/in_face_b.png` — tier B albedo render to fix (clean-shaven blond man).
4. `references_head_b/01_front.png` — the approved HD front portrait of man B: the eyes, brows and lids to match.

## Deliverables (1254x1254, same framing as the corresponding input, unresized returns)
| File | From |
|---|---|
| `out_face_a.png` | input 1 repainted, eye area only, identity from input 2 |
| `out_face_b.png` | input 3 repainted, eye area only, identity from input 4 |

## What to change (eye area only: from just above the brows down to the top of the cheekbones, temple to temple)
- ONE pair of eyebrows, exactly where the upper, real brows are in the input (A: dark brown, full; B: light brown,
  sparse), with natural soft edges. Remove the second, lower brow-like line completely.
- Remove the lighter goggle-shaped band and its outline: the brow bone and upper eyelids become ordinary skin of the
  same tone as the forehead and cheeks around them, with only a soft natural crease above each eye.
- Eyes open and relaxed as in inputs 2 / 4: visible whites and irises (A light blue-grey, B pale blue), dark pupils,
  natural thin lashes; each eye's centre stays EXACTLY where the eye is in the input (same pixel position, same size
  or up to 15 % taller opening). No red rims, no dark sockets, no bags; B gets plain pale skin round the eyes.
- Flat even albedo like the input: no added light, shadows, highlights or reflections in the eyes.

## Keep EXACTLY as in the input (pixel positions and colours)
Everything outside the eye area: hair and hairline, forehead above the brows, ears, nose, cheeks below the cheekbones,
mouth, beard (A), chin, neck, the grey background, the face outline. Same image size and framing. No zoom, no shift.

## Checks before saving (one corrective regeneration per output at most)
Overlay the output on its input: nose tip, mouth corners, hairline and face outline must coincide; the eye centres must
coincide within a few pixels; exactly one pair of brows; no band or outline; no red rims. Write `generation_runs.json`
(id, prompt, inputs with sha256, output, selected, reason) and a `review.png` with input and output side by side for A
and B.
