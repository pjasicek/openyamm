# Codex brief: head paint on our exact 3D head, MM9 Ebora (mm9_ebora_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_ebora_claude/references_head/`. No builds, no Meshy.
Use your built-in image generation tool.
A fantasy video-game character: Ebora, a demon queen with red skin, horns and black hair, a restoration of a 2002 game
character for a game mod. A head-and-shoulders modelling reference, non-sexual.

These images are the TEXTURE reference for a real 3D head. The eight clay renders are the EXACT model (orthographic). Paint
her onto it: every silhouette, the eyes, nose, mouth, ears, hairline, hair masses and horns stay exactly where the clay has
them, pixel for pixel as far as you can, same framing and scale, nothing added outside the clay outline. Only colour and
painted detail are new. The 08_face view is a CLOSE view of the face and matters most.

## Inputs (attached, in order)
1-8. `references_head/clay_08_face.png` (close face), `clay_01_front.png`, `clay_06_q34r.png` (three-quarter from her right),
   `clay_07_q34l.png` (three-quarter from her left), `clay_03_left.png` (her left side, faces image left), `clay_04_right.png`
   (her right side, faces image right), `clay_02_back.png`, `clay_05_top.png`. Geometry and framing authority.
9. `references_hd/mm9_head_views_ebora.png`: the ORIGINAL game model's head with its skin (five views). Look authority:
   red skin, the eye look, dark lips, black hair. Ignore its blur and faceting.
10. `references_hd/01_front.png`: an HD concept of Ebora. Face style and materials (follow the clay's shape, not its shape).

## Deliverables (true transparent background, 1254x1254, same framing as each clay, unresized)
`a_08_face.png`, `a_01_front.png`, `a_06_q34r.png`, `a_07_q34l.png`, `a_03_left.png`, `a_04_right.png`, `a_02_back.png`,
`a_05_top.png`. Paint 08_face FIRST; every other view must show the SAME face, skin tone and hair (use 08_face as a reference
for them). At most one corrective regeneration per view. Raw returns in `raw/`; `generation_runs_head.json`;
`selected_views_review_head.png`.

## Paint
- SKIN: saturated deep red-orange demon skin (about RGB 205,55,25 in mid light, darker 150,25,10 in the creases), with SOFT
  form shading (darker under the brows, along the nose sides, under the cheekbones and the lower lip, under the jaw), a faint
  warmer flush on cheeks and nose, fine skin texture. Not flat: a mature, refined painted-realistic face.
- EYES (on the clay's eye shapes exactly): almond eyes that read from far away: bright pale white-grey eyes with a faint
  pale iris ring and no dark pupil (her look in input 9), a crisp dark upper lash line and a thin lower line, a soft shadow
  in the upper lid crease. Crisp edges, no smearing, both eyes the same size and level.
- BROWS: thin, sharply arched, clearly defined black brows. NOSE: defined bridge highlight, nostrils, soft shadow beside
  the nose. LIPS: dark plum-crimson lips with a crisp outline, a darker line between the lips, a small highlight on the
  lower lip; mouth closed, a cold slight smile.
- HAIR (the clay's hair shell and its fringe): glossy jet-black hair painted as clear STRAND GROUPS (locks 1-2 cm wide)
  following the clay's hair flow from the crown and the side parting, each lock with a soft blue-grey sheen highlight
  along its length, dark gaps between locks. Not a noisy mat of thin lines. The hairline is a clean edge: skin paint
  never on the hair, hair paint never on the skin. NO strand hanging onto the forehead or face: the forehead stays skin.
- HORNS: dark grey-black with pale bone ridged rings. EARS: red skin.
- NECK and shoulders below the jaw: the same red skin, a soft shadow under the jaw.
- Light: flat, even studio light, NO cast shadows, no rim light, no strong specular: an albedo reference with painted
  form shading only.

Do NOT: add pupils, jewellery, a crown, extra hair locks over the face; move any edge; change the pose; add a background.
