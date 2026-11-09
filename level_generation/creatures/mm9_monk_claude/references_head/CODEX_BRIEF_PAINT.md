# Codex brief: paint the MM9 Monk's head, three tiers (mm9_monk_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_monk_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game character, an adult male medieval monk, restored from a 2002 game for a game mod. The result is projected onto a 3D head, so **every painted view must keep the exact outline and feature positions of its clay input**, pixel for pixel: eyes, nose, mouth, ear, chin, jaw. Nothing moves, nothing is added outside the outline.

## Inputs (attached, in order)
1-3. `references_head/clay_01_front.png`, `clay_03_left.png`, `clay_04_right.png`: the clay head, geometry authority. Its back is cut away: that part is hidden in a hood, paint it plain.
4-5. `references_head/clay_06_q34r.png`, `clay_07_q34l.png`: the same head at three-quarter.
6. `references_hd/mm9_head_views_<tier>.png`: renders of the ORIGINAL low-poly head in its hood, five views: identity, hair and colour authority. Ignore the faceting and the hood.
7. `references_hd/mm9_skin_x4_<tier>.png`: the original skin enlarged; the face panel at the top left is the sharpest evidence.

## Deliverables (true transparent background, same size as the clay, unresized returns, no floor, no shadow, no text)
For tier X: `references_head/<x>_01_front.png`, `<x>_03_left.png`, `<x>_04_right.png`, `<x>_06_q34r.png`, `<x>_07_q34l.png`. Generate the front first, then use it as an extra input for the others so all views are the SAME man with the SAME paint. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_<x>.json`.

Even soft studio light, no cast shadows, no rim light, no drama: the paint is a colour map. Semi-realistic game-art materials with sharp detail: skin pores, wrinkles, individual hairs.
The eyes are open, looking straight ahead, one iris each, drawn inside the clay's eye openings. The neck below the jaw is bare skin down to the bottom of the clay. Hair covers the clay's raised hair mass, and short hair on the forehead follows the fringe of input 7.

## Tier A (Initiate): skin file a
A lean stern man of about 40, pale tanned skin with reddish shading in the cheek hollows, steel-blue eyes, heavy dark eyebrows, hooked straight nose, black hair in a short straight fringe low on the forehead, deep lines beside the mouth, a very small thin black goatee on the chin only, thin closed lips.

## Tier B (Monk): skin file b
A warm cheerful man of about 40, tanned skin, brown eyes with laugh lines, thick brown hair swept across the forehead, a short neat brown moustache joined to a short brown beard along the jaw, lips parted in a slight smile showing a thin line of teeth drawn inside the clay's closed mouth.

## Tier C (Reverend Monk): skin file c
A weathered man of about 55, ruddy red-brown skin with freckles and deep wrinkles, pale grey-blue eyes, reddish-brown hair going sparse at the forehead, a full short ginger-red beard and moustache covering the jaw and chin, thin closed lips.
