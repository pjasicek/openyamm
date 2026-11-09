# Codex brief: paint the MM9 Dwarf's head (mm9_dwarf_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_dwarf_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game character, an adult male dwarf warrior, restored from a 2002 game for a game mod. The result is projected onto a 3D head, so **every painted view must keep the exact outline and feature positions of its clay input**, pixel for pixel: eyes, nose, moustache, beard, helmet, its raised band, the three horns and their collars, the neck. Only surface paint is added. Do not change the shape, do not turn or tilt the head, do not add volume beyond the clay's outline.

## Inputs (attached, in order)
1-7. `references_head/clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`, `clay_05_top.png`, `clay_06_q34r.png`, `clay_07_q34l.png`: the clay head, geometry authority.
8. `references_hd/mm9_head_views.png`: renders of the ORIGINAL low-poly head, five views: three-quarter, front, figure's left, back, figure's right: identity, helmet and colour authority. Ignore the faceting.
9. `references_hd/mm9_skin_x4.png`: the original skin enlarged; its face panel top left, the helmet panel and its studded band are the sharpest evidence.
10. `references_head/in_body_head.png`: the high-definition master's head: finish, materials and level of detail authority.

## Deliverables (true transparent background, same size as the clay, unresized returns, no floor, no shadow, no text)
`references_head/a_01_front.png`, `a_03_left.png`, `a_02_back.png`, `a_04_right.png`, `a_05_top.png`, `a_06_q34r.png`, `a_07_q34l.png`. Generate front first, then use it as an extra input for the others so that all views are the SAME dwarf with the SAME paint. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_a.json` (id, prompt, inputs with sha256, output path) and `selected_views_review_a.png`.

Even soft studio light, no cast shadows, no rim light, no drama: the paint is a colour map. Semi-realistic game-art materials with sharp detail: skin pores, individual beard hairs, worn polished steel, gold studs. Eyes open, irises clearly drawn on the clay's eye positions, a single iris in each eye, looking straight ahead. Mouth closed under the moustache.

## Paint
- SKIN: ruddy pale, warm, weathered, a man about 50; heavy reddish-brown eyebrows; pale grey-blue eyes.
- BEARD AND MOUSTACHE: red-auburn with copper highlights and darker roots, individual combed hairs following the clay's beard shape. All of the clay's beard mass is hair.
- HELMET SHELL: polished pale steel, slightly dented and scratched, as inputs 8 and 10. Back of the shell the same plain steel.
- BAND: the raised band across the forehead, down both sides of the face and round the lower rim is a dark brown leather strip edged with thin pale steel lines, set with small gold studs and gold diamond marks at regular spacing, as inputs 9 and 10.
- HORNS: ivory, cream at the base to pale tan at the tips, fine lengthwise grain; the ribbed collars at their base are brown leather wrapping with a thin gold edge.
- NECK: the plain tube below the helmet at the back and under the beard is a tan rough cloth collar.

Do NOT add a nasal bar, jewellery, extra straps, or hair outside the clay's beard.
