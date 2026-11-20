# Bat review and reproduction

Accepted 78 unique native images: 48 referenced images and all 30 unused batst poses. Native idle/walk/fidget share the same six-frame flight cycle; preserved that reuse, all action timing, five stored views, mirrored aliases, native variant scales and anchoring. Unused poses are restored without adding gameplay sequences; their differently indexed draft coloration is normalized to the accepted base identity.

Reviewed all native/raw sheets, ordered all-frame base and mask contacts, all standing palettes, magnified light/dark contours, mirrored walk view 6 / palette 666 / frame 4 and hit view 0 / palette 668 / frame 3 in the offline viewer. The first unused sheet duplicated a head and misplaced a profile head: rejected checkpoint retained, corrected cells accepted, with the already-correct folded front cell copied from the first sheet. generation.json records that exact cell composite. The blue base wing lighting needed explicit native pose/view shadow gains; these operate on enhanced wing coverage with a soft center blend, not native pixel masks or per-frame histogram normalization. A fixed 0.82 overall gain retains dark native weight.

R8 wing masks protect black finger bones, purple body, red eyes, pink ears and ivory details. Linear recoloring made native red-wing shadows too dark; replaced it with fixed native-used luminance lookup curves. Final red hit comparison preserves the native brighter red shadows. Purple-safe matte extraction preserves intentional body/ear coloration; light-feature and two-pixel contour cleanup removed demonstrated pink fang/claw contamination. Final generic magenta candidate counts are 585 cleaned and 772 exported/atlas-extracted; the remaining reviewed contact points lie inside intentional pink ears and purple body details, not an external magenta halo. Alpha is unchanged by grading/recoloring. See validation.json and review/edge_current.png.

The enhanced wing's fine cracked leather detail and muzzle anatomy are interpretive. Some native asymmetric lighting and unused draft details remain approximate. Native motion silhouettes and broad colors are retained. Sequence/contact and paused-viewer checks are not GPU performance measurements.

Rebuild from repository root:
```
python3 level_generation/creatures/mm6_bat/process.py
python3 level_generation/creatures/mm6_bat/package.py
python3 level_generation/creatures/mm6_peasants/build_viewer.py bat
```
Rebuilding resets visual acceptance. Staged only; no gameplay installation or original replacement.
