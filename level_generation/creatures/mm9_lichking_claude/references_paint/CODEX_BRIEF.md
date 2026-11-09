# Codex brief: paint views on our exact 3D figure, MM9 Lich King (mm9_lichking_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_lichking_claude/references_paint/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game character, an undead skeleton king in ornate dark armour, a restoration of a 2002 game character for a game mod.

These images are the texture reference for a real 3D model. The four clay renders are the EXACT model, orthographic. You paint its costume onto it. Every silhouette, edge, plate, panel, step and fold of the clay stays exactly where it is, pixel for pixel as far as you can: the same framing, the same scale, nothing added outside the clay's outline, nothing removed. Only surface colour and painted ornament are new.

## Inputs (attached, in order)
1-4. `references_paint/clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`: the model. Geometry and framing authority. Transparent background.
5-8. `references_hd/01_front.png`, `03_left.png`, `02_back.png`, `04_right.png`: earlier HD concept in the same view, slightly different proportions. Costume, ornament, material and colour authority. Follow its design, not its shape.
9. `references_hd/mm9_chest.png`: the original game model's chest, shoulder plates and arms.
10. `references_hd/mm9_waist.png`: the original game model's belt, front panel, coat and legs.
11. `references_hd/mm9_skin_x4.png`: the original skin enlarged, material and colour only.

## Deliverables (true transparent background, no floor, no shadow, no text, 1024x1536 PORTRAIT, the same framing as the clay; do not resize)
`paint_01_front.png`, `paint_03_left.png`, `paint_02_back.png`, `paint_04_right.png`. All four are one consistent figure. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, reason) and `selected_views_review.png`.

## What goes where on the clay (read the plates off the clay's edges)
- SKULL inside the crown: pale cold bone with a faint blue-grey tint, dark deep eye sockets with a red-orange ember glow, teeth, the open mouth dark with a faint green glow. (It has its own paint later; keep it simple and in place.)
- CROWN-HELM, the tall piece round the skull with five points and the side and back plates: blackened steel with fine silver knotwork, a band of alternating red and turquoise cabochon gems round the brow, a large turquoise gem under the centre point, bright silver rims along every edge and point.
- COLLAR, the ring round the neck under the skull: blackened steel with a silver rim.
- COLLAR POINTS, the two tall thin spikes rising beside the neck: polished silver.
- SHOULDER PLATES, the two big wide flaring plates: engraved silver knotwork on blackened steel, a bright silver rim along every edge and point.
- BREASTPLATE, the torso from the collar to the belt: dark blue-black engraved steel with silver knotwork filigree, a darker blue engraved panel on the lower chest. The three raised round medallions on the upper chest (one big at the centre, two smaller beside it): silver discs, each with a skull relief.
- BACK: the coat starts at the shoulders and covers the whole back: heavy dark navy-black wool with soft vertical folds; the two raised round discs on the shoulder blades: silver skull medallions.
- SLEEVES, the upper arm tubes: black ribbed lacquered armour, horizontal ridges with silver highlights.
- BRACERS, the long raised forearm cuffs: silver knotwork on black, a silver rim at both ends.
- HANDS: black articulated gauntlets, steel plates on each finger joint, silver highlights.
- BELT round the waist: black leather with silver trim. BUCKLE, the large oval lump at the front of the belt: a silver skull relief with a turquoise gem above it.
- FRONT PANEL, the long flat plate hanging from the belt to the shin: silver knotwork on black with a bright silver edge, a skull at its top.
- COAT below the belt, the long open garment round the sides and back of the legs, down to the ankles at the back: heavy dark navy-black wool, soft folds, a thin dark silver edge on its front edges and hem. Its INSIDE (seen through the open front): plain very dark navy lining.
- LEGS (thighs): black ribbed lacquered armour plates. BOOTS, from the knee to the sole: black armour with silver knotwork trim, the winged knee guard at the top; the raised round disc on each knee: a silver skull medallion.

Camera and light: exactly the clay's camera; flat even light, NO cast shadows, no rim light, no ambient occlusion darkening, no strong highlights: this is an albedo reference with the fine ornament sharp.
Do NOT: add a staff, weapons, a cape over the shoulders, hair, or extra plates; move any edge; change the pose; add a background; blur the ornament.
