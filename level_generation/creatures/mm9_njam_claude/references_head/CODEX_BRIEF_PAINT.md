# Codex brief v2: paint the head of MM9's Njam the Meddler (mm9_njam_claude)

This is the second paint. The first (kept in `references_head/v1/`) read as a gaunt, droopy, tired man with small eyes and soft features; this one must read as MM9's Njam: younger, sharper, smug, with clear bright eyes.

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_njam_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game character, an adult male courtier (a trickster god in human form), restored from a 2002 game for a game mod. The result is projected onto a 3D head, so **every painted view must keep the exact outline and feature positions of its clay input**, pixel for pixel: eyes, nose, mouth, hairline, fringe edge, chin, jaw, rim of the hair. Only surface paint is added. Do not change the shape, do not turn or tilt the head, do not add hair volume beyond the clay's outline.

## Inputs (attached, in order)
1-8. `references_head/clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`, `clay_05_top.png`, `clay_06_q34r.png`, `clay_07_q34l.png`, `clay_08_face.png` (a CLOSE front view of the face only, the same head at about twice the size): the clay head and neck, geometry authority. The eyes are smooth bulges in the clay: paint open eyes ON them (white, iris, pupil, lids, lashes) exactly where the bulges are.
9. `references_hd/mm9_head_views.png`: renders of the ORIGINAL low-poly head, five views: three-quarter, front, figure's left, back, figure's right: identity, hair and colour authority. Ignore the faceting and the costume. In a front view the figure's LEFT is on IMAGE RIGHT.
10. `references_head/in_body_head.png`: the body master's head: hair colour and paint quality only. Do NOT copy its tired, droopy expression or its age.

## Deliverables (true transparent background, same size as the clay, unresized returns, no floor, no shadow, no text)
`references_head/a_08_face.png` FIRST (the close face: this is the most important image, the face on the model comes from it alone), then `a_01_front.png`, `a_03_left.png`, `a_02_back.png`, `a_04_right.png`, `a_05_top.png`, `a_06_q34r.png`, `a_07_q34l.png`, each with `a_08_face.png` as an extra input so that all views are the SAME man with the SAME paint. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_a.json` (id, prompt, inputs with sha256, output path) and `selected_views_review_a.png`.

Even soft studio light, no cast shadows, no rim light, no drama: the paint is a colour map. Semi-realistic game-art materials with sharp detail: skin pores, light stubble, individual hair strands combed along the clay's hair mass. Eyes open, pale green-blue irises clearly drawn, the two eyes level and alike. The clay's whole hair mass is hair, nothing of the skin shows through it. The neck is bare warm skin down to the bottom of the clay.

## The man
MM9's Njam the Meddler, a trickster god in human form: a YOUNG man of about 28, lean but healthy (not gaunt, no hollow cheeks, no bags or
dark rings under the eyes), fair warm skin with a light natural flush, high cheekbones, a straight well-shaped nose (crisp bridge and tip,
clear nostrils), a clean defined jaw and chin. His expression is SMUG and knowing, a meddler enjoying a private joke: one eyebrow slightly
raised, the eyes bright, alert and wide open (not droopy, upper lids lifted), a confident one-sided smirk with the mouth CLOSED, the lips
clearly drawn with a crisp lip line. EYES: clear pale green-blue irises with dark rims, crisp black pupils, white sclera, sharp catchlights,
both eyes level, alike and well open. A light trimmed stubble shadow on the jaw, chin and upper lip only (no beard, no moustache). Every
feature sharp and in focus: crisp edges, fine skin texture, no blur, no smudge.
HAIR: medium chestnut-brown with warm lighter strands, combed straight down from the crown into a soft PAGEBOY: a blunt fringe over the
forehead whose lower edge rolls under (paint the rim and the underside of the fringe as hair, a little darker, never skin and never black),
hanging to the jaw at the sides and to the nape at the back with the ends rolling softly under; individual strands follow the clay's mass.
Where the hair meets the cheeks and the forehead, the hair's edge is a clean hair edge and the skin starts below it.

Do NOT add a helmet, a hat, a crown, a hood, a headband, ears or jewellery.
