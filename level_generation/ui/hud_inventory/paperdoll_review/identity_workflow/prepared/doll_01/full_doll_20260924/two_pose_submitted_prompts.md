# PC01 two-pose imagegen submissions

All inputs and returns are preserved in this folder. The assigned original avatar is
`../assigned_portrait_original_x4.png`. The two-pose source is
`source_two_pose_sheet_x4.png`, generated directly from the original native sprites at
game-table offsets. See `TWO_POSE_HASHES.sha256` for hashes.

## V1

Inputs in order: `source_two_pose_sheet_x4.png`,
`../assigned_portrait_original_x4.png`, `raw_detail_repaint_v5.png`.
Return: `raw_two_pose_sheet_v1.png`.

```text
Use case: precise paired 2D RPG paperdoll restoration. Image 1 is the EDIT TARGET and exact layout: ONE ROW with TWO EQUAL-WIDTH CELLS split at exactly 50% of the canvas. Its transparent left cell is the naked/no-item PC01 pose. Its transparent right cell is THE SAME PC01 body, head, legs and screen-right hanging hand at THE SAME coordinates, changing only the screen-left arm to the original horizontal open-grip `pc01rhu` pose. No sword, shield, equipment, background, doll backdrop, floor, frame, labels, separator line or checkerboard. Image 2 is the ORIGINAL assigned avatar head and is the authority for the man's face, hair, eyes, brows, nose, beard and expression; make both cell heads the same person and identical to each other. Image 3 is an already accepted high-detail visual-style reference for the character's painted skin, dark-green trousers, red-brown engraved leather and bracer trims; use only its surface quality/material, NOT its canvas/framing or changed limb positions. Repaint BOTH original cells into coherent smooth high-resolution fantasy game art while preserving Image 1's exact pair layout, equal cell boundaries, body scale, pose, silhouette, shoulders, elbow seams, wrists, hands, boots and item-grip location. The same body, face, legs, boots, screen-right hanging arm, colors, lighting and detail MUST be identical in both cells; only the screen-left arm changes from relaxed diagonal/open hand in cell 1 to the horizontal open grip in cell 2. Maintain complete natural separated fingers, seamless continuous leather bracers, and genuine clean transparent alpha around each isolated figure. Render the figures separately in their own half; never let pixels cross the 50% cell border. Do not enlarge/recenter either figure or redraw it into a single character. Output exactly one two-cell sheet that can be split vertically at 50% without overlap.
```

## V2

Inputs in order: `source_two_pose_sheet_x4.png`, `raw_two_pose_sheet_v1.png`,
`../assigned_portrait_original_x4.png`, `original_pc01rhu_x8.png`.
Return: `raw_two_pose_sheet_v2.png`.

```text
Use case: GEOMETRY-CORRECTION EDIT of a paired paperdoll spritesheet. Image 1 is the ORIGINAL SOURCE SHEET and ABSOLUTE SILHOUETTE/LAYOUT AUTHORITY: one row, two equal columns, transparent background, the exact PC01 naked/no-item pose on the left and the same PC01 with the original horizontal open-grip arm on the right. The first generated attempt in Image 2 has good painterly material but it enlarged the figures inside their cells and made the held hand into a fist; correct those two errors. Image 3 is the ORIGINAL assigned avatar identity for both identical faces. Image 4 is a close view of the ORIGINAL pc01rhu open grip: separated fingers and lifted thumb, NOT a fist. Produce ONE transparent two-cell sheet with the same cell proportions and placements as Image 1. Each figure must have transparent margin above its hair equal to about 9% of CELL height, transparent margin below its lowest boot about 5%, and its full-body silhouette must remain within approximately 15%-91% of CELL width. In the right cell, the horizontal grip extends to about 15% of CELL width; do not let its fingers reach the cell border. The original shoulders, head, elbows, wrists, waist, knees, feet and hand locations are all more important than Image 2's enlarged outlines. Preserve the exact original pose and natural proportions, and transfer Image 2's high-detail skin, beard, dark-green trousers and red-brown bracer/armor finish into those original outlines. Both cells show the same pixel-identical body/face/legs/boots and screen-right hanging arm; ONLY the screen-left arm differs. Right cell: open grip with visible separate fingers and lifted thumb, no closed fist. Keep elbows and bracer patterns continuous. No equipment, doll backdrop, scene, floor, labels, separator, checkerboard or pixels across the 50% boundary. The return MUST have two precisely equal cells that can be split at the midpoint.
```

## V3

Inputs in order: `source_two_pose_sheet_x4.png`,
`../assigned_portrait_original_x4.png`. Return: `raw_two_pose_sheet_v3.png`.

```text
Restore the transparent PC01 paperdoll directly from Image 1 as ONE ROW OF TWO EXACTLY EQUAL CELLS. Image 1 is the original game artwork already assembled at the real game coordinates: left cell empty/naked pose; right cell the SAME body with only its screen-left arm changed to the original horizontal open-grip hand. This source image is the strict guide for all silhouettes and relative positions. Image 2 is the original avatar head: both cells must have that same face, dark hair, beard and expression. Paint over the original pixelated surfaces with smooth high-resolution, crisp fantasy game art while preserving the original pose, arm orientation, finger arrangement, body proportions, item grip location, and the amount of transparent margin around both figures. The body, head, screen-right hanging arm, trousers, boots and every unchanged detail must be identical in the two cells. Restore the screen-left grip in the right cell as the original OPEN hand with visible separate fingers and lifted thumb, never as a fist. Keep both bracers continuous with their upper arms and make all fingertips complete. Return one sheet that can be cut at exactly half its width into two transparent full-doll images. No third figure, no sword, no shield, no inventory background or paperdoll background, no scene, no floor, no labels, no divider, no checkerboard, no shadows, no cropped limb and no opaque backdrop.
```
