# Codex brief: paint the MM9 Evil Sorcerer's head, three tiers (mm9_evilsorcerer_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_evilsorcerer_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game character, an adult male court sorcerer, restored from a 2002 game for a game mod. The result is projected onto a 3D head, so **every painted view must keep the exact outline and feature positions of its clay input**, pixel for pixel: eyes, nose, mouth, ears, chin, jaw, the crown's points, its band, the oval boss, the flap's edges. Nothing moves, nothing is added outside the outline.

## Inputs (attached, in order)
1-7. `references_head/clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`, `clay_05_top.png`, `clay_06_q34r.png`, `clay_07_q34l.png`: the clay head, geometry authority.
8. `references_hd/mm9_head_views_<tier>.png`: renders of the ORIGINAL low-poly head, five views: identity, crown, flap and colour authority. Ignore the faceting and the shoulders.
9. `references_hd/mm9_skin_x4_<tier>.png`: the original skin enlarged; its panels top left (face, crown) are the sharpest evidence.

## Deliverables (true transparent background, same size as the clay, unresized returns, no floor, no shadow, no text)
For tier X: `references_head/<x>_01_front.png`, `<x>_03_left.png`, `<x>_02_back.png`, `<x>_04_right.png`, `<x>_05_top.png`, `<x>_06_q34r.png`, `<x>_07_q34l.png`. Generate the front first, then use it as an extra input for the others so all views are the SAME man with the SAME paint. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_<x>.json`.

Even soft studio light, no cast shadows, no rim light, no drama: the paint is a colour map. Semi-realistic game-art materials with sharp detail: skin pores, wrinkles, individual hairs, embossed metal.
The eyes are open, looking straight ahead, one iris each. The mouth is closed. The neck below the jaw is bare skin down to the bottom of the clay.

## Tier A (Evil Apprentice): skin file a
A clean young man of about 28, smooth tanned skin, handsome, dark brown eyes, thin dark eyebrows, short black hair at the temples and sideburns, a very small neat black goatee on the chin only and a faint thin moustache. CROWN: dark navy blue enamel with bright gold trim on every edge and thin gold scrollwork, the brow band bright gold, the oval boss a teal-green gem in a gold mount. The inner cap dark. FLAP: dark navy blue cloth with a thin gold edge.

## Tier B (Evil Sorcerer): skin file b
A cruel man of about 45, sharp arched black eyebrows, dark brown eyes, strong nasolabial lines, tanned skin, a black swept moustache joined to a thick black goatee, trimmed black sideburns, black hair at the temples. CROWN: red enamel with bright gold scrollwork and gold trim on every edge, the brow band pale gold, the oval boss a red gem in a gold mount. The inner cap dark. FLAP: red and gold brocade with a thin gold edge.

## Tier C (Evil Grand Sorcerer): skin file c
A very old man of about 70, deeply wrinkled pale skin with reddish tones round the eyes, thick white eyebrows, pale piercing eyes, grey-white hair at the temples and over the ears' sides, a white moustache and a short white beard. A few small red ritual marks on the cheeks, as input 8. CROWN: pale ivory enamel with dark gold scrollwork and gold trim on every edge, the brow band pale gold, the oval boss a pale ivory stone in a gold mount. The inner cap dark. FLAP: pale grey-green brocade with gold scrollwork and a thin gold edge.
