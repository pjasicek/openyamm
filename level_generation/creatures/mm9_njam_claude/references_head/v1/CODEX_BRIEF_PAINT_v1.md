# Codex brief: paint the head of MM9's Njam the Meddler (mm9_njam_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_njam_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game character, an adult male courtier (a trickster god in human form), restored from a 2002 game for a game mod. The result is projected onto a 3D head, so **every painted view must keep the exact outline and feature positions of its clay input**, pixel for pixel: eyes, nose, mouth, hairline, fringe edge, chin, jaw, rim of the hair. Only surface paint is added. Do not change the shape, do not turn or tilt the head, do not add hair volume beyond the clay's outline.

## Inputs (attached, in order)
1-7. `references_head/clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`, `clay_05_top.png`, `clay_06_q34r.png`, `clay_07_q34l.png`: the clay head and neck, geometry authority. The eyes are smooth bulges in the clay: paint open eyes ON them (white, iris, pupil, lids, lashes) exactly where the bulges are.
8. `references_hd/mm9_head_views.png`: renders of the ORIGINAL low-poly head, five views: three-quarter, front, figure's left, back, figure's right: identity, hair and colour authority. Ignore the faceting and the costume. In a front view the figure's LEFT is on IMAGE RIGHT.
9. `references_head/in_body_head.png`: the high-definition body master's head: face identity and paint quality.

## Deliverables (true transparent background, same size as the clay, unresized returns, no floor, no shadow, no text)
`references_head/a_01_front.png`, `a_03_left.png`, `a_02_back.png`, `a_04_right.png`, `a_05_top.png`, `a_06_q34r.png`, `a_07_q34l.png`. Generate front first, then use it as an extra input for the others so that all views are the SAME man with the SAME paint. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_a.json` (id, prompt, inputs with sha256, output path) and `selected_views_review_a.png`.

Even soft studio light, no cast shadows, no rim light, no drama: the paint is a colour map. Semi-realistic game-art materials with sharp detail: skin pores, light stubble, individual hair strands combed along the clay's hair mass. Eyes open, pale green-blue irises clearly drawn, the two eyes level and alike. The clay's whole hair mass is hair, nothing of the skin shows through it. The neck is bare warm skin down to the bottom of the clay.

## The man
A lean man about 35 with fair, slightly ruddy skin, high cheekbones, a long straight nose, pale green-blue eyes with a sly knowing look, thin lips closed in a slight one-sided smirk painted on the clay's mouth, light brown stubble along the jaw, chin and upper lip (no full beard, no moustache). Medium chestnut-brown hair over the whole clay hair mass with lighter warm strands, combed straight down from the crown: a blunt fringe over the forehead, hanging to the jaw at the sides and to the nape at the back, as inputs 8 and 9.

Do NOT add a helmet, a hat, a crown, a hood, a headband, ears or jewellery.
