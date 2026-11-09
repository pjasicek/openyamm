# Codex brief: paint the MM9 Bigfoot's head (mm9_bigfoot_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_bigfoot_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game ape-man restored from a 2002 game for a game mod. The result is projected onto a 3D head, so **every painted view must keep the exact outline and feature positions of its clay input**, pixel for pixel: eyes, nose, mouth, ears, brow, crest, chin. Only surface paint is added. Do not change the shape, do not turn or tilt the head, do not add hair volume beyond the clay's outline.

## Inputs (attached, in order)
1-5. `clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`, `clay_05_top.png`: the clay head, geometry authority.
6. `references_hd/mm9_head_views_a.png`, 7. `references_hd/mm9_skin_x4_a.png`: original Bigfoot head and skin: identity, fur layout, colour.
8. `references_hd/mm9_head_views_c.png`, 9. `references_hd/mm9_skin_x4_c.png`: original Yeti head and skin: identity, fur layout, colour.

## Deliverables (true transparent background, same size as the clay, unresized returns, no floor, no shadow, no text)
Tier a (Bigfoot): `a_01_front.png`, `a_03_left.png`, `a_02_back.png`, `a_04_right.png`, `a_05_top.png`.
Tier c (Yeti): `c_01_front.png`, `c_03_left.png`, `c_02_back.png`, `c_04_right.png`, `c_05_top.png`.
Generate each front first, then use it as an extra input for that tier's other views. One corrective regeneration at most. Keep raw returns in `raw/`. Write `generation_runs_a.json` (id, prompt, inputs with sha256, output path).
Even soft studio light, no cast shadows, no rim light: the paint is a colour map. Semi-realistic game-art materials with sharp detail: short dense fur strands, pores and wrinkles on the bare face.

## Paint, tier a (Bigfoot)
- CREST: from the brow up over the crown, striped swept hair, golden tan with dark brown bands, as input 6; it ends in the fringe along the brow ridge.
- FACE: bare dark grey-brown leather, deep wrinkles darker, small amber eyes with black pupils, pale pinkish-grey muzzle and nose with near-black nostrils, thin dark closed lips with a near-black line between them. Dark brown short beard on the chin and cheek edges.
- BACK and SIDES: dark reddish-brown fur flowing down. EARS: pale grey-pink skin, dark inside.

## Paint, tier c (Yeti)
- FUR everywhere: pale blue-white fur. CREST: white with strong saturated blue bands, as input 8. Blue shading round the cheeks.
- EYES: orange-amber with black pupils in a black-brown band of skin under the brow.
- NOSE: pale pink-grey with dark nostrils.
- MOUTH: paint on the clay's muzzle, at the clay's mouth position and about the width of the mouth, a wide open snarl as input 8: a black rounded rectangle with two rows of sharp ivory-white teeth, longer fangs at the corners, black lips round it.
- EARS: red-brown inside with a dark rim.
