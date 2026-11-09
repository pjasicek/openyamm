# Codex brief: paint views on our exact 3D figure, MM9 Concubine (siren skin 1) (mm9_ebora_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_ebora_claude/references_paint/`. No builds, no
Meshy. Use your built-in image generation tool.
A fantasy video-game character: one of Ebora's handmaidens, a horned demon woman in a long-sleeved burgundy brocade
catsuit, a restoration of a 2002 game character for a game mod. Fully clothed, non-sexual, a modelling reference.

These images are the texture reference for a real 3D model. The four clay renders are the EXACT model, orthographic. You
paint her costume onto it. Every silhouette, edge, finger and fold of the clay stays exactly where it is, pixel for pixel
as far as you can: the same framing, the same scale, nothing added outside the clay's outline, nothing removed. Only
surface colour and painted detail are new. The clay has NO wings and the painting has none.

## Inputs (attached, in order)
1-4. `references_paint/clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`: the model.
   Geometry and framing authority. Transparent background.
5. `references_hd/mm9_body_views_siren1.png`: renders of the ORIGINAL low-poly game model in this costume (wings removed),
   five views: three-quarter, front, figure's left, back, figure's right. Costume and colour authority. Grey is
   background; ignore the faceting and blur; the T-pose is not the pose wanted.
6. `references_hd/mm9_head_views_siren1.png`: its head, hair and horns.
7. `references_hd/mm9_chest_views_siren1.png`: its bodice, neckline and sleeves.
8. `references_hd/mm9_legs_views_siren1.png`: its legs and boots.
9. `references_hd/mm9_skin_x4_siren1.png`: the original skin enlarged, material and colour only.

## Deliverables (true transparent background, no floor, no shadow, no text, 1024x1536 PORTRAIT, the same framing as
the clay; do not resize)
`siren_01_front.png`, `siren_03_left.png`, `siren_02_back.png`, `siren_04_right.png`. All four are one consistent
figure. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_siren.json` and
`selected_views_review_siren.png`.

## What goes where on the clay
- SKIN (face, neck, upper chest above the neckline, the open back down to the waist, hands): fair peach human skin, soft
  shading only from form.
- FACE: a fierce beautiful woman of about 25 on the clay's own eyes, nose and mouth: green eyes with pupils, arched dark
  red brows, dark red lips.
- HAIR (the clay's hair shell and the fringe): vivid copper-red straight hair with fine strands, as input 6.
- HORNS (the two horns): black, turning dark red at the tips.
- BODICE AND CATSUIT: one long-sleeved burgundy brocade catsuit with a dark red damask pattern, from the neck down to the
  boots and down the arms to the wrists, as inputs 5 and 7. Deep V neckline edged with black lace; a dark plum-black
  panel over the bust; a black V-shaped panel at the hips and groin as input 7. At the back an open V from the shoulder
  blades down to the waist showing skin, edged with black lace.
- The thin raised band round the hips (belt geometry): a narrow band of black lace. The raised oval at the groin: a dark
  garnet brooch in black metal. The four small spikes on the bust: small black jet ornaments.
- LEGS: burgundy brocade continues down the legs to black knee-high high-heeled boots on the clay's feet, as input 8.
- HANDS: bare peach skin on the clay's long fingers with long pale pink pointed nails.

Camera and light: exactly as inputs 1-4; flat even light, NO cast shadows, no rim light, no strong highlights: an albedo
reference with sharp fine detail.
Do NOT: add wings, a tail, weapons or a cloak; move any edge; change the pose; add a background; show skin anywhere the
catsuit covers.
