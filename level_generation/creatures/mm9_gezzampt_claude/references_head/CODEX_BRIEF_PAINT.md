# Codex brief: paint the MM9 Gezzampt's head (mm9_gezzampt_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_gezzampt_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game monster, a horned fur-covered beast-man, restored from a 2002 game for a game mod. The result is projected onto a 3D head, so **every painted view must keep the exact outline and feature positions of its clay input**, pixel for pixel: eyes, nose, mouth, teeth, tusks, ears, horns, rim of the mane, chin, jaw. Only surface paint is added. Do not change the shape, do not turn or tilt the head, do not add hair volume beyond the clay's outline.

## Inputs (attached, in order)
1-7. `references_head/clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`, `clay_05_top.png`, `clay_06_q34r.png`, `clay_07_q34l.png`: the clay head, geometry authority.
8. `references_hd/mm9_head_views_a.png`: renders of the ORIGINAL low-poly head, four views: identity, fur layout and colour authority. Ignore the faceting and the shoulders.
9. `references_hd/mm9_skin_x4_a.png`: the original skin enlarged; its face panel top left is the sharpest evidence of the face.
10. `references_head/in_body_head.png`: the high-definition master's head: finish and material authority. Follow its colours and fur.

## Deliverables (true transparent background, same size as the clay, unresized returns, no floor, no shadow, no text)
`references_head/a_01_front.png`, `a_03_left.png`, `a_02_back.png`, `a_04_right.png`, `a_05_top.png`, `a_06_q34r.png`, `a_07_q34l.png`. Generate front first, then use it as an extra input for the others so that all views are the SAME creature with the SAME paint. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_a.json` (id, prompt, inputs with sha256, output path) and `selected_views_review_a.png`.

Even soft studio light, no cast shadows, no rim light, no drama: the paint is a colour map. Semi-realistic game-art materials with sharp detail: short dense fur strands, pores on the bare parts.

## Paint
- FACE: tawny golden short fur on brow, cheeks and nose bridge, darker round the eyes in the sockets. The nose is dark grey-brown bare leather with dark nostrils. Heavy dark brow hair. Amber-orange irises with round black pupils, on the clay's eyeballs, looking straight ahead, a dark lid line. Lips dark brown.
- MOUTH: teeth pale ivory with dark gaps, tusks ivory, darker at the root; everything between and behind them near-black.
- BEARD: the jaw and chin mass is dark brown shaggy fur strands, as input 8, blending into tawny on the cheeks.
- MANE: everything behind the hairline and the crest is very dark brown shaggy fur, strands following the clay's sweep from the brow up and back, then down the neck.
- HORNS: pale bone-yellow with darker ring bands following the clay's grooves.
- EARS: tawny golden short fur, darker pink-brown inside.
- NECK under the jaw: tawny golden at the throat, as input 2's front; dark brown behind.
