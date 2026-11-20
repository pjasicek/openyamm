# Codex brief: face repaint of the MM9 townswoman PeasantF5 head texture renders (mm9_peasantf5_claude, face fix)

Scope: image generation/editing only. Write ONLY into `level_generation/creatures/mm9_peasantf5_claude/references_face/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

## What these images are
`in_face_b.png` and `in_face_a.png` are flat, UNLIT (albedo) front orthographic renders of a game character's 3D head texture,
1254x1254, a woman in a cream pointed linen coif and an embroidered standing collar. Each output is projected back onto the 3D head
pixel for pixel, so the FRAMING MUST NOT MOVE: the coif, the face outline, hairline, nose, eye positions and the mouth's centre line stay
on the same pixels. Landmarks in both inputs: eye centres at about (499, 517) and (755, 517); nose tip about (627, 600); the mouth's
centre line about row 791, its corners about x 540 and 714.
Review of the inputs: both women read cross and surprised: a pursed, protruding pout with a hanging lower lip, too red; knitted, angry
brows; round glaring eyes with white showing all round the iris; a dark triangular shadow under the nose. In the original game both
women smile broadly and warmly with crinkled eyes and soft brows, and woman B is clearly elderly.

## Inputs (attached, in order)
1. `references_face/in_face_b.png` — woman B render to fix (the elderly villager, grey-white hair).
2. `references_head/b_01_front.png` — the approved HD portrait of woman B: identity, skin, hair and coif to match.
3. `references_face/mm9_face_b.png` — the ORIGINAL 2002 game face of woman B (low resolution, different framing): her broad warm smile,
   crinkled smiling eyes, rosy cheeks, her age.
4. `references_face/in_face_a.png` — woman A render to fix (auburn hair, broad face).
5. `references_head/a_01_front.png` — the approved HD portrait of woman A: identity, skin, hair.
6. `references_face/mm9_face_a.png` — the ORIGINAL game face of woman A: a broad-faced, warmly smiling woman of about 45.

## Deliverables (1254x1254, same framing as the corresponding input, unresized returns)
| File | From |
|---|---|
| `out_face_b.png` | input 1 repainted, identity from inputs 2 and 3 |
| `out_face_a.png` | input 4 repainted, identity from inputs 5 and 6 |

## What to change (the face from just above the brows down to the chin, cheek to cheek; plus the hair inside the coif opening)
- MOUTH: a warm, natural CLOSED-LIP smile, lips together, no teeth (the 3D mouth is closed and flat). Normal mouth width, the corners at
  about the same x as now, turned gently UP into the cheeks with soft smile lines. Natural lip thickness (upper lip thinner than the
  lower; together clearly thinner than the current pout), natural muted rose lips with a soft edge, no dark outline, not glossy. The line
  between the lips on row ~791 as in the input.
- CHIN and UNDER THE NOSE: clean skin, no dark triangle or shadow under the nose, no smudge under the lower lip; the nostrils small and soft.
- EYES: relaxed, warmly smiling eyes: upper lids lowered a little, lower lids raised slightly by the smile, soft crow's feet; the iris
  touches the upper lid (NO white ring round the iris); irises blue-grey; each eye's centre on the SAME pixel as in the input. No red rims,
  no dark sockets, no heavy eyeliner.
- BROWS: soft, level, relaxed, thinner, with no frown lines between them (B: grey-blonde; A: light auburn). One pair only.
- CHEEKS: rosy and lifted by the smile.
- WOMAN B ONLY: clearly elderly, about 65-70: softer, slightly sagging skin, fine forehead wrinkles, lines round the mouth, deep crow's
  feet, a kind grandmother as in input 3. Her hair is grey-white, parted in the middle and swept back under the coif; the grey band above
  her hairline is the same grey-white hair pulled back (paint it as hair, soft strands, no cap edge).
- WOMAN A ONLY: about 45, a broad, warm, motherly face as in input 6; her auburn hair parted in the middle and swept back; remove the two
  faint light zigzag lines in the hair near the top of the coif opening.
- Flat even albedo like the input: no added light, shadows, highlights or reflections.

## Keep EXACTLY as in the input (pixel positions and colours)
The coif (all cream cloth), the ears' area under it, the neck below the jaw, the embroidered collar, the blouse, the grey background, the face
outline. The nose shape and position. Same image size and framing. No zoom, no shift.

## Checks before saving (one corrective regeneration per output at most)
Overlay the output on its input: coif, hairline, nose tip, eye centres and face outline must coincide within a few pixels; the lip line on
row ~791; closed lips, no teeth; no white ring round the irises; no dark triangle under the nose; soft level brows. Write
`generation_runs.json` (id, prompt, inputs with sha256, output, selected, reason) and a `review.png` with input and output side by side for
B and A.
