# Codex brief: tier A paint views, MM9 Evil Apprentice (mm9_evilsorcerer_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_evilsorcerer_claude/references_paint/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game character, an adult male court sorcerer in ceremonial robes, a restoration of a 2002 game character for a game mod.

You repaint the SAME figure in the costume of its lowest rank. Every silhouette, edge, plate, panel, step and fold of inputs 1-4 stays exactly where it is, pixel for pixel as far as you can: the same framing, scale and pose. Only surface paint changes.

## Inputs (attached, in order)
1-4. `references_paint/paint_01_front_clean.png`, `paint_03_left_clean.png`, `paint_02_back_clean.png`, `paint_04_right_clean.png`: the figure already painted in its middle rank (red and gold). Geometry and framing authority; which part is which.
5-8. `references_paint/clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`: the bare model, the same framing.
9. `references_hd/mm9_views_a.png`: renders of the ORIGINAL low-poly model in this rank, five views: three-quarter, front, figure's left, back, figure's right. Costume and colour authority. Grey is background, ignore the faceting.
10. `references_hd/mm9_waist_views_a.png`: close renders of its belt, panels and legs.
11. `references_hd/mm9_chest_views_a.png`: close renders of its chest and arms.
12. `references_hd/mm9_skin_x4_a.png`: the original skin enlarged, material and colour only.

## Deliverables (true transparent background, no floor, no shadow, no text, 1024x1536 PORTRAIT, the same framing as inputs 1-4; do not resize)
`a_01_front.png`, `a_03_left.png`, `a_02_back.png`, `a_04_right.png`. One consistent figure. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_a.json` and `selected_views_review_a.png`.

## Tier A costume (Evil Apprentice), part by part, as inputs 9-11
- FRONT PANEL and BACK PANEL (the long central plates): plain dark navy-blue wool, a fine vertical weave, NO ornament, NO scrollwork, a thin bright gold edge following the outline.
- HIP FLAPS: plain dark navy-blue wool, the same thin gold edge.
- THIGHS, from under the belt down to about the knee: deep sea-green wool with a fine weave, ending in a curved thin gold piping at the knee as input 10. Below that piping the LOWER LEGS and BOOTS are plain matt black.
- GREAVES, the long pointed shin plates: plain dull grey steel, slightly scuffed, a thin gold edge. NO ornament.
- BRACERS: dark brown tooled leather with a fine swirl, thin gold edge at both ends, two dark round studs where the higher rank has gems.
- SHOES: black with dark teal insets and gold trim, as input 10.
- SLEEVES: sea-green wool. TUNIC: dark navy-blue wool with a sea-green stripe down each side, as input 11.
- YOKES and PAULDRONS: dark navy-blue with a dark green knotwork filigree, a bright gold rim on every edge, as input 11. The small demon face at the chest stays brass.
- BELT and BUCKLE: unchanged, brass.
- HANDS: unchanged.
- HEAD: paint a plausible young man with a navy and gold crown: it is replaced later, do not spend effort on it.

Camera and light: exactly as inputs 1-4; flat even light, NO cast shadows, no rim light, no strong highlights: an albedo reference with sharp fine detail.
Do NOT: add a cape, a staff, weapons or extra plates; move any edge; change the pose; add a background; keep any red or gold scrollwork on the panels, flaps or greaves.
