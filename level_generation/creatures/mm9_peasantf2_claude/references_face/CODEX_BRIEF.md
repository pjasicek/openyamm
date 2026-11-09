# Codex brief: face repaint of the MM9 human townswoman PeasantF2 head texture renders (mm9_peasantf2_claude, face fix)

Scope: image generation/editing only. Write ONLY into `level_generation/creatures/mm9_peasantf2_claude/references_face/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

## What these images are
`in_face_a.png` and `in_face_b.png` are flat, UNLIT (albedo) front orthographic renders of a game character's 3D head texture,
1254x1254. Each output is projected back onto the 3D head pixel for pixel, so the FRAMING MUST NOT MOVE: the face outline, hairline,
hair, braids, nose, eye positions and the mouth's centre line stay on the same pixels.
Review of the inputs: under the nose the nostrils read as a dark smudge with a dark V; between the nose and the upper lip there are small
light specks; the lips are lipstick red and slightly parted with a pale band between them; the eyes are a little too round and wide
(too much white above the irises); woman A's forehead carries pale hair-like streaks.

## Inputs (attached, in order)
1. `references_face/in_face_a.png` — woman A render to fix (about 30, golden-blonde hair, light freckles).
2. `references_head/a_01_front.png` — the approved HD portrait of woman A: identity, warm closed-lip smile, eyes and skin to match.
3. `references_face/mm9_face_a.png` — the ORIGINAL 2002 game face of woman A (low resolution): her warm friendly smile.
4. `references_face/in_face_b.png` — woman B render to fix (about 45, copper-red hair).
5. `references_head/b_01_front.png` — the approved HD portrait of woman B: identity and age.
6. `references_face/mm9_face_b.png` — the ORIGINAL game face of woman B: a kind woman with a warm smile.

## Deliverables (1254x1254, same framing as the corresponding input, unresized returns)
| File | From |
|---|---|
| `out_face_a.png` | input 1 repainted, identity from inputs 2 and 3 |
| `out_face_b.png` | input 4 repainted, identity from inputs 5 and 6 |

## What to change (the face only: from just above the brows down to the chin, cheek to cheek)
- NOSE: keep its outline and position exactly; clean skin on the tip and the sides; two small, soft, rounded nostrils in a cool skin
  shadow (not brown, not red, no dark triangle or V between them); clean skin between the nose and the upper lip (a soft philtrum).
- MOUTH: a calm, warm, natural CLOSED-LIP smile, lips together, no teeth, no pout. Natural lip colour (soft rose for A, paler dusty rose
  for B; NOT lipstick red), a soft edge, no dark outline. The line between the lips on the SAME height as in the input, the same width.
- EYES: calm and warm, relaxed: the upper lid sits a little lower so it just covers the top of the iris (no white above the iris); lashes
  as in the input; irises green-grey (A) / grey-blue (B); each eye's centre on the SAME pixel as in the input. No red rims, no dark sockets.
- WOMAN A: light even freckles on the nose and cheeks; a clean smooth forehead (no streaks).
- WOMAN B: about 45: soft fine lines at the eyes, kind expression. Not cold, not fierce.
- Flat even albedo like the input: no added light, shadows, highlights or reflections.

## Keep EXACTLY as in the input (pixel positions and colours)
Everything outside the face: hair, braid, hairline, neck, the grey background, the face outline. The brows' shape and position. Same
image size and framing. No zoom, no shift.

## Checks before saving (one corrective regeneration per output at most)
Overlay the output on its input: hairline, brows, nose tip, eye centres and face outline must coincide within a few pixels; the lip line
on the input's lip-line height; closed lips, no teeth; no white above the irises; no dark nostril triangle; no specks under the nose.
Write `generation_runs.json` (id, prompt, inputs with sha256, output, selected, reason) and a `review.png` with input and output side by
side for A and B.
