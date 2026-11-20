# Codex brief: paint the MM9 Thrall's head, three tiers (mm9_thrall_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_thrall_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game character, an adult male enslaved tribesman, restored from a 2002 game for a game mod. The result is projected onto a 3D head, so **every painted view must keep the exact outline and feature positions of its clay input**, pixel for pixel: eyes, nose, mouth, hairline, chin, jaw, rim of the hair. Only surface paint is added. Do not change the shape, do not turn or tilt the head, do not add hair volume beyond the clay's outline.

## Inputs (attached, in order)
1-7. `references_head/clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`, `clay_05_top.png`, `clay_06_q34r.png`, `clay_07_q34l.png`: the clay head, geometry authority.
8. `references_hd/mm9_head_views_<tier>.png`: renders of the ORIGINAL low-poly head, four views: identity, hair and colour authority. Ignore the faceting, the white streaks and the shoulders.
9. `references_hd/mm9_skin_x4_<tier>.png`: the original skin enlarged; its face panel top left is the sharpest evidence of the face.

## Deliverables (true transparent background, same size as the clay, unresized returns, no floor, no shadow, no text)
For tier X: `references_head/<x>_01_front.png`, `<x>_03_left.png`, `<x>_02_back.png`, `<x>_04_right.png`, `<x>_05_top.png`, `<x>_06_q34r.png`, `<x>_07_q34l.png`. Generate front first, then use it as an extra input for the others so that all views are the SAME man with the SAME paint. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_<x>.json` (id, prompt, inputs with sha256, output path) and `selected_views_review_<x>.png`.

Even soft studio light, no cast shadows, no rim light, no drama: the paint is a colour map. Semi-realistic game-art materials with sharp detail: skin pores, wrinkles, individual hair strands.

## Tier A (Field Thrall): skin file a
An old man about 65. Deep wrinkles, weathered orange-brown skin, sunken dark eyes with white eyebrows, a short white-grey beard and moustache, mouth closed, the lips thin. BALD crown: the top of the head and forehead are bare skin, with age spots, all the way over the crown (top view: bare skin in the middle). The wide lower mass of the clay's hair is long straight white-grey hair, starting at a line above the ears and running down to its rim, thin and strandy; at the back it starts high on the back of the skull.

## Tier B (Thrall): skin file b
A man about 35, ruddy red-brown skin, blue-grey eyes, a short sandy-brown beard and moustache with stubble, mouth closed. Sandy-brown to auburn hair over the whole clay hair mass, combed straight down from the crown. A dark brown leather headband round the head at the forehead, just above the eyebrows, covering the hairline, running level round the whole head, tied at the back with a small knot.

## Tier C (Thrall Master): skin file c
A man about 40, dark tanned skin, dark brown eyes, a short dark beard, mouth closed, strong brow. Dark brown hair over the whole clay hair mass, combed straight down from a loose centre parting, with lighter sun-streaked strands.
