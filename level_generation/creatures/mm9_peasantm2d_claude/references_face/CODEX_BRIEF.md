# Codex brief: face repaint for tier C of the MM9 young elf PeasantM2d (mm9_peasantm2d_claude)

Scope: image generation/editing only. Write ONLY into `level_generation/creatures/mm9_peasantm2d_claude/references_face/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

## What the input is
`in_face_c.png` is a flat, UNLIT (albedo) front orthographic render of a game character's 3D head texture, 1254x1254: a young
blond elf man (person D). The output is projected back onto the same 3D head pixel for pixel, so the FRAMING MUST NOT MOVE:
the face outline, hairline, ears, nose, eye positions and the line between the lips stay on the same pixels.
Repaint ONLY the face (from the hairline down to the chin, cheek to cheek) into a DIFFERENT man, person C, the other elf townsman
who wears the same clothes in the original game.

## Inputs (attached, in order)
1. `references_face/in_face_c.png` — the render to repaint (edit target; keep its framing and lighting-free flat albedo).
2. `references_face/mm9_face_c.png` — the ORIGINAL 2002 game face of person C (low resolution): identity authority.
3. `references_hd/mm9_head_views_c.png` — the original game head of person C from five sides (identity, skin tone).

## Deliverable (1254x1254, same framing as input 1, unresized return)
`out_face_c.png`. Also write `generation_runs.json` (id, prompt, inputs with sha256, output, selected, reason) and `review.png`
(input and output side by side). At most ONE corrective regeneration.

## Person C (from inputs 2-3)
An elf man of about 35, a broader, squarer face than D with a strong straight brow ridge and a firm square chin; ruddy warm skin
with a healthy rosy tone on the cheeks and nose; clear blue-green eyes; slightly thicker, darker honey-brown brows; clean-shaven
(no beard, no stubble). A warm, friendly CLOSED-LIP smile (the 3D mouth is closed: lips together, no teeth, no open dark gap),
corners turned gently up, relaxed smiling eyes with faint smile lines. Calm and kind, never stern or fierce.

## Rules
- The line between the lips on the SAME height and width as in input 1; the eye centres, the brows' height, the nose tip and
  nostrils on the same pixels; the face outline unchanged.
- ONE set of brows; ONE nose with two nostrils (painted where input 1 has them); lips painted once, no second lip line, no dark slot
  between the lips; no pale crescent under the lower lids; no red rims; no light band between brows and eyes; no make-up lines.
- Flat even albedo like the input: no added light, shadows, highlights or reflections.
- Keep EXACTLY as in input 1: hair and hairline, ears, neck, the grey background, the face outline. No zoom, no shift.

## Check before saving
Overlay the output on input 1: hairline, ears, nose tip, eye centres, lip line and face outline coincide within a few pixels.
