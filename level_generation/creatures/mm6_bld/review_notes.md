# Bloodsucker review and reproduction

Accepted 78 unique native images: 48 referenced images and all 30 unused fidget/wince poses. Native standing/walk/hit reuse, separate fidget, six-frame lunge, five-frame collapse and separate corpse hold are retained. Five stored views, mirrored aliases, 125 ms timing, native 0.699997 scale and bottom anchoring are preserved. Unused images do not introduce new timelines.

Reviewed every native/raw sheet, all-frame base and mask contacts, all standing palettes, light/dark magnified edges and offline viewer comparisons: mirrored walk view 6 / palette 162 / frame 4, close attack view 0 / palette 673 / frame 2, death view 0 / base palette 672 / frame 4. Fixed 0.76 gain and 0.82 body saturation reduce generated bright green/tan weight. Wing folds, curled-tail flight, mouth-forward lunging foreshortening and collapse silhouettes follow native poses. AI bone/spine details and surface cracks are interpretive; some fine limb and mouth shading differs from native.

Four enhanced material channels select body, membrane, eye and pink maw/underside. Pale bones, spines, talons and teeth remain protected. Initial membrane selection left brown patches in variants; widened hue coverage and fitted only native purple-changing membrane indices. Recomputed the stored LUTs after adding eye/mouth channels; the first stale-LUT export was rejected visually (black mouths). Final mouth and wing colors reviewed after regeneration. Native-used fixed sigma=4 luminance LUTs derive both variants from the same enhanced base. Always recompute recolor_vectors.json when changing materials.fit; package.py deliberately consumes that stored checkpoint.

Source/palette hashes, all 78 provenance entries, crop/atlas reconstruction, alpha preservation, base bypass, four-channel weight sums and native sequences pass. Magenta candidates: zero cleaned, exported and atlas-extracted. No demonstrated contour spill remains. These sequence/contact and paused-viewer checks do not establish GPU performance.

Rebuild from repository root:
```
python3 level_generation/creatures/mm6_bld/process.py
python3 level_generation/creatures/mm6_bld/package.py
python3 level_generation/creatures/mm6_peasants/build_viewer.py bld
```
Rebuild resets visual acceptance. Staged only; no gameplay installation or original replacement.
