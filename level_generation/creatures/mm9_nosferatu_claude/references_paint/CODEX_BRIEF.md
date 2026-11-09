# Codex brief: paint views on our exact 3D figure, MM9 Nosferatu (mm9_nosferatu_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_nosferatu_claude/references_paint/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game creature, a goblin-faced undead noble in a long ceremonial robe, a restoration of a 2002 game monster for a game mod.

These images are the texture reference for a real 3D model. The four clay renders are the EXACT model, orthographic. You paint its costume onto it. Every silhouette, edge, plate, fold and step of the clay stays exactly where it is, pixel for pixel as far as you can: the same framing, the same scale, nothing added outside the clay's outline, nothing removed. Only surface colour and painted ornament are new.

## Inputs (attached, in order)
1-4. `references_paint/clay_01_front.png`, `clay_03_left.png`, `clay_02_back.png`, `clay_04_right.png`: the exact model. Geometry and framing authority.
5-8. `references_hd/01_front.png`, `03_left.png`, `02_back.png`, `04_right.png`: the approved high-definition figure: costume, colours, materials and pattern authority. Its proportions differ a little from the clay: the clay wins.
9. `references_hd/mm9_chest_views_b.png`: the original model's chest, sleeves and hands.
10. `references_hd/mm9_skin_x4_b.png`: the original skin enlarged, surface material and colour only.

## Deliverables (true transparent background, no floor, no shadow, no text, 1024x1536 PORTRAIT, the same framing as inputs 1-4; do not resize)
`paint_01_front.png`, `paint_03_left.png`, `paint_02_back.png`, `paint_04_right.png`. Generate the front first, then use it as an extra input for the others, so they are the same figure with the same paint. At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs.json` and `selected_views_review.png`.

## The paint, part by part (the clay's parts)
- ROBE, from the belt down to the hem: deep blood-red silk damask with a darker tone-on-tone woven pattern of scrolls, diamonds, eyes and circles, as inputs 5-8. A soft even sheen, no strong light. Pattern scale as input 5: the circles about 12 cm across.
- CENTRE PANEL on the robe's front: from the belt to the hem, a straight panel about 16 cm wide, nearly black olive, edged left and right by a thick braided gold cord, ending just above the hem in a point with a small red damask diamond, as input 5.
- CHEST PLATE (the clay's upper body plate with the V lower edge): same red damask. Along its V edge a band of thick braided gold cord, running from the shoulders down to the V's point at the centre of the chest. Inside the V a pale cream creased linen bib in the upper part, and below it a narrow olive-gold embroidered panel to the V's point, as input 5. A narrow black-olive strip runs from the V's point down to the belt, with a thin gold cord each side.
- BACK PLATE (the clay's plate on the upper back, ending in a rounded point): same red damask, with the same braided gold cord following its lower edge.
- SHOULDERS: the top corner of each shoulder has a small cream linen knot on the back side, and a band of gold cord over the top, as inputs 6 and 7.
- COLLAR (the flared standing collar and its rim): pale cream creased linen, a thin gold edge at its rim. The ring below the collar: braided gold cord.
- PENDANT: a small brass disc with one red faceted gem, on the chest under the collar's V.
- SLEEVES: the same red damask; near the end of each sleeve two parallel bands of braided gold cord round the sleeve, a dark edge at the very end, as input 6.
- BELT: narrow brown tooled leather. CLASP at the front: a large oval gold filigree clasp, as input 5.
- HANDS: bare, thin and bony, sallow pale tan skin with clear knuckles and tendons, each finger ending in a long sharp black claw: the last third of every finger is glossy black, as input 5.
- The forearm tube visible inside the sleeve opening: pale cream linen.
- HEAD: paint the skin a plain sallow tan. It is replaced later, do not spend effort on it.

Camera and light: exactly as inputs 1-4; flat even light, NO cast shadows, no rim light, no strong highlights: an albedo reference with sharp fine detail.
Do NOT: add a cape, a hood, feet, weapons or extra parts; move any edge; change the pose; add a background.
