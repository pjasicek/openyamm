# Rat review and reproduction

Accepted all 59 unique native images: 58 referenced and unused ratfib0, without adding timeline bindings. Native actions, five stored views, mirrored aliases, timing, logical placement and palette-specific scales retained. Palette 809 omits YAML scale; the exporter now applies the documented native SpriteTables.cpp default 1.0, while preserving explicit scales in the other variants.

Reviewed every raw sheet and the ordered all-frame base/mask contacts, all standing variants, magnified light/dark contour contact and offline viewer samples: mirrored walk view 6 / palette 807 / frame 4 and attack view 0 / palette 809 / frame 3. Sequence and paused-viewer checks are not a GPU performance measurement. Native raised forepaws and stretched jumping/rolling poses are intentional. Fixed 0.65 RGB grade matches the dark base B; fur/skin and iris masks derive grey-purple and red-brown native palettes with fixed luminance ramps. Tightened iris selection and protected pale teeth/spikes after the first variant contact. Native red variant itself reddens tooth tips in attack; main ivory tooth highlights remain recognizable. Local three-pixel contour correction limits excess green left by matte unmixing while retaining olive skin interiors and alpha. Final cleaned/exported/atlas-extracted magenta candidates above 16 are zero; inspected edges are clean.

Fur strands, segmented tail and collar details are interpretive enhancements. Grey-purple variant is slightly more muted than native, with the same broad color and tonal mass. Extraction comparison contacts precede final tone grading.

Rebuild from repository root:
```
python3 level_generation/creatures/mm6_rat/process.py
python3 level_generation/creatures/mm6_rat/package.py
python3 level_generation/creatures/mm6_peasants/build_viewer.py rat
```
Rebuilding resets visual acceptance. Staged only; originals and gameplay unchanged.
