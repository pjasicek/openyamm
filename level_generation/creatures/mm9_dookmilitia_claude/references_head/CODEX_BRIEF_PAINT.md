# Codex brief: paint the MM9 Half Orc's head, three tiers (mm9_dookmilitia_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_dookmilitia_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game character, an adult male half-orc soldier in a helmet, restored from a 2002 game for a game mod. The result is projected onto a 3D head, so **every painted view must keep the exact outline and feature positions of its clay input**, pixel for pixel: eyes, nose, mouth, ears, helmet rim, cheek straps, spikes, coif, chin, jaw. Only surface paint is added. Do not change the shape, do not turn or tilt the head, do not add volume beyond the clay's outline.

## Inputs (attached, in order)
1-7. `references_head/clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`, `clay_05_top.png`, `clay_06_q34r.png`, `clay_07_q34l.png`: the clay head with the bare V of the chest below the neck, geometry authority.
8. `references_hd/mm9_head_views_<tier>.png`: renders of the ORIGINAL low-poly head, five views: three-quarter, front, figure's left, back, figure's right: identity, helmet design and colour authority. Ignore the faceting and the chest. In a front view the figure's LEFT is on IMAGE RIGHT.
9. `references_hd/mm9_skin_x4_<tier>.png`: the original skin enlarged; its face panel top left is the sharpest evidence of the face; the leather or chain beside it the helmet's material.

## Deliverables (true transparent background, same size as the clay, unresized returns, no floor, no shadow, no text)
For tier X: `references_head/<x>_01_front.png`, `<x>_03_left.png`, `<x>_02_back.png`, `<x>_04_right.png`, `<x>_05_top.png`, `<x>_06_q34r.png`, `<x>_07_q34l.png`. Generate front first, then use it as an extra input for the others so that all views are the SAME man with the SAME paint. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_<x>.json` (id, prompt, inputs with sha256, output path) and `selected_views_review_<x>.png`.

Even soft studio light, no cast shadows, no rim light, no drama: the paint is a colour map. Semi-realistic game-art materials with sharp detail: skin pores, stubble, stitched leather, individual mail rings. Eyes open, irises clearly drawn, each eye one iris only, mouth closed. Dark, muted colours as input 8: no bright orange, no saturated red.

## All tiers
Skin: tawny brown half-orc skin, warm but not orange. Dark deep-set brown eyes, heavy dark brows. Ears: the same skin, pointed, darker in the folds. On each cheek strap: dark leather with thin gold edges and two small silver studs. Spikes: black horn. Below the chin the neck is the same skin; the V below it is dark mail rings. Nothing of skin shows on the helmet.

## Tier A (Recruit): skin file a
Coarse young half-orc, two short pale lower tusks painted rising from the lower lip beside the mouth, a shadow of dark goatee on the chin. Skull cap, rim: dark reddish-brown stitched leather. Coif: very dark brown leather, a thin gold line round the back of the head at rim level, as input 8.

## Tier B (Soldier): skin file b
The same half-orc as tier A, same two tusks, slightly older and harder. Skull cap, rim and coif: all dark steel-grey CHAIN MAIL, round rings clearly drawn; the rim a band of denser mail, as input 8.

## Tier C (Captain): skin file c
An older, calmer half-orc, no tusks, closed firm mouth, a neat black goatee with a thin moustache line, heavy black brows, as input 9. Skull cap and rim: dark polished STEEL, rivets on the rim; coif: dark chain mail with a band of small rivets at rim level, as input 8.

Do NOT add hair, a beard beyond the above, jewellery or a visor.
