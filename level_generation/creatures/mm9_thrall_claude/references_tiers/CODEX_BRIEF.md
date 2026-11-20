# Codex brief: tier repaints of the MM9 Thrall (mm9_thrall_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_thrall_claude/references_tiers/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game character, an adult male enslaved tribesman, restored from a 2002 game for a game mod.

You are repainting the SAME figure in other clothes. The four attached HD views of the Thrall Master stay exact in pose, body shape, proportions, silhouette, camera and framing: every limb, every jag of the skirt hem, the rope belt and bow, the rope collar with its ring, wrist wraps, leg wraps and sandals stay in exactly the same place, pixel for pixel as far as you can. Only surface paint changes, as listed.

## Inputs (attached, in order)
1-4. `references_hd/01_front_clean.png`, `03_left_clean.png`, `02_back_clean.png`, `04_right_clean.png`: the HD figure. Geometry authority.
5. `references_hd/mm9_views_a.png` or `_b.png` (see the tier): renders of the ORIGINAL low-poly model in this tier, five views: three-quarter, front, figure's left, back, figure's right. Costume and colour authority. Grey is background, ignore the faceting and white streaks.
6. `references_hd/mm9_waist_views_a.png` or `_b.png`: close renders of its waist.
7. `references_hd/mm9_head_views_a.png` or `_b.png`: close renders of the head and chest.
8. `references_hd/mm9_skin_x4_a.png` or `_b.png`: the original skin enlarged, material and colour only.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1024x1536, four views each)
Tier A: `a_01_front.png`, `a_03_left.png`, `a_02_back.png`, `a_04_right.png`. Tier B: `b_01_front.png`, `b_03_left.png`, `b_02_back.png`, `b_04_right.png`.
At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, reason) and `selected_views_review.png`.

## Tier A (Field Thrall)
- Clothing: a sleeveless tunic of dark brown coarse leather or worn hide, painted tight on the torso exactly as input 5 and 7: from the neck to the belt, front and back, wide shoulders of the tunic ending on top of the shoulder, arms bare from there. Worn pale patches and long vertical scuffs, a torn pale V at the throat, on the back three pale torn patches of the underlayer as in input 7. No muscles or six-pack visible through it: a plain worn garment with soft folds.
- Skirt: same shape and jags, darker brown mottled leather than the Master's, nearly the same brown as the tunic, torn lighter strips at the front as input 6. Same dark hide shorts under it.
- Skin of arms and legs: weathered older man, a little paler and more orange-brown than the Master's. Same wraps and sandals.
- Head: as input 7, an old man, bald crown, long white hair at the sides and back, short white beard, deep wrinkles (this view is only a guide: the head is replaced later).

## Tier B (Thrall)
- Clothing: a pelt of dark rust-brown short fur or hide over his RIGHT shoulder and the RIGHT half of his chest and stomach (IMAGE LEFT in a front view), down to the belt, with a torn, wavering edge running down the middle of the chest, exactly as input 7 and input 5. His LEFT chest and left stomach are bare skin with pectoral muscle (IMAGE RIGHT in a front view). On the back: a band of the same pelt across the top of the shoulders, bare skin below it with faint scars, and a dark square of pelt above the belt at the small of the back, as input 5.
- Skirt: same shape and jags, dark rust-brown hide, fur-like mottling, almost black in the hollows, as input 6. Same dark hide shorts under it.
- Skin: warm red-brown, as input 5. Same wraps (darker), same sandals.
- Head: as input 7, sandy-blond hair with a dark leather headband (only a guide: the head is replaced later).

Camera and light unchanged: near-orthographic, even soft studio light, no drama, no cast shadows on the figure. Do NOT add armour, weapons, sleeves or trousers; do NOT move anything.
