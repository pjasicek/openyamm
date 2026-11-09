# Codex brief: face repaint masters for the MM9 peasant girls on their CURRENT 3D head (mm9_peasantgirl_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantgirl_claude/references_head2/`. Do not edit any other
file, do not run builds, do not call Meshy. Use your built-in image generation tool.

Purpose: these images are projected onto an existing 3D head as its texture (a Meshy retexture of that exact mesh). So each output must be
a PAINT-OVER of the supplied render: the SAME camera, the SAME framing and size, the SAME head shape, silhouette, hairline, ears, eye,
nose, mouth and chin POSITIONS and proportions as the render, only with a clean, natural, high-detail surface painted on it. Do not
redesign, re-pose, re-frame or rescale anything. A feature that is 10 px off in the output lands on the wrong part of the 3D face.

There are three girls (three different children on the same head mesh): g2, g3, g1e. For each girl make three images.

## Inputs (attached, in order)
1. `cur_pg_g2_front.png`, 2. `cur_pg_g2_q34l.png`, 3. `cur_pg_g2_right.png`: renders of the current 3D head of girl g2 (front, three-quarter
   looking toward IMAGE LEFT, profile facing IMAGE RIGHT). GEOMETRY / FRAMING AUTHORITY for g2. Their face paint is blotchy and wrong
   (smeared nostrils, dark lip outline, dark marks under the eyes and on the chin): do NOT copy those marks.
4. `cur_pg_g3_front.png`, 5. `cur_pg_g3_q34l.png`, 6. `cur_pg_g3_right.png`: the same for girl g3.
7. `cur_pg_g1e_front.png`, 8. `cur_pg_g1e_q34l.png`, 9. `cur_pg_g1e_right.png`: the same for girl g1e (an elf: pointed ears).
10. `references_head/g2_01_front.png`, 11. `references_head/g3_01_front.png`, 12. `references_head/g1e_01_front.png`: earlier HD portraits of
    each girl: SKIN, HAIR AND FACE CHARACTER reference only (not geometry: their feature positions differ from the 3D head).
13. `references_hd/mm9_head_views_g2.png`, 14. `references_hd/mm9_head_views_g3.png`, 15. `references_hd/mm9_head_views_g1e.png`: the original
    Might and Magic IX girls (low-poly): identity and colour authority (hair colour, eye colour, freckles).

## Deliverables (unresized returns, square 1024x1024 or the closest supported square, the same framing as the matching input render, a TRUE
transparent background outside the figure, no text)
| File | Paint-over of |
|---|---|
| `g2_front.png`, `g2_q34.png`, `g2_profile.png` | inputs 1, 2, 3 |
| `g3_front.png`, `g3_q34.png`, `g3_profile.png` | inputs 4, 5, 6 |
| `g1e_front.png`, `g1e_q34.png`, `g1e_profile.png` | inputs 7, 8, 9 |

Make g2_front first, check it against input 1 (overlay mentally: eyes, nostrils, mouth corners, chin, hairline at the same pixels), then the
rest. At most ONE corrective regeneration per image. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256,
output path, selected flag, reason) and a `selected_review.png` contact sheet (each output next to its input render).

## What to paint (all images)
- A calm, warm, natural nine-year-old girl's face, relaxed, gentle closed-mouth smile. No makeup, no lipstick: lips a soft natural pink,
  the same tone family as the skin, with a soft edge (no dark outline, no dark mouth corners); the mouth is ONE closed line, no teeth, no
  gap, no pale specks between the lips.
- Nose: a small child's nose painted exactly on the render's nose; seen from the front, the nostrils are two SMALL, SOFT shadows exactly
  where the render's nostril openings are, no brown smear, no outline round the nose wings, nothing painted outside the nose's real outline.
- Eyes: clear irises (g2 blue, g3 grey-blue, g1e green), natural white, soft lashes, NO dark wedges or shadows under the lower lids, no
  pale crescent, no second brow line; one soft natural brow each.
- Skin: fair, even, light freckles on g2 and g1e, a few on g3, soft natural cheek warmth (no hard red patches), no dark spots or lines on
  the chin, under the chin or down the middle of the face; even light, no baked shadows (the 3D lighting adds them).
- Hair exactly as the render's hair shape: g2 auburn with braids, g3 brown with the short fringe, g1e light golden-brown; g1e's pointed ears
  skin-coloured.
- Dress neckline as in the render (g2 black with gold, g3 navy, g1e teal).

## Do NOT
change the camera, framing, head size or position; move or resize any feature; add makeup, jewellery, ribbons or text; paint shadows or dark
outlines; open the mouth; add a background, floor or shadow.
