# Codex brief: HD head turnaround for the MM9 cat (mm9_cat_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_cat_claude/references_head/`. No builds, no
Meshy, no other files. Use your built-in image generation tool. Record `generation_runs.json` (id, prompt, inputs
with sha256, output, selected, reason) and a `selected_views_review.png` contact sheet.

## Inputs (attached, in order)
1. `references_hd/00_three_quarter.png`: the accepted HD cat: identity, colours, fur.
2. `references_hd/mm9_head_views.png`: renders of the original low-poly MM9 cat head (front, left profile, 3/4): the
   FACE MARKINGS authority (white muzzle and blaze, orange forehead patch), not the shape.
3. `references_hd/mm9_skin_x8.png`: the original skin enlarged, colour and fur material only.

## Deliverables (true transparent background, unresized 1254x1254 returns, bust only)
`00_three_quarter.png` (front 3/4 from the cat's RIGHT, nose to image right), `01_front.png`, `02_back.png`,
`03_left.png` (pure profile, nose to IMAGE LEFT), `04_right.png` (pure profile, nose to IMAGE RIGHT).
Generate 00 first and use it as an input for the others, so all five show the same head. At most one corrective
regeneration per view.

## Prompt content
Faithful high-definition reconstruction of an existing game cat's head as a 3D modelling and texturing reference: a
real domestic cat with semi-realistic sharp fine fur, as a high-quality sculpt.
- Anatomy: a true adult domestic cat skull: rounded cranium, short wedge face, small neat muzzle with distinct whisker
  pads and a small chin, two upright triangular ears with visible inner ear cups, set wide on the skull.
- Eyes: large, wide open, almond-shaped, clearly recessed in sockets with defined lids and tear lines; yellow-green
  iris with a vertical dark slit pupil, a small catchlight. Both eyes level and symmetric.
- Nose and mouth: small PINK nose leather with nostrils; a closed mouth with the fine dark "Y" line from nose to lips.
- Whiskers: NONE or only fine painted dots on the whisker pads (no long whisker hairs; no hairs sticking out of the
  silhouette; ear hairs short).
- Markings: very dark brown-black tortoiseshell with rusty orange flecks on the head and ears; a white blaze from the
  forehead down the nose; white muzzle, chin and throat; a small orange patch on the forehead above the blaze.
- Pose: the head perfectly STRAIGHT and level, facing along the neck axis, not turned or tilted, strictly left/right
  symmetric in shape. Include the upper NECK as a straight stub of the neck's full width, cut off flat about one
  head-length behind the skull, leaving neck fur only (no shoulders).
- Light: even soft neutral studio light, no strong shadows. Near-orthographic camera. Generous margins, nothing
  cropped, no floor, no text.
Do NOT add a collar, open the mouth, show teeth, add whisker hairs, change the colours or turn the head.

## Per-image checks
Same head in all views; two ears; both eyes open with slit pupils where visible; pink nose; closed mouth; no long
whiskers; correct side faces the correct image side; true alpha; 1254x1254.
