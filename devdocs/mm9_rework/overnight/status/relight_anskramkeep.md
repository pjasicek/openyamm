# Re-light: Anskram Keep (`anskramkeep`)

**State: DONE (2026-10-31 04:45).** Lightmap-matched bake installed; record in
`level_generation/projects/mm9r_anskramkeep/README.md` "Baked lighting".

- Profile: direct 1.0 -> **0.46**, ambient 0.5 -> **0.58**, bounce 6, max 1 (unchanged), dirlights. Recompose only.
  Old profile: `work/profile_capture_matched.yml`. Zones: new `hue_zones.py` (ten k-d boxes).
- Per-zone ratio ours/MM9 before -> after: z01 1.35 -> 1.01, z02 1.41 -> 1.02, z03 1.33 -> 0.96, z04 1.24 -> 0.92,
  z05 1.11 -> 0.84, z06 1.47 -> 1.11, z07 1.38 -> 0.99, z08 1.30 -> 0.95, z09 1.37 -> 1.00, z10 1.28 -> 0.94; hue
  matches (warm yellow).
- Screen (30 views): capture 46.4, unbaked 45.9, old 46.9, **new 35.1**. Darkest `25-gate_switch` 17.6. No floor needed.
- Props: **old path kept** (sector min light 20): model lighting (ambient 40) draws wardrobes/beds near black
  (`review/lighting_v06_props_compare.jpg`, `work/relight/model_lighting_props.txt`).
- Rebuilt twice for the trial (BLV/scene identical at the end); scenarios chests, doors_exits, rotating, scripted pass.
- `stale_bakes.py --check`: not listed. Sheet (looked at): `mm9r_anskramkeep/review/lighting_v06_compare.jpg`, `_p01-p05`.
- Not checked: no real MM9 screenshot; sectors 11/17 (small rooms MM9 lights, ours at the floor, x0.5) left as they are.
