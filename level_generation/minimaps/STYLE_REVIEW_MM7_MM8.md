# MM7/MM8 style correction requested after deployment

**Current direction (2026-09-28):** the user selected native ESRGAN upscaling for MM7/MM8.
See [the model study and recommendation](esrgan_study_20260928/README.md). The Blender work below is retained
research; its final prepared masks were not rendered or accepted.

Feedback: 2026-09-27. MM6 captures fit the desired look. MM7/MM8 need a separate visual calibration.
The completed batch/deployment receipts remain historical records; they do not establish visual equivalence.

The user subsequently authorized the Blender calibration. Four review candidates and their editable scenes are
available in [style_v2_20260927](style_v2_20260927/README.md).

## Evidence reviewed

- `test_img/2055.png`: MM8 Ravenshore (`out02`). The original has rounded riverbanks, dark bank outlines,
  lavender-blue shallows, very dark offshore water, subdued terrain and strongly readable building relief.
  The capture exposes tiled banks, nearly uniform water color, sharp material boundaries and stronger terrain relief.
- `test_img/2056.png`: MM8 Garrote Gorge (`out05`). The original rounds and simplifies the river, blends
  grass into the mountains, softens relief and gives buildings a distinct turquoise palette.
- `test_img/2057.png`: MM7 Avlee (`out14`). The original has rounded island silhouettes, cyan coastal water,
  deeper blue offshore, softer terrain transitions and more legible building highlights/shading.
- `test_img/2058.png`: MM7 Evenmorn Island (`out09`). Broad cyan-to-dark-blue water bands are especially clear;
  the capture's repeated water texture and angular shore edges do not reproduce them.

These observations establish different visual treatment, not the original studio's exact software/process.

## Cause and limits of the previous checks

The batch reused the MM6 lighting template and grading recipe for all worlds. Water was sampled from game textures
with no distance-to-shore color treatment. Terrain used an unsmoothed tile atlas and mostly smoothed normals with
15% native face normals. Buildings used current restored game textures and the same independent levels curve.
Those operations do not reproduce the painted coasts, regional palettes and object readability above.

The zero projection-error result checks our captures against ODM coordinates. It neither compares the native
painting's silhouette/feature extents nor proves a matching style. The previous visual overview check missed these
differences. A close-up of the Evenmorn `house 9E` shows a roof in the raw object layer; a blanket assertion that
missing roof geometry explains the building difference is unsupported.

## Next calibration

Use Evenmorn Island for MM7 and Ravenshore for MM8, with Avlee and Garrote Gorge as cross-checks.
Target the original painted treatment unless the user prefers a refined version of the current rendered look.

1. Build a separate shoreline mask, round its small tile steps and feather the bank transition within a measured
   tolerance. Protect bridges, docks, roads and building positions. Record shoreline displacement separately from
   the unchanged geometry projection checks.
2. Shade water using distance from the bank: cyan/deep blue for the MM7 examples, lavender shallows/dark offshore
   water for these MM8 examples. A constant blue texture and global blur are insufficient. Underwater and elemental
   maps require their own masks; do not classify lava or the underwater floor as ordinary open water.
3. Soften terrain normals/shading and blend material transitions independently, preserving the selected light grain.
4. Calibrate building palette and relief independently of terrain, checking roofs/walls and small landmark readability
   against the originals at actual minimap size. Avoid a global filter over the whole composite.
5. Review the two small comparisons before repeating a batch. Retain MM6's accepted treatment and the immutable
   deployed revision. A subsequent approved revision should use the existing replacement-ledger workflow.

Original-derived upscaling remains a fallback if matching the painted artwork would require too much reconstruction.
The initial inspection made no revised art or deployment. The linked follow-up contains the new calibration art;
the existing accepted/runtime revision remains installed while its visual differences are reviewed.
