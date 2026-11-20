# V2 grip finger-count correction

The goal was to repair the **right figure's screen-left grip** in V2 from thumb + three
visible fingers to thumb + four visible fingers. The raw imagegen returns are unchanged.

## Full-sheet edit 1 — rejected

Inputs: `raw_two_pose_sheet_v2.png`, `two_pose_v2_grip_detail.png`,
`original_pc01rhu_x8.png`. Return: `raw_two_pose_sheet_v2_grip_fix_v1.png`.
The returned sheet still shows only three distinguishable fingers beneath the thumb.

```text
Use case: LOCAL CORRECTION of an existing two-cell transparent PC01 paperdoll sheet. Image 1 is the EDIT TARGET. Edit ONLY the screen-left hand of the RIGHT FIGURE, the horizontal held-item grip. Image 2 is a close crop of the exact defect: the hand has a raised thumb and only THREE curled fingers visible under it. It needs FOUR curled fingers plus the thumb, five digits total. Add one small, anatomically natural curled LITTLE FINGER below the current lowest finger, with its own rounded knuckle and fingertip and a visible dark/transparent crease separating it from the adjacent finger. It must join the existing palm naturally, match the exact skin tone, lighting and painterly detail, and remain inside the original hand's compact grip envelope. Do not add a second thumb or turn the hand into an open fan. Image 3 is the original pc01rhu grip reference and shows four fingers beneath the thumb and the required horizontal bracer-to-grip silhouette. Preserve the current thumb, three existing fingers, cuff, wrist, bracer length/pattern, elbow attachment and item grip coordinates. Keep the LEFT FIGURE and both figures' heads, bodies, legs, screen-right arms, all other pixels, canvas size, two equal cells, transparency and spacing unchanged. No sword, shield, background, labels or extra hand. Output the complete corrected two-cell sheet, not a hand-only crop.
```

## Close-up edit — five-digit source for final composite

Inputs: `two_pose_v2_grip_detail.png`, `original_pc01rhu_x8.png`,
`raw_pc01rhu_isolated_v1.png`. Return: `raw_grip_five_digit_v1.png`.
This one has a thumb and four distinct curled fingers.

```text
Use case: close-up corrective edit of a transparent PC01 paperdoll grip. Image 1 is the exact EDIT TARGET: a horizontal red-brown leather bracer ending in a compact right-hand grip, thumb raised across the top. The close-up has a wrong FOUR-DIGIT hand: thumb plus only THREE curled fingers. Repaint only the hand so it has FIVE digits total: preserve the raised thumb, and render FOUR INDIVIDUALLY DISTINGUISHABLE curled fingers stacked BELOW it, from index to middle to ring to a shorter little finger at the bottom. There must be four separate rounded fingertip/knuckle forms visible on the screen-left edge beneath the thumb, with subtle dark creases between them. Add the missing little finger by refining the lower palm within the existing grip envelope; do not lengthen or shift the bracer/cuff/wrist or move the grip point. The hand remains a compact weapon-holding grip, not an open spread palm. Image 2 is the original pc01rhu sprite showing the intended grip orientation and digit arrangement. Image 3 shows high-detail matching skin and bracer material, but its open hand is not the target pose. Preserve the bracer's red-brown engravings, fur cuff, light direction, transparent alpha and horizontal silhouette. Return ONE isolated hand-and-bracer crop with the same framing as Image 1, no sword, no body, no other hand, no background, no text, no pixelated blocks.
```

## Full-sheet edit 2 — rejected

Inputs: `raw_two_pose_sheet_v2.png`, `raw_grip_five_digit_v1.png`,
`two_pose_v2_grip_detail.png`, `source_two_pose_sheet_x4.png`.
Return: `raw_two_pose_sheet_v2_grip_fix_v2.png`. The generator again merged the bottom
fingers when rendering the complete sheet. It is not the final artwork.

```text
Use case: tiny localized repair of the two-cell transparent paperdoll in Image 1. Image 1 is the EXACT EDIT TARGET; preserve its canvas and everything except the screen-left hand of the RIGHT character. Image 2 is the just-corrected high-detail grip with correct FIVE-DIGIT anatomy: one thumb above FOUR individually visible curled fingers, including a short little finger at the bottom. Image 3 zooms the defective three-finger grip in Image 1; replace that defect with Image 2's digit arrangement while preserving Image 1's compact wrist, cuff, forearm, same grip location and approximately the same hand size. Image 4 is the original table-aligned pair and confirms the arm pose and transparent two-cell layout. In the RIGHT character ONLY, repaint the hand from the cuff outward so the thumb and four fingers can each be counted at normal zoom. Keep the fingers curled for holding a weapon; do not fan them open, draw a second thumb, move the wrist, or extend the hand beyond its current footprint. Keep both characters' faces, bodies, legs, boots, other arms, bracers, spacing, alpha, and 50/50 split unchanged. No sword, shield, background, labels or extra parts. Return the full corrected two-cell sheet.
```

`place_corrected_grip.py` records the final local placement of the successful close-up return.
It does not assert whole-pose registration or change any game asset.
