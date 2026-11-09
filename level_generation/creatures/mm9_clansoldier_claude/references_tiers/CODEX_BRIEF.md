# Codex brief: tier repaints of the MM9 Horde Soldier (mm9_clansoldier_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_clansoldier_claude/references_tiers/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game character, an adult male medieval foot soldier in leather and mail, restored from a 2002 game for a game mod.

You are repainting the SAME figure in other armour. The four attached HD views of the Horde Grunt stay exact in pose, body shape, proportions, silhouette, camera and framing: every limb, the mantle's outline, the skirt's hem, the sash, the sleeves, boots and fur cuffs. Only the surface paint changes.

## Inputs (attached, in order)
1-4. `references_hd/01_front_clean.png`, `03_left_clean.png`, `02_back_clean.png`, `04_right_clean.png`: the HD figure. Geometry authority.
5. `references_hd/mm9_views_b.png` or `_c.png` (see the tier): renders of the ORIGINAL low-poly model in this tier, five views: three-quarter, front, figure's left, back, figure's right. Costume and colour authority. Grey is background, ignore the faceting.
6. `references_hd/mm9_waist_views_b.png` or `_c.png`: close renders of the coat and skirt.
7. `references_hd/mm9_head_views_b.png` or `_c.png`: close renders of the head and chest.
8. `references_hd/mm9_skin_x4_b.png` or `_c.png`: the original skin enlarged, material and colour only.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1536x1024, four views each)
Tier B: `b_01_front.png`, `b_03_left.png`, `b_02_back.png`, `b_04_right.png`. Tier C: `c_01_front.png`, `c_03_left.png`, `c_02_back.png`, `c_04_right.png`.
At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_<tier>.json` (id, prompt, inputs with sha256, output path, reason) and `selected_views_review_<tier>.png`.
All surfaces follow inputs 5-8 exactly. Unchanged parts stay as in the HD figure: dark brown trousers, leather gloves, the chain-mail mantle's rings.

## Tier B (Horde Warrior)
- Torso, front and back: a steel cuirass of narrow vertical lamellar strips with dark seams, on the chest a large round silver disc of Celtic knotwork, as inputs 5, 7, 8. An opening at the top of the chest shows olive-gold wool under the mantle.
- Mantle: as before; its V edge is rust-brown leather instead of olive-gold, with a small knot of cord below it.
- Shoulders: brown fur caps stay. Sleeves: olive-gold wool with a fine mottled weave from shoulder to wrist, the steel-and-gold laminated strips on the outside of the upper arm stay; a narrow teal-and-brown wrapped band at the wrist as input 5.
- Sash: rust-brown leather wrapped round the waist, the knot in the middle.
- Skirt: the scale panels become smooth polished steel plates in horizontal rows edged with thin gold lines, on olive-gold wool; a narrow rust-brown edge; the lower part is plain olive-gold wool to the hem; a small panel of chain mail in the centre slit, as input 6.
- Boots and fur cuffs unchanged.

## Tier C (Horde Leader)
- Torso, front and back: a polished dark steel breastplate with a raised centre seam and a dark blue padded strap down the middle of the chest, riveted edge, as inputs 5, 7, 8.
- Mantle: as before; its V edge is dark blue cord. Under the mantle in front, red and white lamellar scales with dark blue lacing.
- Shoulders: brown fur caps stay. Sleeves: olive-gold wool; the laminated strips on the outside of the upper arm become red and white lamellar scales with dark blue lacing; dark blue wrapped bands at the wrist.
- Sash: dark blue cloth wrapped round the waist, the knot in the middle.
- Skirt: the panels become red and white lamellar scales framed in dark blue lacing, the lower part olive-gold wool with a dark blue edge, a small panel of chain mail in the centre slit, as input 6.
- Legs: on the FRONT of each knee a rounded polished steel knee plate; on the front of each shin a dark blue and dark steel greave with thin gold edges over the fur cuff, as input 5. At the back of the leg the boot and fur cuff are unchanged.

Do NOT: add weapons, a shield, change the pose, proportions, silhouette or framing, add a cloak, or draw a floor or a shadow. The helmet and face are only a guide (the head is replaced later): keep them as in the HD figure.
