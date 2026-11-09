# Nobleman review and reproduction

Accepted all 71 unique native images: 58 referenced and 13 additional unused native poses. Native actions, five stored directions/eight aliases, timing, logical placement and scale are preserved. Unused draft poses are retained without adding timeline bindings; their differently indexed native clothing is normalized to the accepted family base, with source artwork retained.

Reviewed every raw sheet, ordered all-frame base and mask contacts, all three standing palette variants, enlarged light/dark edges and offline viewer samples (walk view 6/palette 777/frame 4; death view 0/palette 779/frame 3). These sequence and paused-viewer checks are not a GPU performance measurement. Fixed RGB gain 0.88 matches native cloth/gold tonal weight. Enhanced soft coverage separates cape from tabard; corrected their blue/violet boundary using enhanced connected regions. Fixed native luminance ramps derive olive/burgundy and magenta/brown appearances. Hair, skin, silver, gold, gloves and boots remain protected. All-frame contour checks show zero residual magenta candidates above 16 in cleaned, exported and atlas-extracted images.

Fine woven fabric and brighter side-facing blade detail are interpretations of low-resolution artwork. Native silhouettes, equipment and action order remain recognizable. Extraction contacts precede final grading; packaged contacts/viewer include it.

Rebuild from repository root:
```
python3 level_generation/creatures/mm6_nobl/process.py
python3 level_generation/creatures/mm6_nobl/package.py
python3 level_generation/creatures/mm6_peasants/build_viewer.py nobl
```
Rebuild resets visual acceptance. Stage only; no gameplay installation.
