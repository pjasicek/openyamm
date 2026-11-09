# Codex brief: paint the MM9 Nosferatu's head (mm9_nosferatu_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_nosferatu_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game creature, a bald goblin-faced undead, restored from a 2002 game for a game mod. The result is projected onto a 3D head, so **every painted view must keep the exact outline and feature positions of its clay input**, pixel for pixel: eyes, nose, mouth, teeth, ears, chin, jaw. Nothing moves, nothing is added outside the outline.

## Inputs (attached, in order)
1-5. `references_head/clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`, `clay_05_top.png`: the clay head, geometry authority.
6. `references_hd/mm9_head_views_b.png`: renders of the ORIGINAL low-poly head, five views: identity and colour authority. Ignore the faceting and the shoulders.
7. `references_hd/mm9_skin_x4_b.png`: the original skin enlarged; the face at the top left is the sharpest evidence for skin tone, wrinkles and the teeth.
8. `references_head/in_body_head.png`: the approved high-definition head.

## Deliverables (true transparent background, same size as the clay, unresized returns, no floor, no shadow, no text)
`b_01_front.png`, `b_03_left.png`, `b_02_back.png`, `b_04_right.png`, `b_05_top.png`. Generate the front first, then use it as an extra input for the others so all views are the SAME creature with the SAME paint. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_b.json`.

Even soft studio light, no cast shadows, no rim light, no drama: the paint is a colour map. Semi-realistic game-art materials with sharp detail: leathery skin, pores, wrinkles, veins.

## The paint
SKIN: sallow pale tan parchment skin, slightly ochre, as input 7, darker and redder in the deep folds round the eyes, nose and mouth, a faint mottling, a raised vein up the forehead. No hair at all, no eyebrows. The ears the same skin, a little pinker in their hollows, thin and veined.
EYES: small sharp amber-orange irises with a black pupil, one iris each, looking straight ahead, dark lids, a red rim.
MOUTH: dark red-brown gums, the teeth uneven dirty ivory-yellow. Inside the mouth nearly black.
The neck below the jaw: the same skin down to the bottom of the clay.
