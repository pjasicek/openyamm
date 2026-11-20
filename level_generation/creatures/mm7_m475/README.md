# MM7 blaster actor — staged native restoration

Open [viewer.html](viewer.html) directly for native/restored playback, all directions, native mirrors,
descriptor selection, backgrounds and matching mask overlays. No server or gameplay installation is required.

All 124 native frames are restored: five standing views, 40 walking, 40 attack, 30 reaction, four fidget,
four collapse and one corpse pose. Descriptors 457–459 retain native palette 527 and scale 1. Native action
aliases, frame order, lengths, durations, loop/hold flags and five stored views with mirrored directions remain
in descriptor_animations. The logical canvas is 256×256 with bottom-center pivot (128,256); expanded transparent
storage canvases and exact crop origins retain cape poses extending beyond the logical canvas.

Nineteen selected built-in imagegen sheets provide base artwork once. Twenty-four successful calls include rejected
profile/rear-oblique attack v1 sheets that omitted the native upward muzzle flash. Their accepted v2 edits restore
that flash. All exact prompts, reference hashes, raw outputs, rejection notes and selected versions are preserved
in generation.json. Native blue boot highlights in front/oblique reaction poses are intentional and retained.

Connected-pose extraction preserves cape silhouettes crossing nominal cell boundaries. Each sheet uses one common
scale calibration against native bounds, inverse reference-window placement and recorded native-baseline translation;
individual poses are not stretched. Processing uses a fixed 0.85 RGB multiplier to retain black cloth tonal weight.
Enhanced cool violet cloth is protected during magenta extraction. Contour repair borrows opaque interior hue while
preserving luminance, limits residual magenta outside protected material and neutralizes demonstrated green edge spill.
These settings, extracted cells, aligned artwork and placement records are retained for deterministic reproduction.

There is one native palette. Matching R8 masks contain zero weights; base bypass, alpha and zero-mask pixel identity
are verified. No additional palette or generated variant artwork is invented. The 2× export has RGBA8 pages
with identically packed R8 masks: 61,849,600 decoded bytes (58.98 MiB), including padding.
Four-pixel crop padding and three-pixel invisible RGB extrusion support filtered edges. Offline previews and embedded
viewer imagery are excluded from runtime memory figures.

Visual review covered all 124 native/restored poses, native sequence ordering, light/dark contours, native violet and
blue materials, corrected muzzle flashes and browser captures of the profile flash and mirrored walk. Review contacts
use one shared union window, including negative cape extents. Coverage, unchanged native source hashes, exact crop
reconstruction and atlas extraction, masks, alpha, timings and flags pass validation.json. The cleaned/exported contour
audit finds zero magenta candidates above 32/255 outside intentionally protected cool-colored materials.
Fine facial, cloth and armor surface details remain an AI interpretation of low-resolution native artwork.

The profile attack was reopened after its eight-pose sheet measured 1.996748 generated pixels per native pixel.
Two overlapping six-pose sheets replace only those eight exported frames; four overlap poses guide continuity.
The repaired six-pose v3 preserves native white forearm flash illumination and the upward flash cell margin.
All other selected raw artwork is reused. The minimum actual generated detail now exceeds 2.09549 pixels per
native pixel, separately from 2× runtime size. detail_rebatch_plan.json records crops and measured detail;
checkpoints/before_sampling_repair preserves the prior accepted metadata.

Reproduce processing using accepted checkpoints:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m475 --tone 0.85
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m475
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m475
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m475
```

Reinspect changed outputs and renew acceptance hashes after any processing change. Original assets remain untouched.
