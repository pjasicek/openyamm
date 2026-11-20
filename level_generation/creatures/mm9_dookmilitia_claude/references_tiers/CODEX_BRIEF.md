# Codex brief: tier repaints of the MM9 Half Orc (mm9_dookmilitia_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_dookmilitia_claude/references_tiers/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game character, an adult male half-orc militiaman in armour, restored from a 2002 game for a game mod.

You are repainting the SAME figure in other clothes. The four attached HD views stay exact in pose, body shape, proportions, silhouette, camera and framing: every limb, the mantle's outline, the tunic skirt's hem, the belt, the sleeves, boots. Only the surface paint changes.

## Inputs (attached, in order)
1-4. `references_hd/01_front_clean.png`, `03_left_clean.png`, `02_back_clean.png`, `04_right_clean.png`: the HD figure. Geometry authority.
5. `references_hd/mm9_views_b.png` or `_c.png` (see the tier): renders of the ORIGINAL low-poly model in this tier, five views: three-quarter, front, figure's left, back, figure's right. Costume and colour authority: dark, muted, low saturation. Grey is background, ignore the faceting.
6. `references_hd/mm9_waist_views_b.png` or `_c.png`: close renders of the tunic.
7. `references_hd/mm9_head_views_b.png` or `_c.png`: close renders of the head and chest.
8. `references_hd/mm9_skin_x4_b.png` or `_c.png`: the original skin enlarged, material and colour only.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1536x1024, four views each)
Tier B: `b_01_front.png`, `b_03_left.png`, `b_02_back.png`, `b_04_right.png`. Tier C: `c_01_front.png`, `c_03_left.png`, `c_02_back.png`, `c_04_right.png`.
At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_<tier>.json` (id, prompt, inputs with sha256, output path, reason) and `selected_views_review_<tier>.png`.

## Tier B (Half Orc Soldier)
- Tunic body below the chest panel and the skirt: dark steel-grey riveted CHAIN MAIL, small rings clearly drawn, the skirt's hem a frayed row of mail, no quilting, no lacing.
- Sleeve caps and upper sleeves: the same dark chain mail, the caps' lower edge jagged rings, as input 5.
- Unchanged but darker and less saturated, as inputs 5 and 7: the dark brown leather mantle of riveted strips with silver studs, the soft dark-brown chest panel, the belt with thin gold lines and studs, the dark leather bracers with their gold band, the reddish-brown trousers with the tan-olive knee patches, the dark boots.
- Head: as input 7 (only a guide: the head is replaced later).

## Tier C (Half Orc Captain)
- Tunic body, chest and skirt: dark steel-grey CHAIN MAIL, all the way up to the throat, no leather chest panel, no quilting, no lacing. Sleeve caps and upper sleeves the same chain mail.
- The mantle's outline becomes polished dark STEEL plates: two broad riveted steel pauldron plates over the shoulders running down to the chest and upper back, with raised edges and silver rivets, as inputs 5 and 7 and the plates in input 8. No leather strips.
- Across the chest between the plates, three round bronze filigree medallions joined by a short chain, as input 7, the largest in the centre.
- Trousers: black-brown leather with a thin dark seam, no knee patch.
- Belt, dark leather bracers with their gold band, dark brown boots with studs as input 5.
- Head: as input 7 (only a guide: the head is replaced later).

Do NOT: add weapons, change the pose, proportions, silhouette or framing, add a cloak or hood, brighten or saturate the colours beyond input 5, or draw a floor or a shadow.
