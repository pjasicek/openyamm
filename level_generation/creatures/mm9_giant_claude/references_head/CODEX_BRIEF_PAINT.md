# Codex brief: paint the MM9 Giant's head, two tiers (mm9_giant_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_giant_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game character, a huge barbarian giant man, restored from a 2002 game for a game mod. The result is projected onto a 3D head, so **every painted view must keep the exact outline and feature positions of its clay input**, pixel for pixel: eyes, nose, mouth, ears, hairline, chin, jaw, rim of the hair. Only surface paint is added. Do not change the shape, do not turn or tilt the head, do not add hair volume beyond the clay's outline.

## Inputs (attached, in order)
1-7. `references_head/clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`, `clay_05_top.png`, `clay_06_q34r.png`, `clay_07_q34l.png`: the clay head with the neck, geometry authority.
8. `references_hd/mm9_head_views_<tier>.png`: renders of the ORIGINAL low-poly head, four views: front, three-quarter, figure's left, back: identity, hair and colour authority. Ignore the faceting. In a front view the figure's LEFT is on IMAGE RIGHT.
9. `references_hd/mm9_skin_x4_<tier>.png`: the original skin enlarged; its face panel top left is the sharpest evidence of the face and hair.

## Deliverables (true transparent background, same size as the clay, unresized returns, no floor, no shadow, no text)
For tier X: `references_head/<x>_01_front.png`, `<x>_03_left.png`, `<x>_02_back.png`, `<x>_04_right.png`, `<x>_05_top.png`, `<x>_06_q34r.png`, `<x>_07_q34l.png`. Generate front first, then use it as an extra input for the others so that all views are the SAME man with the SAME paint. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_<x>.json` (id, prompt, inputs with sha256, output path) and `selected_views_review_<x>.png`.

Even soft studio light, no cast shadows, no rim light, no drama: the paint is a colour map. Semi-realistic game-art materials with sharp detail: skin pores, stubble, individual hair strands combed along the clay's hair mass. Eyes open, irises clearly drawn ON the clay's eyes, mouth closed: lips on the clay's lips, no teeth. The clay's whole hair mass is hair, nothing of the skin shows through it. The beard is painted on the clay's jaw and chin only: keep the clay's lips, nose and eyes exactly where they are. The neck below the jaw is plain tanned skin.

## Tier A (Plain Giant): skin file a
A rugged man about 40, warm tanned skin with a ruddy tone, pale blue eyes, a short full COPPER-RED beard and moustache. Bright copper-red hair over the whole clay hair mass, worked into many small tight BRAIDS running down from the crown to the rim, exactly as inputs 8 and 9. A black leather HEADBAND with small dark metal studs runs level round the whole head across the forehead just above the eyebrows and round the back of the head, as inputs 8 and 9.

## Tier B (Forest Giant): skin file b
A rugged man about 40, tanned weathered skin, grey-blue eyes, heavy dark brows, a short full DARK-BROWN beard and moustache with grey flecks. Long loose DARK-BROWN hair over the whole clay hair mass, parted at the centre, straight strands combed down to the rim, as inputs 8 and 9. A small gold ring earring on each ear lobe. No headband.

Do NOT add a helmet, hood, crown, scars or other jewellery.
