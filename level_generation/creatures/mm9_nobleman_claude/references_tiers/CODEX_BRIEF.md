# Codex brief: tier repaints of the MM9 Nobleman (mm9_nobleman_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_nobleman_claude/references_tiers/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game character, an adult male nobleman in a rich medieval court costume, restored from a 2002 game for a game mod.

You are repainting the SAME figure in other clothes. The four attached HD views of the Baron stay exact in pose, body shape, proportions, silhouette, camera and framing: every limb, the mantle's outline, the doublet skirt's hem, the belt, the sleeves, the collar, the shoes. Only the surface paint changes.

## Inputs (attached, in order)
1-4. `references_hd/01_front_clean.png`, `03_left_clean.png`, `02_back_clean.png`, `04_right_clean.png`: the HD figure. Geometry authority.
5. `references_hd/mm9_views_b.png` or `_c.png` (see the tier): renders of the ORIGINAL low-poly model in this tier, five views: three-quarter, front, figure's left, back, figure's right. Costume and colour authority. Grey is background, ignore the faceting.
6. `references_hd/mm9_waist_views_b.png` or `_c.png`: close renders of the doublet and sleeves.
7. `references_hd/mm9_head_views_b.png` or `_c.png`: close renders of the head and chest.
8. `references_hd/mm9_skin_x4_b.png` or `_c.png`: the original skin enlarged, material and colour only.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1024x1536 PORTRAIT, four views each)
Tier B: `b_01_front.png`, `b_03_left.png`, `b_02_back.png`, `b_04_right.png`. Tier C: `c_01_front.png`, `c_03_left.png`, `c_02_back.png`, `c_04_right.png`.
At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_<tier>.json` (id, prompt, inputs with sha256, output path, reason) and `selected_views_review_<tier>.png`.

## Tier B (Viscount)
- The fur mantle and the whole body of the doublet become one long open FUR COAT of dark blue-black fur, thick and shaggy, from the shoulders to the hem, with a mottled slate-blue sheen, open at the front in a long narrow V. Back: all blue-black fur, as inputs 5 and 7.
- Inside the opening at the front: the cream linen chest panel at the top with the gold chain and a round BLUE gem pendant, under it a teal-blue undergarment, and a burgundy brocade panel with the wide gold embroidered centre band, gold belt buckle and brown belt, as input 6.
- Two round gold filigree brooches on the chest, two smaller ones at the waist.
- Sleeves: plain smooth pale TEAL BLUE-GREEN cloth from the shoulder to the wrist, soft sheen, with narrow gold-and-brown braid bands at the upper arm, the elbow and the wrist, as input 6. The cream ruffled cuff stays.
- Breeches: very dark navy-black cloth. Shin bands: slate-blue fur with gold lines, as input 5.
- Shoes unchanged.
- Head: as input 7: white-haired older man (only a guide: the head is replaced later).

## Tier C (Count)
- Fur mantle: warm tan-brown fur, with a ragged lower edge coming to a long point down the centre of the back and over the shoulder fronts, as inputs 5 and 7. On it three large round pale gold studded bosses: one on each shoulder and one on each side of the chest (four in all, as input 7), and a large one on the chest in the middle.
- Doublet: gold-yellow brocade with a small raised dark scale pattern, front panels edged with tan fur down to the hem, wide fur hem, as input 6.
- In the middle of the chest from the collar to the hem a long panel of orange-red quilted cloth, with one large round gold boss at the waist.
- Belt: narrow brown leather with a small embroidered plate, as input 6.
- Sleeves: panelled gold-yellow brocade, long vertical plain gold panels framed by scale-patterned bands, tan fur bands at the upper arm and elbow, and at the wrist, as input 6.
- Breeches: very dark brown cloth. Shin bands: pale tan and white fur with gold, as input 5.
- Shoes unchanged.
- Head: as input 7: brown-haired man with a cap (only a guide: the head is replaced later).

Do NOT: add weapons, change the pose, proportions, silhouette or framing, add a hood, or draw a floor or a shadow.
