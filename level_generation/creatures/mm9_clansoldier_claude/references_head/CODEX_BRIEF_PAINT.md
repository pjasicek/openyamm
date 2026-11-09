# Codex brief: paint the MM9 Horde Soldier's head, three tiers (mm9_clansoldier_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_clansoldier_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game character, an adult male medieval foot soldier, restored from a 2002 game for a game mod. The result is projected onto a 3D head, so **every painted view must keep the exact outline and feature positions of its clay input**, pixel for pixel: eyes, nose, mouth, ears, chin, jaw, helmet, nasal bar, the curtain behind the neck. Only surface paint is added. Do not change the shape, do not turn or tilt the head, do not add volume beyond the clay's outline.

## Inputs (attached, in order)
1-7. `references_head/clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`, `clay_05_top.png`, `clay_06_q34r.png`, `clay_07_q34l.png`: the clay head, geometry authority. It shows a dome helmet with a thick brim, a nasal bar, the face and ears, the neck running down to the collar (the lowest part of the neck is the bare V of the chest), and a curtain hanging behind the neck.
8. `references_hd/mm9_head_views_<tier>.png`: renders of the ORIGINAL low-poly head, five views: three-quarter, front, figure's left, back, figure's right: identity, helmet, hair and colour authority. Ignore the faceting and the mail and coat. In a front view the figure's LEFT is on IMAGE RIGHT.
9. `references_hd/mm9_skin_x4_<tier>.png`: the original skin enlarged; its face panel top left and the helmet panel next to it are the sharpest evidence.

## Deliverables (true transparent background, same size as the clay, unresized returns, no floor, no shadow, no text)
For tier X: `references_head/<x>_01_front.png`, `<x>_03_left.png`, `<x>_02_back.png`, `<x>_04_right.png`, `<x>_05_top.png`, `<x>_06_q34r.png`, `<x>_07_q34l.png`. Generate front first, then use it as an extra input for the others so that all views are the SAME man with the SAME paint. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_<x>.json` (id, prompt, inputs with sha256, output path) and `selected_views_review_<x>.png`.

Even soft studio light, no cast shadows, no rim light, no drama: the paint is a colour map. Semi-realistic game-art materials with sharp detail: skin pores, stubble, worn metal, fur, individual hair strands. Eyes open, irises clearly drawn on the clay's eye positions, mouth closed.

## Common to all tiers
Warm tanned skin. The bare neck and the V at the throat are skin. The dome of the helmet is worn grey-bronze steel with a slightly raised ridge painted from the front to the top and darker seams, as input 8. The nasal bar is plain worn steel.

## Tier A (Horde Grunt): skin file a
A man about 35, pale blue-grey eyes, thin dark eyebrows, a thin black moustache and a small black goatee on the chin, as inputs 8 and 9. The helmet's brim and the lower part of the dome are mottled dark brown and tan fur, as input 8; the upper dome is steel. Long straight black hair: the whole curtain behind the neck is black hair with individual strands combed straight down. A small gold earring in each ear lobe.

## Tier B (Horde Warrior): skin file b
A man about 40, grey eyes, a full short black beard and moustache over the jaw and chin, as inputs 8 and 9. Helmet as tier A. The curtain behind the neck is a laminated steel neck guard: five or six horizontal overlapping steel bands edged with thin gold lines, as input 8; at the sides in front of the ears' line a thin black hair edge. 

## Tier C (Horde Leader): skin file c
A man about 50, grey eyes, a short grey-white beard and moustache, as inputs 8 and 9. The helmet's brim and the front of the dome are bone white and tan, painted with a stylised golden lion mask in the middle of the forehead, red flashes at the sides and small red marks round the brim, as inputs 8 and 9; the back of the dome is grey-bronze. The curtain behind the neck is red and white lamellar scales with dark blue lacing, framed at the sides by a tan leather band behind each ear, and dark fur at its lower edge, as input 8.

Do NOT add a beard or hair relief beyond the clay's outline, no extra straps, no jewellery beyond the above.
