# Codex brief: repaint our head renders as the skull (mm9_banshee_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_banshee_claude/references_head2/skull/`. Do not edit any other file, do not run builds, do not call Meshy.

Inputs (attached, in order):
1. `references_head2/ours/01_front.png`, 2. `02_back.png`, 3. `03_left.png`, 4. `04_right.png`: exact flat renders of OUR 3D head model painted as the woman. These images are projected back onto the model, so the outline, position, size and every feature's place (eyes, nose, mouth, teeth, hairline, chin, neck edge) must stay EXACTLY where they are, pixel for pixel: this is a repaint of the surface, not a new drawing.
5. `references_head2/e/01_front.png`, 6. `references_head2/e/03_left.png`: the look to reach: the skull identity.
7. `references_hd/mm9_skin_x4_E.png`: the original game skin, top left: the skull painting.

Deliverables in `references_head2/skull/` (1024x1024, same framing as the matching input, true transparent background outside the head, unresized):
`01_front.png`, `02_back.png`, `03_left.png`, `04_right.png`.

Prompt for each: Edit this exact image. Keep the outline, the framing, the size and the position of every feature unchanged. Repaint the skin as a real SKULL painted onto the same shape: ivory bone with brown shading and hairline cracks; the eye areas become large round black sockets, each holding a glowing GREEN eye with a dark pupil exactly where her eye is now; the nose becomes a black nose cavity in place; the lips disappear and the cheeks over the teeth show long ivory teeth roots; teeth stay where they are, ivory; the mouth interior stays black. The hair stays where it is, same strands direction, recoloured to pale straw-blond with dark umber streaks. The neck becomes ivory bone-coloured dry skin with cracks. Even flat light, no cast shadows, no new highlights, no text.

Per image check: outline unchanged against its input; same side; eyes, nose, mouth at the same pixels. One correction per view at most. Keep raw returns in `references_head2/skull/raw/`. Write `references_head2/skull/generation_runs.json` and `references_head2/skull/review.png` (contact sheet).
