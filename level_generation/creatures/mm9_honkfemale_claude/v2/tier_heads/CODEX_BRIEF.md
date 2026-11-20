# Codex brief: repaint one head into another person (female Honk, Elder tier), exact alignment (mm9_honkfemale_claude/v2/tier_heads)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_honkfemale_claude/v2/tier_heads/`. No builds, no Meshy.

These images are projected straight back onto a 3D head, so the GEOMETRY MUST NOT MOVE: for every output the head, hat, eyes, nose,
mouth, jaw, neck, braids, the long back shape, and the silhouette stay at exactly the same pixel positions, sizes and angles as in
the attached render of that view. Only the paint changes. It is a repaint, not a new portrait. Same canvas, same framing, same head
turn, flat even unlit colours like the input (no added shading, highlights or shadows), true transparent background. The goose hat
stays exactly as it is, unchanged, and the robe at the bottom too. Mouth closed.

## Inputs (attached, in order)
1. `front.png`, 2. `q34.png`, 3. `side.png`: the head to repaint, three views (1254 x 1254).
4. `mm9_honkf3_views.png`: the target: renders of the original low-poly model (front, three-quarter, profile).
5. `mm9_honkf3_face.png`: its face skin enlarged, for identity and colours.

## Deliverables (unresized returns; keep raw returns in raw/; at most one corrective regeneration per image)
`elder_front.png`, `elder_q34.png`, `elder_side.png`: repaints of inputs 1, 2, 3. Make the front first, then the other two with that
front as an extra input. Write `generation_runs.json` and a `selected_views_review.png`.

## The person (skin HONKF3)
The same face bones at about forty-five: warm tanned skin, a confident closed-mouth smile with defined rosy lips, dark brown eyes with
dark brows, a few fine lines. The long pale veil of the input is repainted as long straight dark brown hair with fine strands (same
shape, it hangs from under the hat down the back); dark brown hair frames the forehead. The two thin braids become dark brown.
The neck and the upper chest above the robe's neckline are covered by a high blue-grey linen undergarment up to the throat, as in
input 4, painted on the same surface; the face above the jaw stays skin.
