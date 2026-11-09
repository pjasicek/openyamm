# Codex brief: face repaint of the MM9 townswomen PeasantF4 A and B head texture renders (mm9_peasantf4_claude)

Scope: image generation/editing only. Write ONLY into `level_generation/creatures/mm9_peasantf4_claude/references_face/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

## What these images are
`in_face_a.png` and `in_face_b.png` are flat, UNLIT (albedo) front orthographic renders of a game character's 3D head texture,
1254x1254. Each output is projected back onto the 3D head pixel for pixel, so the FRAMING MUST NOT MOVE: the face outline, the hood and
its edge, the nose, the eye positions and the mouth's centre line stay on the same pixels.
Both are the SAME 3D head (two different women of the same game model). Review of the inputs: the mouth is painted slightly OPEN with
dark lipstick-red lips and a pale gap between them (the 3D mouth is closed, so this reads as a second lip layer); the eyes are wide and
staring with a lot of white; the brows are drawn heavy; there is NO hair visible under the hood (the forehead skin runs up to the hood's
edge), while the game original shows dark hair there.

## Inputs (attached, in order)
1. `references_face/in_face_a.png`: woman A render to fix.
2. `references_head/01_front.png`: the approved HD portrait of woman A: identity, warm closed-lip smile, eyes, skin and dark hair to match.
3. `references_face/mm9_face_a.png`: the ORIGINAL 2002 game render of woman A (low resolution): her face and her dark hair under the hood.
4. `references_face/in_face_b.png`: woman B render to fix.
5. `references_face/mm9_face_b.png`: the ORIGINAL game render of woman B: an older, thinner woman (about 60) with dark hair streaked with
   grey under the same hood, a lined, tired face, a calm closed mouth.

## Deliverables (1254x1254, same framing as the corresponding input, unresized returns)
| File | From |
|---|---|
| `out_face_a.png` | input 1 repainted, identity from inputs 2 and 3 |
| `out_face_b.png` | input 4 repainted, identity from input 5 (a different, older person than A) |

## What to change
Both women (the face from the hood's edge down to the chin, cheek to cheek):
- HAIR: dark brown hair parted in the middle, visible inside the hood's opening as in the game originals: from the hood's edge down over
  the upper forehead in two soft sweeps to the temples, with soft natural edges against the skin and the hood. The hood itself is not
  changed. Woman B's hair: dark brown with grey strands.
- MOUTH: a calm CLOSED mouth, lips together, NO teeth and no pale gap between the lips (the 3D mouth is closed). Normal mouth width and
  natural lip thickness (upper lip thinner than the lower), natural muted rose lips with a soft edge, no dark outline, no lipstick red.
  The line between the lips on the SAME height as the centre of the current mouth. Woman A: a gentle warm closed-lip smile. Woman B: a
  calm, kind, slightly tired mouth (not stern).
- CHIN: clean skin under the lower lip, no smudge, no second lip shape.
- EYES: relaxed, friendly eyes, the iris touching the upper lid (not staring), each eye's centre on the SAME pixel as in the input; NO red
  rims, no pale crescent under the lower lid, no dark sockets, one natural brow line each (thinner than in the input).
- SKIN: even warm skin; woman A about 45 (soft lines at the eyes); woman B about 60 (more lines on the forehead, round the eyes and
  mouth, slightly hollower cheeks in paint only).
- Flat even albedo like the input: no added light, shadows, highlights or reflections.

## Keep EXACTLY as in the input (pixel positions and colours)
The hood (olive-brown cloth) and its edge, the dark inside of the hood beside the jaw, the neck, the grey background, the face outline,
the nose shape and position. Same image size and framing. No zoom, no shift.

## Checks before saving (one corrective regeneration per output at most)
Overlay the output on its input: hood edge, nose tip, eye centres and face outline must coincide within a few pixels; closed lips, no
teeth; no red eye rims; dark hair under the hood edge with soft edges; calm, warm expressions (never fierce, cold or staring). Write
`generation_runs.json` (id, prompt, inputs with sha256, output, selected, reason) and a `review.png` with input and output side by side for
A and B.
