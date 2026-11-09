# Codex brief: paint the MM9 Highwayman's head, three tiers (mm9_highwayman_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_highwayman_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game character, an adult male travelling rogue, restored from a 2002 game for a game mod. The result is projected onto a 3D head, so **every painted view must keep the exact outline and feature positions of its clay input**, pixel for pixel: eyes, nose, mouth, hairline, chin, jaw, rim of the hair. Only surface paint is added. Do not change the shape, do not turn or tilt the head, do not add hair volume beyond the clay's outline.

## Inputs (attached, in order)
1-7. `references_head/clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`, `clay_05_top.png`, `clay_06_q34r.png`, `clay_07_q34l.png`: the clay head with the bare V of the chest below the neck, geometry authority.
8. `references_hd/mm9_head_views_<tier>.png`: renders of the ORIGINAL low-poly head, five views: front, three-quarter, figure's left, back, figure's right: identity, hair and colour authority. Ignore the faceting and the tunic. In a front view the figure's LEFT is on IMAGE RIGHT.
9. `references_hd/mm9_skin_x4_<tier>.png`: the original skin enlarged; its face panel top left is the sharpest evidence of the face.

## Deliverables (true transparent background, same size as the clay, unresized returns, no floor, no shadow, no text)
For tier X: `references_head/<x>_01_front.png`, `<x>_03_left.png`, `<x>_02_back.png`, `<x>_04_right.png`, `<x>_05_top.png`, `<x>_06_q34r.png`, `<x>_07_q34l.png`. Generate front first, then use it as an extra input for the others so that all views are the SAME man with the SAME paint. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_<x>.json` (id, prompt, inputs with sha256, output path) and `selected_views_review_<x>.png`.

Even soft studio light, no cast shadows, no rim light, no drama: the paint is a colour map. Semi-realistic game-art materials with sharp detail: skin pores, stubble, individual hair strands combed along the clay's hair mass. Eyes open, irises clearly drawn, mouth closed. The clay's whole hair mass is hair, nothing of the skin shows through it.

## Tier A (Cutpurse): skin file a
A man about 35, warm tanned skin, blue eyes, a short ginger-blond beard and moustache. Dark-blond to ginger hair over the whole clay hair mass, parted at the centre, combed straight down. A black leather HEADBAND runs level round the whole head across the forehead just above the eyebrows, dark metal rivets, with a dark metal diamond-shaped central clasp in the middle of the forehead rising to the crown, exactly as inputs 8 and 9, and level round the back of the head.

## Tier B (Burglar): skin file b
A man about 30, fair tanned skin, bright blue eyes, a light blond short stubble beard and thin moustache, a thin vertical scar on the cheek as input 9. Long pale-blond hair over the whole clay hair mass, centre parting, golden highlights. No headband.

## Tier C (Bandit): skin file c
A man about 40, ruddy tanned skin, a blue eye, a short red beard and a heavy red moustache. Copper-red hair over the whole clay hair mass, combed from a centre parting, with one thin braid running down from the temple on the figure's LEFT side (IMAGE RIGHT in a front view) as inputs 8 and 9. A black leather EYE PATCH with a small dark metal plate covers his LEFT eye (IMAGE RIGHT in a front view), held by a thin black strap running level round the whole head across the forehead and the back of the head, exactly as inputs 8 and 9. His right eye is open.

Do NOT add a helmet, hood, ears or jewellery beyond the above.
