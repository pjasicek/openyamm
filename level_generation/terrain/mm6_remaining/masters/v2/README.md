# MM6 remaining terrain masters — v2

[Original / v1 / v2 comparisons, repeats, tiles and prompts](index.html).

- Cracked ground: larger main plates and greater spacing between cracks, with the same clay/olive colour family.
- Tropical: larger interleaved angular segments, keeping the established green palette.
- Sand: repairs the cut dune ridges identified in 1281.png. The old donor-strip quilting was inappropriate for these broad shapes: wrap-pixel checks passed while internal patches were visible. The original generated tile was half-shifted, imagegen repainted the disconnected central cross, and periodic Poisson insertion transferred those gradients to the outside band. No copied border strips or averaged colour bands. The central 352×352 pixels of the 512px source remain exactly unchanged.
- Snow and accepted swamp: master and runtime PNGs remain byte-identical to v1.

512px masters are in `materials/`. 256px runtime exports are in `runtime_x2/worlds/mm6/terrain_x2/`. The current enhanced playtest and all transitions remain untouched; these are revised master candidates for review.

The built-in imagegen tool produced three edits. Inputs, raw outputs, prompts and file hashes are retained. Sand's input is `raw/sand_offset_input.png` and its AI guide is `raw/sand_repair.png`. Cracked/tropical reuse the periodic material quilting convention; sand instead uses `repair_sand.py` because broad ridge geometry requires connected reconstruction. All runtime reductions use wrapped gutters.

Rebuild from repository root:

```sh
python3 level_generation/terrain/mm6_remaining/masters/v2/build.py
python3 level_generation/terrain/mm6_remaining/masters/v2/review.py
```

`report.json` records hashes and seam screening. `sand_multiscale.json` adds internal-column diagnostics at native and blurred contour scales; these are diagnostic profiles, not a substitute for visually checking ridges. Review covers original/v1/v2 comparisons, repeated tiles and half-tile offsets. Seamless material still repeats its recognizable motif; no in-engine or transition validation is claimed here.
