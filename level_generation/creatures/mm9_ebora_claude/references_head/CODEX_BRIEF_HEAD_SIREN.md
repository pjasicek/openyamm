# Codex brief: head paint on our exact 3D head, MM9 Concubine, siren skin 1 (mm9_ebora_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_ebora_claude/references_head/`. No builds, no Meshy.
Use your built-in image generation tool.
A fantasy video-game character: one of Ebora's handmaidens, a horned demon woman with fair skin and copper-red hair, a restoration of a 2002 game
character for a game mod. A head-and-shoulders modelling reference, non-sexual.

These images are the TEXTURE reference for a real 3D head. The eight clay renders are the EXACT model (orthographic). Paint
her onto it: every silhouette, the eyes, nose, mouth, ears, hairline, hair masses and horns stay exactly where the clay has
them, pixel for pixel as far as you can, same framing and scale, nothing added outside the clay outline. Only colour and
painted detail are new. The 08_face view is a CLOSE view of the face and matters most.

## Inputs (attached, in order)
1-8. `references_head/clay_08_face.png` (close face), `clay_01_front.png`, `clay_06_q34r.png` (three-quarter from her right),
   `clay_07_q34l.png` (three-quarter from her left), `clay_03_left.png` (her left side, faces image left), `clay_04_right.png`
   (her right side, faces image right), `clay_02_back.png`, `clay_05_top.png`. Geometry and framing authority.
9. `references_hd/mm9_head_views_siren1.png`: the ORIGINAL game model's head with its skin (five views). Look authority:
   red skin, the eye look, dark lips, black hair. Ignore its blur and faceting.
10. `references_hd/mm9_skin_x4_siren1.png`: the original skin enlarged (top-left: her face and hair), colour only.

## Deliverables (true transparent background, 1254x1254, same framing as each clay, unresized)
`s_08_face.png`, `s_01_front.png`, `s_06_q34r.png`, `s_07_q34l.png`, `s_03_left.png`, `s_04_right.png`, `s_02_back.png`,
`s_05_top.png`. Paint 08_face FIRST; every other view must show the SAME face, skin tone and hair (use 08_face as a reference
for them). At most one corrective regeneration per view. Raw returns in `raw/`; `generation_runs_head_siren.json`;
`selected_views_review_head_siren.png`.

## Paint
- SKIN: fair warm peach human skin (about RGB 222,152,109 in mid light, 170,100,70 in the creases), SOFT form shading
  (under the brows, nose sides, under the cheekbones and lower lip, under the jaw), a faint rosy flush on cheeks, fine skin
  texture. A fierce, beautiful woman of about 25. Not flat.
- EYES (on the clay's eye shapes exactly): almond eyes that read from far away: green irises with dark pupils and white
  sclera, a crisp dark upper lash line and thin lower line, a soft shadow in the upper lid crease. Crisp, both the same.
- BROWS: thin, sharply arched, clearly defined dark red-brown brows. NOSE: defined bridge highlight, nostrils, soft shadow beside
  the nose. LIPS: dark red lips with a crisp outline, a darker line between the lips, a small highlight on the
  lower lip; mouth closed, a cold slight smile.
- HAIR (the clay's hair shell and its fringe): vivid copper-red hair painted as clear STRAND GROUPS (locks 1-2 cm wide)
  following the clay's hair flow from the crown and the side parting, each lock with a soft golden-orange sheen highlight
  along its length, dark gaps between locks. Not a noisy mat of thin lines. The hairline is a clean edge: skin paint
  never on the hair, hair paint never on the skin. NO strand hanging onto the forehead or face: the forehead stays skin.
- HORNS: black, turning dark red at the tips. EARS: skin.
- NECK and shoulders below the jaw: the same skin, a soft shadow under the jaw.
- Light: flat, even studio light, NO cast shadows, no rim light, no strong specular: an albedo reference with painted
  form shading only.

Do NOT: jewellery, a crown, extra hair locks over the face; move any edge; change the pose; add a background.
