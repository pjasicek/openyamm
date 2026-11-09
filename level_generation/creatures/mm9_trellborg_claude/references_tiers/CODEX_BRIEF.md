# Codex brief: tier repaints of the MM9 Trellborg (mm9_trellborg_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_trellborg_claude/references_tiers/`. No builds, no Meshy. Use your built-in image generation tool.
A fantasy video-game monster, a big orc-like tribesman, restored from a 2002 game for a game mod.

You are repainting the SAME figure in other clothes. The four attached HD views of the Trellborg stay exact in pose, body shape, proportions, silhouette, camera and framing: every limb, the shorts' outline, the feet. Only the surface paint changes. Nothing is added to the silhouette.

## Inputs (attached, in order)
1. `references_hd/01_front_clean.png`, 2. `03_left_clean.png`, 3. `02_back_clean.png`: the HD figure. Geometry authority. (The right side view is the mirror of the left.)
4. `references_hd/mm9_views_b.png` or `_c.png`: renders of the ORIGINAL low-poly model in this tier, five views: three-quarter, front, figure's left, back, figure's right. Costume and colour authority. Grey is background, ignore the faceting.
5. `references_hd/mm9_torso_views_b.png` or `_c.png`: close renders of the torso and arms. A second call may swap this for `mm9_legs_views_b.png` or `_c.png` (close renders of hips and legs) if five inputs is the limit.

## Deliverables (true transparent background, no glow, no floor, no shadow, no text, unresized returns, same aspect as the figure, four views each)
Tier B: `b_01_front.png`, `b_03_left.png`, `b_02_back.png`, `b_04_right.png`. Tier C: `c_01_front.png`, `c_03_left.png`, `c_02_back.png`, `c_04_right.png`.
At most one corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs_<tier>.json` (id, prompt, inputs with sha256, output path, reason) and `selected_views_review_<tier>.png`.
All surfaces follow inputs 4-5 exactly. Head and hair stay as in the HD figure (the head is replaced later). Hands bare.

## Tier B (Kin Trellborg)
- SKIN: same red-brown leathery skin on the arms, knees and feet.
- No harness at all, no skull medallion on the chest, no arm bands.
- TORSO, front and back: a sleeveless vest of shaggy tawny golden fur, tight on the body like a pelt, the muscles still reading under it, irregular torn fur edge at the armholes and at the neck, pale fur on the shoulder tops, ending at the belt. On the back a deep V cut-out showing the skin between the shoulder blades down to the middle of the back, as input 4 view 4. In front a low neck opening.
- NECKLACE: a thin cord round the neck with a row of long white curved claws and teeth on the upper chest. Below it on the breastbone a small ornamental bronze knotwork brooch.
- WAIST: narrow dark leather belt with a gold-toned steel skull buckle, small studs. Below it the pale pelt apron with a brown leather lower half in front, and in the back a tawny fur pelt seat with a pale edge. Dark brown fur short breeches as before.
- WRISTS: no steel. Pale fur cuffs bound with crossed brown leather straps, as input 5.
- SHINS: no steel. Pale fur leg wraps bound with crossed dark brown leather straps from the ankle to below the knee, as input 4.
- FEET: bare, with yellow claws.

## Tier C (Ancient Trellborg)
- SKIN: a lighter golden-tan ochre on the arms and thighs, as input 4.
- No harness.
- TORSO, front and back: a fitted steel chain-mail shirt, small even rings, dark grey with soft highlights, short sleeves to the upper arm with a ragged mail hem; a V neck opening in front showing skin, a mail hood fold lying on the back of the neck, as input 4 view 4.
- SHOULDERS: on each shoulder a layered pauldron of brown and white lamellar scales laced with dark blue cord, a pale leather strap from the shoulder to the chest, a round steel boss at the top of the chest each side.
- NECKLACE: long white curved claws and teeth on a cord across the upper chest. On the middle of the chest a round steel skull medallion, as in the HD figure.
- WAIST: a wide dark leather belt with thin gold lines and a steel skull buckle. Below it in front a panel of brown and white lamellar scales laced with dark blue; at the back a row of white and brown scales with dark blue lacing in columns. Below these, short breeches of dark grey mail with a ragged hem.
- WRISTS: dark leather bracers with dark blue edge cords and a riveted engraved steel plate.
- LEGS: bare ochre thighs and knees; from below the knee polished steel boots: a riveted steel greave in front, brown leather straps behind, and on the foot a smooth articulated steel sabaton following the foot's shape (the toes become the rounded lames of the shoe, no claws, no skin on the foot), as input 4.

Do NOT: add weapons, change the pose, proportions, silhouette or framing, add a cloak, or draw a floor or a shadow. Keep the even, shadowless light of the HD figure.
