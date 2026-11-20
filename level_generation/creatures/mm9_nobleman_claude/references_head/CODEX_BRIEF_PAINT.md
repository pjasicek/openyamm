# Codex brief: paint the MM9 Nobleman's head, three tiers (mm9_nobleman_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_nobleman_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game character, an adult male nobleman, restored from a 2002 game for a game mod. The result is projected onto a 3D head, so **every painted view must keep the exact outline and feature positions of its clay input**, pixel for pixel: eyes, nose, mouth, hairline, chin, jaw, rim of the hair. Only surface paint is added. Do not change the shape, do not turn or tilt the head, do not add hair volume beyond the clay's outline.

## Inputs (attached, in order)
1-7. `references_head/clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`, `clay_05_top.png`, `clay_06_q34r.png`, `clay_07_q34l.png`: the clay head and neck, geometry authority.
8. `references_hd/mm9_head_views_<tier>.png`: renders of the ORIGINAL low-poly head, five views: three-quarter, front, figure's left, back, figure's right: identity, hair and colour authority. Ignore the faceting and the costume. In a front view the figure's LEFT is on IMAGE RIGHT.
9. `references_hd/mm9_skin_x4_<tier>.png`: the original skin enlarged; its face panel top left is the sharpest evidence of the face.

## Deliverables (true transparent background, same size as the clay, unresized returns, no floor, no shadow, no text)
For tier X: `references_head/<x>_01_front.png`, `<x>_03_left.png`, `<x>_02_back.png`, `<x>_04_right.png`, `<x>_05_top.png`, `<x>_06_q34r.png`, `<x>_07_q34l.png`. Generate front first, then use it as an extra input for the others so that all views are the SAME man with the SAME paint. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_<x>.json` (id, prompt, inputs with sha256, output path) and `selected_views_review_<x>.png`.

Even soft studio light, no cast shadows, no rim light, no drama: the paint is a colour map. Semi-realistic game-art materials with sharp detail: skin pores, stubble, individual hair strands combed along the clay's hair mass. Eyes open, irises clearly drawn, the two eyes level and alike. The clay's whole hair mass is hair, nothing of the skin shows through it. The neck is bare warm skin down to the bottom of the clay.

## Tier A (Baron): skin file a
A handsome man about 35, warm fair skin, blue eyes, a short golden-brown beard and moustache along the jaw, mouth closed. Thick golden blond hair over the whole clay hair mass, parted at the centre, combed straight down, with lighter strands, as inputs 8 and 9.

## Tier B (Viscount): skin file b
A jovial older man about 60, pale ruddy skin, deep smile lines, blue eyes, a short white beard and white moustache, a broad open-lipped smile painted on the clay's mouth with white teeth showing, as inputs 8 and 9. White-silver hair over the whole clay hair mass, wavy, parted at the centre.

## Tier C (Count): skin file c
A stern man about 40, warm tanned skin, blue eyes, a short brown beard and moustache, mouth closed. Thick chestnut-brown hair over the clay's lower hair mass, combed straight down. On the crown a CAP painted on the clay: from just above the eyebrows up, a level band all round the head, dark brown leather with small silver studs and a thin gold edge, with a large round gold medallion in the middle of the forehead; above the band a dark brown fur cap covering the whole top of the head, as inputs 8 and 9.

Do NOT add a helmet, a crown, a hood, ears or jewellery beyond the above.
