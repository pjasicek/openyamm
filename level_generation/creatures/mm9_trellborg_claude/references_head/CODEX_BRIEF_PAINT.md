# Codex brief: paint the MM9 Trellborg's head (mm9_trellborg_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_trellborg_claude/references_head/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game monster, a big orc-like tribesman, restored from a 2002 game for a game mod. The result is projected onto a 3D head, so **every painted view must keep the exact outline and feature positions of its clay input**, pixel for pixel: eyes, nose, mouth, tusks, ears, every hair lock. The paint goes ON the clay; nothing moves.

## Inputs (attached, in order)
1-5. `references_head/clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`, `clay_05_top.png`: the clay head, geometry authority.
6. `references_head/in_body_head.png`: the high-definition master's head: identity, colour and material authority.
7. `references_hd/mm9_skin_x4_a.png`: the original skin enlarged; its face and hair panel top left is the sharpest evidence of the face.

## Deliverables (true transparent background, same size as the clay, unresized returns, no floor, no shadow, no text)
`references_head/a_01_front.png`, `a_03_left.png`, `a_02_back.png`, `a_04_right.png`, `a_05_top.png`. Generate front first, then use it as an extra input for the others so that all views are the SAME creature with the SAME paint. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_paint.json`.

Even soft studio light, no cast shadows, no rim light, no drama: the paint is a colour map. Semi-realistic game-art materials with sharp detail: pores and leathery creases on the skin, individual hair strands following each lock.

## Paint
- FACE: red-brown tan leathery skin, warmer rust on the nose and cheeks, paler ochre highlights on the brow and cheekbones, grey-brown shading in the eye sockets and round the mouth, as input 6.
- EYES: small, deep-set, on the clay's eye openings: amber-orange irises with round black pupils, dark lid lines, pale eye whites only at the corners. Looking straight ahead. Paint them exactly in the clay's eye slits, the same size on both sides.
- MOUTH: dark brown lips with a near-black parting line along the clay's mouth line. The tusks stay pale ivory, darker at the root.
- BEARD: a short rust-red beard on the chin wedge only, strands going down, soft edge into the jaw skin. Thin stubble line along the jaw.
- HAIR: every lock dark auburn: near-black in the grooves, deep red-brown strands, a few lighter rust strands on the ridges, following the clay's sweep from the brow up and back and down to each pointed tip. The hairline on the forehead is clear.
- EARS: same skin as the face, darker pink-brown inside. A small gold ring in the lobe of each ear.
- NECK: same skin as the chest, red-brown, no strap.

Do NOT paint a background, a body, straps or light effects. Do NOT change any outline.
