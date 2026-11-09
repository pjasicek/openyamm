# Barbarian review and reproduction

Accepted all 57 native unique and referenced images. Native standing, five stored walking views, front attack/hit/fidget/death/corpse, mirrored view aliases, timing, palette-specific scales and logical anchoring are retained. Blue palette 664 is the sole generated base; armor and leather masks derive palettes 663 and 665 using fixed native luminance ramps.

Reviewed every raw sheet, ordered all-frame base and mask contacts, all standing variants, magnified light/dark edges and offline viewer samples: mirrored walk view 6 / palette 663 / frame 4 and death view 0 / palette 665 / frame 3. No demonstrated pose or sequence discontinuity remained. These sequence/paused-viewer checks are not GPU performance measurements.

Fixed RGB gain 0.88 reduces overbright generated materials. Armor color selection initially included the sword's blue reflections. A native-index principal-axis guide was rejected because it cut actual armor and missed enhanced blades. The accepted protection uses visually reviewed enhanced blade axes (blade_axes_reviewed.json), including eight manually corrected short/rear blades. Gold, skin, hair and scabbard remain protected. The nearly black raised glove in bar1ded0 needed an explicit enhanced-art selection after final variant review. Mask coverage preserves dark shadows and straps rather than flattening their shading. Cleaned/exported/atlas-extracted magenta candidates above 16 are zero; inspected contours are clean.

Fine armor scales, gold details and hair strands are interpretive. Blades retain cool enhanced silver reflections rather than the native palette's warm pale highlights. Broad color, tonal mass, silhouette and identity remain recognizable.

Rebuild from repository root:
```
python3 level_generation/creatures/mm6_bar1/process.py
python3 level_generation/creatures/mm6_bar1/package.py
python3 level_generation/creatures/mm6_peasants/build_viewer.py bar1
```
Rebuilding resets visual acceptance. Staged only; originals and gameplay unchanged.
