# Codex brief: face repaint for tier B of the MM9 townsman PeasantM5 (mm9_peasantm5_claude)

Scope: image generation/editing only. Write ONLY into `level_generation/creatures/mm9_peasantm5_claude/references_face/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

## What the input is
`in_face_b.png` is a flat, UNLIT (albedo) front orthographic render of a game character's 3D head texture, 1254x1254: a stocky
man of about 40 with a short full beard (person A, with his hair already tinted golden-brown). The output is projected back onto
the same 3D head pixel for pixel, so the FRAMING MUST NOT MOVE: the face outline, hairline, ears, nose, eye positions, the beard
outline and the line between the lips stay on the same pixels. Repaint ONLY the face (from the hairline down to the chin, cheek to
cheek) into a DIFFERENT man, person B, the other townsman who wears the same clothes in the original game.

## Inputs (attached, in order)
1. `references_face/in_face_b.png` — the render to repaint (edit target; keep its framing and lighting-free flat albedo).
2. `references_face/mm9_face_b.png` — the ORIGINAL 2002 game face of person B (low resolution): identity authority.
3. `references_hd/mm9_head_views_b.png` — the original game head of person B from five sides (identity, skin and hair tone).

## Deliverable (1254x1254, same framing as input 1, unresized return)
`out_face_b.png`. Also write `generation_runs.json` (id, prompt, inputs with sha256, output, selected, reason) and `review.png`
(input and output side by side). At most ONE corrective regeneration.

## Person B (from inputs 2-3)
A man of about 35, a slightly leaner, more angular face than A with a straight nose and defined cheekbones; fair skin with a light
healthy warmth; clear light BLUE eyes fully open with visible irises; straight golden-brown brows; a SHORT, close-trimmed
golden-brown beard and moustache (stubble-length on the cheeks, a little fuller on the chin) inside the SAME beard outline as input 1,
the skin faintly showing through it; a calm, friendly CLOSED-LIP slight smile (lips together, no teeth, no dark gap). Calm and kind,
never stern or fierce.

## Rules
- The line between the lips on the SAME height and width as in input 1; the eye centres, the brows' height, the nose tip and nostrils
  on the same pixels; the face outline and the beard outline unchanged.
- ONE set of brows; ONE nose with exactly two small nostrils (painted where input 1 has them, not wider); lips painted once, no second
  lip line, no dark slot between the lips, no lipstick colour; no pale crescent or dark line under the lower lids; no red rims; no
  light band between brows and eyes; no make-up lines; no hard edge where the beard ends.
- Flat even albedo like the input: no added light, shadows, highlights or reflections.
- Keep EXACTLY as in input 1: hair and hairline, ears, neck, collar, the grey background, the face outline. No zoom, no shift.

## Check before saving
Overlay the output on input 1: hairline, ears, nose tip, eye centres, lip line, beard outline and face outline coincide within a
few pixels.
