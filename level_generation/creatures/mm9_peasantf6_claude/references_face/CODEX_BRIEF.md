# Codex brief: face repaint of the MM9 elf townswoman PeasantF6 head texture render (mm9_peasantf6_claude)

Scope: image generation/editing only. Write ONLY into `level_generation/creatures/mm9_peasantf6_claude/references_face/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. The tool takes at most five
reference images per call.

## What the input is
`in_face_a.png` is a flat, UNLIT (albedo) front orthographic render of a game character's 3D head texture, 1254x1254: a young elf woman
with a honey-blond bob, long pointed ears and a cream linen collar. Each output is projected back onto the 3D head pixel for pixel, so
the FRAMING MUST NOT MOVE: the face outline, the hair outline and hairline, the ears, the nose, the eye positions and the mouth's centre
line stay on the same pixels. Landmarks: eye centres about (488, 512) and (762, 512); nose tip about (627, 690); the mouth's centre line
about row 803, its corners about x 520 and 735.
Review of the input: the lips are painted as a large, bright red lipstick mouth (too red, too large and glossy, with a pale speck in the
middle of the lip line); a faint dark crease line runs down the cheek under her right eye (image left).

## Inputs (attached, in order)
1. `references_face/in_face_a.png`: the render to repaint (used for BOTH outputs).
2. `references_head/a_01_front.png`: the approved HD portrait of woman A: identity, skin, hair, lips.
3. `references_face/mm9_face_a.png`: the ORIGINAL 2002 game face of woman A (low resolution, different framing).
4. `references_face/mm9_face_b.png`: the ORIGINAL game face of woman B: a warm, broad-faced elf woman of about 45 with auburn-chestnut hair.

## Deliverables (1254x1254, same framing as the input, unresized returns)
| File | Identity |
|---|---|
| `out_face_a.png` | woman A, fixed (inputs 1-3) |
| `out_face_b.png` | woman B on the same head (inputs 1 and 4) |

## What to change (the face from the hairline down to the chin, cheek to cheek, and the hair's COLOUR where visible)
- MOUTH (both): a warm, natural CLOSED-LIP smile, lips together, no teeth (the 3D mouth is closed and flat). The lip line between the lips
  stays on row ~803 and the corners at about the same x, turned gently UP. Natural lip size (smaller than the input's: upper lip thinner
  than the lower), soft natural rose-pink lips close to the skin tone with a soft edge, NO lipstick red, no gloss, no dark outline, ONE pair
  of lips only (no second lip line, no pale gap).
- SKIN (both): clean, even, no dark crease lines on the cheeks, no dark triangle or shadow under the nose or the lower lip, small soft
  nostrils.
- EYES (both): relaxed, open, friendly eyes; the upper lid rests just over the top of the iris, the lower lid touches the bottom of the iris
  (no white showing below the iris), each eye's centre on the SAME pixel as in the input; no red rims, no pale crescent under the lower
  lid, no heavy liner. ONE soft natural brow per eye, level and relaxed.
- WOMAN A: about 25, as input 2: fair warm-peach skin, faint freckles over the nose, blue eyes, light-brown brows, honey-blond hair (keep the
  input's hair exactly).
- WOMAN B: about 45, a broad warm motherly face as input 4: fuller cheeks, soft smile lines and faint crow's feet, a warm closed-lip smile;
  blue-grey eyes, brows auburn-brown; the hair repainted from honey-blond to a rich AUBURN / CHESTNUT brown with the same strands and the
  same outline (input 4's colour); the ears stay skin.
- Flat even albedo like the input: no added light, shadows, highlights or reflections.

## Keep EXACTLY as in the input (pixel positions)
The hair outline and the hairline, the ears' outline, the neck, the collar and the clothes below the chin, the grey background, the face
outline, the nose shape and position. Same image size and framing. No zoom, no shift.

## Checks before saving (one corrective regeneration per output at most)
Overlay the output on the input: hair outline, hairline, ears, nose tip, eye centres and face outline must coincide within a few pixels;
the lip line on row ~803; closed lips, no teeth; no lipstick red; no white below the irises; no crease line under the eye. Write
`generation_runs.json` (id, prompt, inputs with sha256, output, selected, reason) and a `review.png` with the input and both outputs side by
side.
