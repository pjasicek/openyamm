# Built-in imagegen submissions

The images listed here are in the exact order supplied to the built-in imagegen tool. All three
returns were copied without changes from the tool's generated-image directory. Output hashes
and input hashes are recorded in `HASHES.sha256`.

## v1 — rejected bracer mismatch

Inputs:

1. `../in_situ_left_open/full_candidate_pose_x2.png` — edit target, previously restored assembly.
2. `../assigned_portrait_original_x4.png` — facial identity.
3. `../assembled_native_poses_x2.png` — original pose reference.
4. `../../../../../chat_bundles/remaining_icons_dense_v2_20260922/runs/restore-part-2/v4/processed/cleaned/S006/engine--icons--pc01bod.bmp.png` — detailed body style reference.

Output: `raw_full_doll_v1.png`.

```text
Use case: identity-preserve. Asset type: coherent full-body source art for a layered 2D fantasy RPG paperdoll, character PC01. Image 1 is the edit target: a current detailed assembled PC01 sprite with flawed, incomplete hands. Image 2 is the assigned original avatar portrait and defines the man's face, hair, brow, eyes, nose, beard, and expression. Image 3 contains four poses of the original low-resolution paperdoll; use only its LEFTMOST empty-hands figure to preserve the pose, silhouette, limb direction, elbow and wrist locations, and relative item-anchor geometry. Image 4 is the detailed body sprite and defines the painted material, lighting, dark-green trousers, brown leather leg armor, and crimson-brown decorated bracer style. Regenerate ONE complete, coherent standing male doll in the Image 1 pose, empty hands, viewed straight on as 2D game sprite art. Keep the torso, legs, head and feet very close to the detailed original; repair BOTH arms and hands as anatomically coherent extensions of that same body. The figure's screen-left arm angles outward and down with its relaxed palm open; the screen-right arm hangs down with relaxed open fingers. Repaint the two forearm bracers as the same red leather material, ornament and lighting as the upper bracers on the body. Each complete finger must have a rounded tip and a visible natural gap where appropriate; leave transparent breathing room below BOTH hands so no fingertip touches the image edge. Preserve body proportions and the original positions of shoulders, elbows, wrists, palm centers, and future item grip points. No weapon, shield, extra arms, disconnected parts, labels, red circles, scenery, shadow or background. Return exactly one full-body figure on genuine transparent alpha with crisp clean cutout edges and no magenta spill. This full figure will be split into separately registered paperdoll sprites later; visual cohesion and complete hands matter more than copying the existing flawed limb pixels.
```

## v2 — direct edit of original assembly

Inputs:

1. `original_assembled_empty_x4.png` — edit target, original body and limbs assembled at table offsets.
2. `../assigned_portrait_original_x4.png` — facial identity.
3. `../body_and_limbs_original_x2.png` — original part materials and seam reference.

Output: `raw_original_assembly_v2.png`.

```text
Use case: identity-preserve. Asset type: 2D fantasy RPG paperdoll restoration. Image 1 is the EDIT TARGET: the ORIGINAL PC01 doll already assembled from its original body, screen-left open arm, and screen-right hanging open arm at the exact game-table positions. Restore that single assembled original figure directly. Image 2 is the assigned ORIGINAL avatar portrait, used only to keep the man's facial identity, hair, eyes, brow, beard, and expression. Image 3 shows those same original body and arm source sprites separately, so their materials and attachment seams are unambiguous; it is a reference, not the output layout. Produce ONE full-body, empty-hand paperdoll on genuine transparent alpha, in precisely Image 1's pose and proportions. Keep head, shoulders, elbows, wrists, palms, feet and the future item grip area aligned with Image 1. Render the body and both attached arms as one coherent painted figure: same anatomy, skin tone, lighting, dark green trousers, brown leather leg armor, and source bracer designs. At EACH elbow/forearm attachment, continue the exact corresponding upper-arm leather, trim and ornament seamlessly into its own forearm; no abrupt red-versus-brown swap, color block, or disconnected cuff. The screen-left open palm angles outward/down; the screen-right open palm hangs beside the hip. Both hands must have complete natural fingers and rounded visible fingertips, with transparent breathing room below them; no cropped/flat fingertips. Preserve the original silhouette and scale as closely as possible. No weapon, shield, extra limbs, detached sprites, labels, boxes, red markup, background, shadows, magenta fringe or checkerboard. Return only the restored assembled figure, not a sprite sheet.
```

## v3 — detail refinement of v2

Inputs:

1. `raw_original_assembly_v2.png` — edit target.
2. `original_assembled_empty_x4.png` — original pose and geometry.
3. `../assigned_portrait_original_x4.png` — facial identity.

Output: `raw_original_assembly_refined_v3.png`.

```text
Use case: identity-preserve. Asset type: final-detail pass for a single assembled 2D fantasy RPG paperdoll. Image 1 is the edit target and is an initial restoration of the original PC01 doll with BOTH arms already attached. Image 2 is the exact original assembled pose and geometry contract. Image 3 is the assigned original avatar portrait for facial identity. Refine ONLY the painted detail, anatomy, and cutout finish of Image 1 while keeping Image 2's proportions and all joints, hands, feet, and item-grip locations. Preserve the complete relaxed fingers and the coherent forearm bracers already visible in Image 1: each arm's bracer must remain one continuous piece of leather with consistent color, gold trim, ornament and lighting from upper elbow side to wrist side. Make skin, hair, facial features, fabric scale, leather grain and rivets crisp, richly painted and smooth at enlarged display size; remove blocky upscaling pixels, red edge halos and jagged matte colors. Keep the original avatar's dark hair, brows, eyes, beard shape and expression. Do not redesign or shift the pose, change limb length, crop any finger, alter the bracer pattern halfway down, add equipment, add scenery, add labels, or add shadows. Output exactly one complete empty-handed full figure on clean genuine transparent alpha.
```
