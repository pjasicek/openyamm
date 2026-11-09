# Codex brief: repaint one head into two other people (male Honk tiers), exact alignment (mm9_honkmale_claude/v2/tier_heads)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_honkmale_claude/v2/tier_heads/`. No builds, no Meshy.

These images are projected straight back onto a 3D head, so the GEOMETRY MUST NOT MOVE: for every output the head, ears, eyes, nose,
mouth, jaw, neck, hairline and silhouette stay at exactly the same pixel positions, sizes and angles as in the attached render
of that view. Only the paint changes (skin, wrinkles, eyes' colour, brows, facial hair, hair colour). It is a repaint, not a
new portrait. Same canvas, same framing, same head turn, flat even unlit colours like the input (no added shading,
no highlights, no shadows), true transparent background, keep the robe at the bottom as it is. Mouth stays CLOSED exactly
where it is, a calm closed smile line, no teeth.

## Inputs (attached, in order)
1. `front.png`, 2. `q34.png`, 3. `side.png`: the head to repaint, three views (1254 x 1254).
4. `mm9_honkm3_views.png` + 5. `mm9_honkm3_face.png`: the ELDER: renders of the original low-poly model (front, three-quarter, profile)
   and its face skin enlarged, for identity and colours only.
6. `mm9_honkleader_views.png` + 7. `mm9_honkleader_face.png`: the SEER, same.

## Deliverables (unresized returns; keep raw returns in raw/; at most one corrective regeneration per image)
| File | Repaint of | Person |
|---|---|---|
| `elder_front.png`, `elder_q34.png`, `elder_side.png` | inputs 1, 2, 3 | ELDER |
| `seer_front.png`, `seer_q34.png`, `seer_side.png` | inputs 1, 2, 3 | SEER |
Make the front first, then the other two with that front as an extra input. Write `generation_runs.json` and a `selected_views_review.png`.

## ELDER (skin HONKM3)
The same bone structure aged to about seventy: weathered ruddy skin with pinkish-red cheeks and forehead, deep crow's feet, forehead
lines, nasolabial folds, sagging under-eye skin, thin lips; thick grey-white eyebrows; pale grey-blue eyes; clean-shaven apart
from a little white stubble on the jaw; the hair silver-grey and white with fine strands, the same shape as the input.

## SEER (skin HONKLEADER)
The same bone structure at about forty-five: tanned skin; blue eyes; a full, well-groomed red-brown beard and moustache covering the
jaw, chin and upper lip, painted on the same jaw shape (the beard is paint, the outline of the jaw does not change); red-brown
eyebrows; hair chestnut brown as in input 6, the same shape as the input.
