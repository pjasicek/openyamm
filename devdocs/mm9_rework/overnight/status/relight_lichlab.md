# Re-light: Lich Lab (`lichlab`)

**State: DONE (2026-10-31 05:20).** Lightmap-matched bake and MM9 model lighting installed; record in
`level_generation/projects/mm9r_lichlab/README.md` "Baked lighting".

- Profile: direct 0.9 -> **1.65**, ambient 0.95 -> **0.655**, sky 0.75 -> **0.05**, `max_lighting` 4 -> **1**, bounce 6.
  Recompose only. Old profile: `work/profile_capture_matched.yml`. Zones: new `hue_zones.py` (ten k-d boxes).
  MM9 here is a flat neutral floor (0.224, AmbientLight 60) with bright pools: lower floor, stronger lamps.
- Per-zone ratio before -> after: z01 1.16 -> 0.94, z02 (teal pods) 0.96 -> 0.78, z03 1.11 -> 0.88, z04 1.26 -> 1.04,
  z05 1.28 -> 1.05, z06 1.18 -> 0.94, z07 1.28 -> 1.07, z08 1.24 -> 1.02, z09 1.28 -> 1.09, z10 1.27 -> 1.08.
  Hue: ours a little warm (B/R 0.87-0.94, MM9 0.94-1.08); pods too neutral (LIGHTDEFS lights need a bake to raise).
- Screen (40 views): capture 34.4, unbaked 43.2, old 33.5, **new 29.8**. Darkest `13-u13_east_wing` 16.6. No floor.
- Props: **`model_lighting: true`** (rebuild; BLV identical): props under x0.6 of their view old 14, model 1; relative
  brightness capture 0.97, old 0.54, model 0.99.
- Scenarios chests, doors_exits, scripted pass after the rebuild.
- Note for converter owners: Lich Lab's `overrides.yml` now has `model_lighting: true`, so its full build's scene
  differs from builds before 2026-10-31 05:15 (the BLV does not). Compare before/after a converter change from the same
  overrides.
- `stale_bakes.py --check`: not listed. Sheet (looked at): `mm9r_lichlab/review/lighting_v05_compare.jpg`, `_p01-p07`.
- Not checked: no real MM9 screenshot; the 74 capped lights do not reach models; the warm lamp hue and the pods left.
