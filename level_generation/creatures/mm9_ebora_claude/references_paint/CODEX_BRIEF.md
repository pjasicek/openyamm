# Codex brief: paint views on our exact 3D figure, MM9 Ebora (mm9_ebora_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_ebora_claude/references_paint/`. No builds, no
Meshy. Use your built-in image generation tool.
A fantasy video-game character: Ebora, a demon queen with red skin, horns and a black armoured corset, a restoration of a
2002 game character for a game mod. Fully clothed villain, non-sexual, a modelling reference.

These images are the texture reference for a real 3D model. The four clay renders are the EXACT model, orthographic. You
paint her costume onto it. Every silhouette, edge, plate, finger and fold of the clay stays exactly where it is, pixel for
pixel as far as you can: the same framing, the same scale, nothing added outside the clay's outline, nothing removed.
Only surface colour and painted detail are new. The clay has NO wings and the painting has none.

## Inputs (attached, in order)
1-4. `references_paint/clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`: the model.
   Geometry and framing authority. Transparent background.
5-8. `references_hd/01_front.png`, `03_left.png`, `02_back.png`, `04_right.png`: the HD concept in the same views,
   slightly different proportions. Costume, material and colour authority. Follow its design, not its shape.
9. `references_hd/mm9_chest_views_ebora.png`: the original game model's corset, cups, belt and arms.
10. `references_hd/mm9_legs_views_ebora.png`: the original game model's legs and boots.
11. `references_hd/mm9_head_views_ebora.png`: the original game model's head, hair and horns.

## Deliverables (true transparent background, no floor, no shadow, no text, 1024x1536 PORTRAIT, the same framing as
the clay; do not resize)
`paint_01_front.png`, `paint_03_left.png`, `paint_02_back.png`, `paint_04_right.png`. All four are one consistent
figure. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs.json` (id,
prompt, inputs with sha256, output path, reason) and `selected_views_review.png`.

## What goes where on the clay
- SKIN (face, neck, shoulders, upper chest, upper arms down to just above the elbow, the small of the back above the
  corset): smooth saturated ORANGE-RED skin, soft shading only from form, no cast shadows.
- FACE: haughty, high cheekbones, arched black brows, fully WHITE eyes with no pupils, dark plum lips, on the clay's own
  eyes, nose and mouth exactly.
- HAIR (the clay's hair shell and the fringe over the forehead): glossy straight black hair with fine strands.
- HORNS (the two horns): dark grey-black with pale ridged rings.
- CORSET (from the bust to the hips): black leather. The two BREAST CUPS: engraved dark silver, a small silver skull at
  the centre of each. The two small spikes at the top of each cup (geometry on the clay): polished silver. Belly: overlapping
  horizontal dark-silver scale plates down the front. Back: black leather laced up the spine with a silver spine ridge.
  Thin black shoulder straps over the shoulders.
- BELT (the thin raised band round the hips): a gold-and-silver chain. The raised oval at the groin: a dark silver plate
  with a silver skull emblem, with dark silver plate continuing down between the legs.
- LEGS: glossy black-blue leather leggings; on the FRONT of each thigh and shin a vertical band of pale bone-silver studs
  and plates as inputs 5 and 10; black high-heeled boots on the clay's feet with a silver heel.
- ARMS: black leather GLOVES from just above the elbow down over the hands and every finger; long black claw tips on
  the clay's long finger ends.

Camera and light: exactly as inputs 1-4; flat even light, NO cast shadows, no rim light, no strong highlights: an albedo
reference with sharp fine detail.
Do NOT: add wings, a tail, weapons or a cloak; move any edge; change the pose; add a background; give her pupils.
