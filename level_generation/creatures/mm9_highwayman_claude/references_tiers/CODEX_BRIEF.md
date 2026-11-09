# Codex brief: tier repaints of the MM9 Highwayman (mm9_highwayman_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_highwayman_claude/references_tiers/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game character, an adult male travelling rogue in leather and cloth clothes, restored from a 2002 game for a game mod.

You are repainting the SAME figure in other clothes. The four attached HD views of the Cutpurse stay exact in pose, body shape, proportions, silhouette, camera and framing: every limb, the yoke's outline, the tunic skirt's hem, the belt, the sleeves, boots and flared boot tops. Only the surface paint changes.

## Inputs (attached, in order)
1-4. `references_hd/01_front_clean.png`, `03_left_clean.png`, `02_back_clean.png`, `04_right_clean.png`: the HD figure. Geometry authority.
5. `references_hd/mm9_views_b.png` or `_c.png` (see the tier): renders of the ORIGINAL low-poly model in this tier, five views: three-quarter, front, figure's left, back, figure's right. Costume and colour authority. Grey is background, ignore the faceting.
6. `references_hd/mm9_waist_views_b.png` or `_c.png`: close renders of the tunic.
7. `references_hd/mm9_head_views_b.png` or `_c.png`: close renders of the head and chest.
8. `references_hd/mm9_skin_x4_b.png` or `_c.png`: the original skin enlarged, material and colour only.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1536x1024, four views each)
Tier B: `b_01_front.png`, `b_03_left.png`, `b_02_back.png`, `b_04_right.png`. Tier C: `c_01_front.png`, `c_03_left.png`, `c_02_back.png`, `c_04_right.png`.
At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_<tier>.json` (id, prompt, inputs with sha256, output path, reason) and `selected_views_review_<tier>.png`.

## Tier B (Burglar)
- The yoke stays olive-green wool, but its wide tan pebbled-leather edging is replaced by a NARROW bright gold-yellow piping along the same outline, exactly as input 7. Collar at the throat keeps its tan pebbled edge as input 7.
- Tunic, belt, sleeve caps, green sleeves, trousers and boots unchanged.
- Forearms: the gold embroidered cuffs are gone. Instead each forearm wears a dark almost black leather bracer with three or four thin straps and small silver ring buckles, as input 5 and the dark panel at the top of input 8. The thin gold band at its upper edge stays.
- Head: as input 7: longer blond hair, no headband (only a guide: the head is replaced later).

## Tier C (Bandit)
- Over the yoke, on the chest and on the upper back, a heavy armour of overlapping DARK BROWN leather strips riveted with small silver studs, like hanging fingers fanned over the shoulders down to the chest, as input 7 and input 8. The olive yoke shows only in the gaps; the brooch stays in the middle of the chest.
- The quilted tunic becomes dark red-brown leather with evenly spaced rows of oval silver studs, no diamond quilting, front and back and on the skirt, as inputs 5, 6, 8. The lacing below the chest stays. Belt as before.
- Trousers: warm TAN brown suede, much lighter than the Cutpurse's, with a thin dark seam with small silver studs down the outside of each leg, as input 5 and input 8.
- Green sleeves, gold cuffs and boots unchanged.
- Head: as input 7: red hair, a black eye patch (only a guide: the head is replaced later).

Do NOT: add weapons, change the pose, proportions, silhouette or framing, add a cloak or hood, or draw a floor or a shadow.
