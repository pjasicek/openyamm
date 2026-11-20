# Codex brief: face repaint of the MM9 townswomen PeasantF3 A and B head texture renders (mm9_peasantf3_claude)

Scope: image generation/editing only. Write ONLY into `level_generation/creatures/mm9_peasantf3_claude/references_face_f3/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

## What these images are
`in_face_a.png` and `in_face_b.png` are flat, UNLIT (albedo) front orthographic renders of a game character's 3D head texture,
1254x1254. Each output is projected back onto the 3D head pixel for pixel, so the FRAMING MUST NOT MOVE: the face outline, hairline,
white veil, nose, eye positions and the mouth's centre line stay on the same pixels.
Both are the SAME 3D head (two different women of the same game model: A blonde, B dark-haired). Review of the inputs: the mouth is
painted slightly OPEN, with a pink inner plate and a line of teeth between the lips (the 3D mouth is closed, so this reads as a second lip
layer); thin red rims under the eyes. In B the hair was re-coloured crudely: a dark cap with jagged, triangle-shaped edges, while the hair
at the sides is still blonde.

## Inputs (attached, in order)
1. `references_face_f3/in_face_a.png`: woman A render to fix (young, golden-blonde, white veil).
2. `references_head_f3/01_front.png`: the approved HD portrait of woman A: identity, warm closed-lip smile, eyes and skin to match.
3. `references_face_f3/mm9_face_a.png`: the ORIGINAL 2002 game render of woman A (low resolution): her face and blonde hair.
4. `references_face_f3/in_face_b.png`: woman B render to fix (young, DARK-BROWN hair, worn cream veil).
5. `references_face_f3/mm9_face_b.png`: the ORIGINAL game render of woman B: a young woman with dark brown, almost black hair parted in the
   middle, pale skin, grey-blue eyes, natural lips, a calm face.

## Deliverables (1254x1254, same framing as the corresponding input, unresized returns)
| File | From |
|---|---|
| `out_face_a.png` | input 1 repainted, identity from inputs 2 and 3 |
| `out_face_b.png` | input 4 repainted, identity from input 5 (a different person from A) |

## What to change
Both women (the face: from the hairline down to the chin, cheek to cheek):
- MOUTH: a warm, calm CLOSED-LIP smile, lips together, NO teeth and no pink gap between the lips (the 3D mouth is closed). Normal mouth
  width and natural lip thickness (upper lip thinner than the lower), natural rose lips with a soft edge, no dark outline. The line between
  the lips on the SAME height as the centre of the current mouth.
- CHIN: clean skin under the lower lip, no smudge.
- EYES: relaxed, friendly eyes, the iris touching the upper lid, each eye's centre on the SAME pixel as in the input; NO red rims, no dark
  sockets, one brow line each.
- Flat even albedo like the input: no added light, shadows, highlights or reflections.
Woman B only, also the HAIR: dark brown, almost black hair (as input 5), parted in the middle and drawn back to both sides under the veil,
smooth natural strands with soft edges against the skin and the veil, replacing BOTH the jagged dark cap and the blonde strands at the
sides (everything that is hair in input 4 between the veil's edges). Her face is her own (input 5): a calm young woman, slightly narrower
features than A, pale skin, grey-blue eyes, darker brows; warm, not cold or stern.

## Keep EXACTLY as in the input (pixel positions and colours)
The veil (white for A, cream for B) and its edge, the ears region beside the cheeks, the neck, the grey background, the face outline,
the nose shape and position. Same image size and framing. No zoom, no shift. Woman A's hair stays golden blonde as in input 1.

## Checks before saving (one corrective regeneration per output at most)
Overlay the output on its input: veil edge, hairline, nose tip, eye centres and face outline must coincide within a few pixels; closed lips,
no teeth; no red eye rims; B's hair fully dark brown with soft edges. Write `generation_runs.json` (id, prompt, inputs with sha256, output,
selected, reason) and a `review.png` with input and output side by side for A and B.
