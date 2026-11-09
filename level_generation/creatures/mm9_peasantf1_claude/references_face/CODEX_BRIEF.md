# Codex brief: face repaint of the MM9 townswoman PeasantF1 head texture renders (mm9_peasantf1_claude, face fix)

Scope: image generation/editing only. Write ONLY into `level_generation/creatures/mm9_peasantf1_claude/references_face/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

## What these images are
`in_face_b.png` and `in_face_a.png` are flat, UNLIT (albedo) front orthographic renders of a game character's 3D head texture,
1254x1254. Each output is projected back onto the 3D head pixel for pixel, so the FRAMING MUST NOT MOVE: the face outline, hairline,
hood, nose, eye positions and the mouth's centre line stay on the same pixels.
Review of the inputs: both women have a swollen, sausage-shaped pout (one thick crimson blob far too wide and full for the face) with a
dark smudge under it on the chin; the eyes are round, wide and staring with too much white showing; woman A reads as middle-aged, not as
the white-haired grandmother she is in the original game.

## Inputs (attached, in order)
1. `references_face/in_face_b.png` — woman B render to fix (about 55, grey-brown hair, ochre hood).
2. `references_head/b_01_front.png` — the approved HD portrait of woman B: identity, warm closed-lip smile, eyes and skin to match.
3. `references_face/mm9_face_b.png` — the ORIGINAL 2002 game face of woman B (low resolution): her warm broad smile, crinkled smiling eyes, rosy cheeks.
4. `references_face/in_face_a.png` — woman A render to fix (white hair, white hood).
5. `references_head/a_01_front.png` — the approved HD portrait of woman A (the grandmother): identity and age.
6. `references_face/mm9_face_a.png` — the ORIGINAL game face of woman A: a plump, white-haired grandmother of about 70 with a broad smile.

## Deliverables (1254x1254, same framing as the corresponding input, unresized returns)
| File | From |
|---|---|
| `out_face_b.png` | input 1 repainted, identity from inputs 2 and 3 |
| `out_face_a.png` | input 4 repainted, identity from inputs 5 and 6 |

## What to change (the face only: from just above the brows down to the chin, cheek to cheek)
- MOUTH: a warm, natural CLOSED-LIP smile, lips together, no teeth (the 3D mouth is closed). Normal mouth width: the corners about 10 %
  closer to the centre than the current blob's ends, turned gently UP into the cheeks with soft smile lines. Natural lip thickness (the
  upper lip thinner than the lower; together about two thirds of the current blob's height), natural rose-red lips (B) / paler, thinner
  older lips (A) with a soft edge, no dark outline. The line between the lips on the SAME height as the dark line in the input.
- CHIN: clean skin, no dark smudge or shadow under the lower lip.
- EYES: relaxed, warmly smiling eyes: upper lids lowered a little, lower lids raised slightly by the smile, crow's feet; the iris touches
  the upper lid (no white ring round the iris); irises B hazel/green, A blue-grey; each eye's centre on the SAME pixel as in the input.
  No red rims, no dark sockets.
- CHEEKS: rosy, lifted by the smile.
- WOMAN A ONLY: clearly elderly, about 70: softer, slightly sagging skin, fine wrinkles across the forehead and round the mouth, deep
  crow's feet, a plumper lower face as in input 6. Keep her white hair and white hood unchanged.
- Flat even albedo like the input: no added light, shadows, highlights or reflections.

## Keep EXACTLY as in the input (pixel positions and colours)
Everything outside the face: hood, hair and hairline, ears, neck, collar, the grey background, the face outline. The nose shape and
position. Same image size and framing. No zoom, no shift.

## Checks before saving (one corrective regeneration per output at most)
Overlay the output on its input: hood, hairline, nose tip, eye centres and face outline must coincide within a few pixels; the lip line on
the input's lip-line height; closed lips, no teeth; no white ring round the irises; no chin smudge. Write `generation_runs.json`
(id, prompt, inputs with sha256, output, selected, reason) and a `review.png` with input and output side by side for B and A.
