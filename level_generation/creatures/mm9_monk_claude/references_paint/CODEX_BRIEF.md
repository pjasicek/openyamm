# Codex brief: paint views on our exact 3D figure, MM9 Monk (mm9_monk_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_monk_claude/references_paint/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game character, an adult male medieval monk in a plain wool habit, a restoration of a 2002 game character for a game mod.

These images are the texture reference for a real 3D model. The four clay renders are the EXACT model, orthographic. You paint its costume onto it. Every silhouette, edge, fold and step of the clay stays exactly where it is, pixel for pixel as far as you can: the same framing, the same scale, nothing added outside the clay's outline, nothing removed. Only surface colour and painted cloth detail are new.

## Inputs (attached, in order)
1-4. `references_paint/clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`: the model. Geometry and framing authority. Transparent background. The figure runs a little past the frame at the top and bottom of nothing: keep the same crop.
5-8. `references_hd/01_front.png`, `03_left.png`, `02_back.png`, `04_right.png`: earlier HD concept in the same view, slightly different proportions. Costume, material and colour authority. Follow its design, not its shape.
9. `references_hd/mm9_chest_views_a.png`: the original game model's hood, mantle, sleeves and hands.
10. `references_hd/mm9_waist_views_a.png`: the original game model's rope.
11. `references_hd/mm9_skin_x4_a.png`: the original skin enlarged, material and colour only: a coarse linen-like wool weave, warm mid brown.

## Deliverables (true transparent background, no floor, no shadow, no text, 1024x1536 PORTRAIT, the same framing as the clay; do not resize)
`paint_01_front.png`, `paint_03_left.png`, `paint_02_back.png`, `paint_04_right.png`. All four are one consistent figure. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, reason) and `selected_views_review.png`.

## What goes where on the clay
- ROBE, MANTLE, HOOD, SLEEVES: all one coarse woven wool in warm mid brown, the same cloth everywhere: a visible even crosshatch weave of thick threads, as input 11. Very gentle darker tone in the deepest folds only. NO pattern, NO stripes, NO trim, NO embroidery, NO patches. The edge of the mantle, the rim of the hood and the rims of the cuffs are a very slightly darker line, nothing more.
- INSIDE of the cuffs, of the hood round the face and under the hem: plain dark brown, almost black.
- ROPE (the belt round the waist, the two hanging cords, their knots): twisted hemp, tan and honey, sharply drawn strands, a clear spiral lay along the rope. The two end knots the same hemp with a short frayed tuft.
- FOREARMS AND HANDS: warm bare skin, knuckles, fingernails, no gloves.
- SHOES: warm tan soft leather.
- HEAD: paint a plausible plain face only: it is replaced later, do not spend effort on it.

Camera and light: exactly the clay's camera; flat even light, NO cast shadows, no rim light, no ambient occlusion darkening, no strong highlights: this is an albedo reference with the weave sharp.
Do NOT: add a cross, beads, a book, a pouch, a staff; move any edge; change the pose; add a background; blur the weave; paint folds that are not in the clay.
