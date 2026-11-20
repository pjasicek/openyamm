# Codex brief: paint views on our exact 3D figure, MM9 Evil Sorcerer (mm9_evilsorcerer_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_evilsorcerer_claude/references_paint/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game character, an adult male court sorcerer in ceremonial robes, a restoration of a 2002 game character for a game mod.

These images are the texture reference for a real 3D model. The four clay renders are the EXACT model, orthographic. You paint its costume onto it. Every silhouette, edge, plate, panel, step and fold of the clay stays exactly where it is, pixel for pixel as far as you can: the same framing, the same scale, nothing added outside the clay's outline, nothing removed. Only surface colour and painted ornament are new.

## Inputs (attached, in order)
1-4. `references_paint/clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`: the model. Geometry and framing authority. Grey background.
5-8. `references_hd/01_front.png`, `03_left.png`, `02_back.png`, `04_right.png`: earlier HD concept in the same view, slightly different proportions (longer arms). Costume, ornament, material and colour authority. Follow its design, not its shape.
9. `references_hd/mm9_chest_views_b.png`: the original game model's chest, yoke, shoulder plates and arms.
10. `references_hd/mm9_waist_views_b.png`: the original game model's belt, panels and legs.
11. `references_hd/mm9_skin_x4_b.png`: the original skin enlarged, material and colour only.

## Deliverables (true transparent background, no floor, no shadow, no text, 1024x1536 PORTRAIT, the same framing as the clay; do not resize)
`paint_01_front.png`, `paint_03_left.png`, `paint_02_back.png`, `paint_04_right.png`. All four are one consistent figure. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, reason) and `selected_views_review.png`.

## What goes where on the clay (read the plates off the clay's edges)
- FRONT YOKE, the raised plate on the chest ending in a low V: embossed brass-and-red-enamel filigree, a small brass demon face at the centre of the chest, a thin bright brass rim following the plate's edge exactly.
- BACK YOKE, the raised plate on the upper back ending in a low V: the same filigree without the face, same rim.
- COLLAR: the raised rim round the neck: dark grey wool undershirt inside it, brass at its outer edge.
- PAULDRONS: the two big shoulder plates, including their upward peak: embossed brass dragon filigree on red enamel, bright brass rim following every edge.
- TUNIC below the yokes, to the belt: dark charcoal padded wool with shallow vertical quilting. SLEEVES above the bracers: dark grey wool.
- BRACERS, the raised sleeve cuffs on the forearm: stiff olive brass with a darker zigzag upper edge and two small red cabochon gems on the outer face.
- HANDS: warm tanned bare skin, knuckles, fingernails, no gloves.
- BELT: plaited brass knotwork. BUCKLE: the large central lump on the belt: a brass demon face with red eyes.
- FRONT PANEL and BACK PANEL, the long central plates from the belt to the shin: red silk damask with gold scrollwork as in inputs 5-8 and a thin bright brass edge following the plate's outline, including its pointed lower end.
- HIP FLAPS, the short pointed plates at the hips, front and back: the same red damask, gold scroll, brass edge.
- LEGS: slim charcoal wool trousers. A brass ring band round the top of the boot.
- GREAVES, the long pointed plates on the shins: red enamel with raised gold scrollwork, brass edge.
- BOOTS: charcoal, the raised top edge is the brass ring. SHOES: black leather with brass trim.
- HEAD: paint a plausible head only (a dark-bearded man, a red and gold crown): it is replaced later, do not spend effort on it.

Camera and light: exactly the clay's camera; flat even light, NO cast shadows, no rim light, no ambient occlusion darkening, no strong highlights: this is an albedo reference with the fine ornament sharp.
Do NOT: add a cape, a staff, weapons or extra plates; move any edge; change the pose; add a background; blur the ornament.
