# Re-light: Drangheim Prison (`drangheimprison`)

**State: DONE (2026-10-31 04:52).** Lightmap-matched bake and MM9 model lighting installed; record in
`level_generation/projects/mm9r_drangheimprison/README.md` "Baked lighting".

- Profile: direct 0.75 -> **0.41**, ambient 0.55 -> **0.58** with **`ambient_colour` (0.8, 1, 1)** (MM9's AmbientLight
  40 50 50 is under its lightmaps: red never below 41), `max_lighting` 4 -> **1**, bounce 6, dirlights. Recompose only.
  Old profile: `work/profile_capture_matched.yml`. Zones: new `hue_zones.py` (ten k-d boxes).
- Per-zone ratio before -> after: z01 1.25 -> 1.00, z02 1.29 -> 1.02, z03 1.12 -> 1.00, z04 1.08 -> 0.96, z05 1.09 -> 0.96,
  z06 1.12 -> 0.99, z07 1.33 -> 1.06, z08 1.28 -> 1.01, z09 1.26 -> 1.02, z10 1.27 -> 1.02. Hue: lower storey B/R
  1.66-1.76 (MM9 1.83-2.03; before 1.62-1.78), upper levels 0.97-1.03 (MM9 0.99-1.10; before 0.76-0.85).
- Screen (52 views): capture 33.5, unbaked 57.5, old 32.1, **new 25.0**. Darkest `39-l01_stairs` 15.4. No floor needed.
- Props: **`model_lighting: true`** (rebuild; BLV identical, scene gained the block): relative prop brightness capture
  1.07, old 1.81, model 1.40; props under x0.6 of their view: old 4, model 0. Nagate beetles read brown near orange
  lamps under model lighting. `work/relight/model_lighting_props.txt`, `review/lighting_v07_props_compare.jpg`.
- Scenarios chests, doors_exits, immobile, quests, scripted pass after the rebuild.
- `stale_bakes.py --check`: not listed. Sheet (looked at): `mm9r_drangheimprison/review/lighting_v07_compare.jpg`,
  `_p01-p09`.
- Not checked: no real MM9 screenshot; the 8 capped lights do not reach models.
