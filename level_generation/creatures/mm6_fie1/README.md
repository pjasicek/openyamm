# MM6 Fire Elemental — validated, staged only

All 47 unique native images are generated for descriptor IDs 529–531 and palettes 204/728/729. Nine compact sheets cover all native poses and stored views. Native timing, mirrors, scale, lighting/transparency flags and the NULL corpse are retained.

Open [review.html](review.html) directly for the native/restored offline viewer. [manifest.json](manifest.json) describes the 2x atlas pages and matching R8 masks in atlas/. See [review_notes.md](review_notes.md), [validation.json](validation.json) and acceptance.json for the checked result. Exact prompts, raw artwork, source hashes, earlier rejections and processing settings are retained.

Reproduce from the repository root:

```sh
python3 level_generation/creatures/mm6_fie1/process.py
python3 level_generation/creatures/mm6_fie1/package.py
python3 level_generation/creatures/mm6_peasants/build_viewer.py fie1
```

Processing cleans the matte, registers frames at native logical placement and applies fixed 0.96 tone. The R8 mask selects the darker red core and protects saturated outer flames. Fixed native-derived LUTs create the green and blue cores while preserving alpha and the exact base palette. A fixed 1.17 input-luminance calibration and dark-shade extrapolation preserve restored core detail. All settings are in materials.py. Repackaging resets visual acceptance; review again before updating acceptance.json.

Decoded base+R8 masks+float32 LUTs occupy 40,342,594 bytes (38.47 MiB), excluding optional variant preview atlases. Flame shapes are smoother and more organized than the native pixels, while poses and color character are retained. Gameplay installation and LUT-aware runtime support are separate tasks. Originals and gameplay were not changed.
