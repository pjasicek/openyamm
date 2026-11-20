# Codex brief: second master pass for the MM9 Skeleton, painted on the actual model (mm9_skeleton_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_skeleton_claude/references_hd/v2/`. No builds, no Meshy, nothing else edited.
Use your built-in image generation tool. Keep raw returns in `v2/raw/`. Write `v2/generation_runs.json` (format of `references_hd/generation_runs.json`) and a `v2/selected_views_review.png` contact sheet.

Why: the first masters gave the bones a mottled, scaly, reptile-skin surface and an orange woven vest, and a 3D paint made from them looks wrong. The bone in the head views below is right.

## Inputs (attached, in order)
1. `v2/clay_01_front.png`, 2. `v2/clay_02_back.png`, 3. `v2/clay_03_left.png`, 4. `v2/clay_04_right.png`: grey clay renders of the FINISHED 3D model, on a transparent background. They are the absolute authority for shape, silhouette, pose,
   framing and which part is where: every bone, rib, strap, rope and vest panel must stay exactly where it is in the clay, at the same size and the same place in the frame. You are PAINTING this exact figure, like colouring a photograph of the clay model.
5. `references_head/bust_front.png`: the BONE material authority: warm aged ochre-ivory bone, smooth, with fine hairline cracks and soft brownish staining.
6. `references_hd/mm9_torso_views_skel2.png`: original MM9 model renders of the torso: colour authority for the leather (dull dark brown, not orange).
7. `references_hd/mm9_skin_x4.png`: the original skin enlarged: the design authority for the materials and details.

## Deliverables (true transparent background, unresized returns, 1024x1536 portrait, same framing as the clay)
`v2/01_front.png` (from clay 1), `v2/02_back.png` (clay 2), `v2/03_left.png` (clay 3), `v2/04_right.png` (clay 4). The skull in these views is not used, keep it plain aged bone.

## What to paint
Fantasy-game texture reference, semi-realistic, sharp fine detail, even soft neutral studio light, no cast shadows, no dramatic lighting, no glow.
- BONE (all bones, ribs, spine, pelvis, femurs, shins, arms, hands, feet): smooth aged ochre-ivory bone as input 5, gently darker brown in hollows and at the joints, with sparse fine hairline cracks. NO scales, NO reptile pattern, NO mottling, NO spots, NO dots, NO pores, NO stipple.
- VEST (the broad flat panels on both flanks of the ribcage and the panel across the upper back): dull dark brown worn LEATHER (about RGB 70,40,25 in the middle, 100,60,35 on worn edges), plain and matte, gently scuffed, with a few stitches near the edges and ragged torn lower ends; colour as input 6. NOT orange, NOT red, NOT woven, NOT striped, no vertical lines.
- STRAP (the narrow diagonal band from the figure's right shoulder across the chest to its left lower ribs, and on over the back): plain very dark brown leather with a neat row of small dull iron studs and one square iron buckle at the middle of the chest. No white spots.
- ROPE (the ring round the neck and the belt round the hips): twisted hemp rope in dull tan-brown, as in input 7. Not orange.
- HIP SCRAPS (the small narrow strips hanging at the hips): dull dark brown torn leather.
- THIGHS: on the outer side of each femur a torn patch of the same dull brown leather is wrapped tight, from just under the hip to above the knee, as input 7's leg tile. The bone shows on the inside of the thigh.
- ELBOWS: a crossed pale linen bandage round each elbow knob. WRIST: the two rings just above each hand are dark brown leather cuffs. ANKLE: the rings above each foot are dark brown leather bands.

## Do NOT
Change the silhouette, move, add or remove any part, change the pose, add a weapon, add flesh, add a background, floor, shadow or text, crop anything.

## Checks per image
Same outline as the clay (overlay it); smooth bone with no pattern; dull dark brown leather; dark strap with small iron studs; tan rope; true alpha; 1024x1536. At most one corrective regeneration per view.
