# Re-light: Temple of Honk (`templeofhonk`)

**State: DONE (2026-10-31 04:35).** Lightmap-matched bake installed in `output/mm9_rework/assets_dev`; record in
`level_generation/projects/mm9r_templeofhonk/README.md` "Baked lighting".

- Profile `tools/lighting/baked_indoors/profiles/mm9_templeofhonk.yml`: direct 0.65 -> **0.3**, ambient 1.15 -> **0.62**,
  sky 0.35 -> **0.8**, `max_lighting` 4 -> **1**; bounce 6. Recompose of the saved passes (no Cycles). Old profile kept as
  `work/profile_capture_matched.yml`.
- Zones: new `hue_zones.py` (eight k-d boxes, `mm9r_common/relight_zones.py`).
- Per-zone lightmap luma ours/MM9, before -> after: z1 1.72 -> 0.90, z2 1.76 -> 0.97, z3 1.72 -> 1.02, z4 2.06 -> 1.07,
  z5 1.83 -> 1.01, z6 1.98 -> 1.02, z7 1.79 -> 1.04, z8 1.69 -> 0.93; hue matches everywhere (MM9 neutral-warm).
- Screen (30 views, centre luma): capture 124.6, unbaked 120.9, old bake 127.0, **new 73.2**. Darkest baked view
  `11-northwest_corridor_south` 44.2. No player-light floor needed (MM9's darkest texels here 0.3).
- Props: **old path kept** (sector min light 14, `model_lighting: false`): relative prop brightness old 1.15, model
  lighting 0.74, capture 0.80; the 3 capped fill lights miss the model path. By eye the old path blackens the west wing
  tables (view 12). `work/relight/model_lighting_props.txt`, `review/lighting_v03_props_compare*.jpg`.
- Rebuilt twice for the model-lighting trial (BLV and scene byte-identical at the end); scenarios doors_exits, chests,
  scripted, hostility all pass (`work/relight/scenario_*.log`).
- `stale_bakes.py --check`: not listed.
- Sheet (looked at): `level_generation/projects/mm9r_templeofhonk/review/lighting_v03_compare.jpg`, `_p01-p05.jpg`.
- Not checked: no real MM9 screenshot exists for this map; actors' look under the darker bake not reviewed in detail.
