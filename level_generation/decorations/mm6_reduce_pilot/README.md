# MM6 decoration reduction survey (2026-10-14, numbers only)

User: "check if the decorations can benefit from this tris reduction as well". Nothing installed or rendered yet.

- `scripts/deco_dump.py` (Blender): LOD0 of each bound decoration (`decorations.yml`, 83 of the 164 models), welded,
  wedge UVs with u + 100 x material (bark UVs tile), opaque flag per face (alpha-mask leaf cards and blended water
  are left untouched).
- `scripts/deco_ladder.py` (venv with pymeshlab): texture-aware collapse of the opaque faces at 70/55/45/35/25 %,
  two-way Hausdorff distance in % of the model height; pass = max <= 1.5 % and mean <= 0.15 % (the creature limits per
  metre). Lowest passing step is the pick. `work/ladder_<name>.json`, `work/survey.txt`. Whole survey: ~45 s.

Result: LOD0 of the 83 bound models 324,589 -> 271,609 triangles (-53k, -16 %). Half of the LOD0 triangles are
alpha leaf cards (163k), which collapse reduction must not touch (thinning cards is a different technique).
Big wins: corpses 04/05/06 (4.6-4.8k -> 2.1-2.7k), sword in the stone (4.4k -> 2.0k), the five pedestals (3.2k ->
1.1-1.4k), rocks 01/04/09/12 and surf rock (2.4k -> 1.3k), tree27/28 bark (-1.5k each), fountain (-1k).
18 models save >= 1,000 triangles, 40 save >= 500, 26 save < 200. No passing step: skullpile_meshy (11k, piles of
small skulls), swptree4 (8.2k bark/roots), rock03/07/13/14, cactus 5/8/17, campfire, food bowl.

## Installed: 18 often-placed decorations (2026-10-14)

User: "do them if it makes sense ... if there are a lot of the given decorations in the level". Ranked by triangles
saved x placements (outdoor: `catalogues/outdoor_decorations/decoration_usage.csv`; dungeons:
`decorations/mm6_dungeons_3d/inventory.json`). Corpses, the sword in the stone and the pedestals save the most per
model but are placed 1-6 times, so they stay. The barrel was left out (its GLB has duplicated faces the survey weld
merged: 1,760 vs 1,280 triangles).

- `scripts/deco_build.py`: reduced opaque faces (deco_ladder pick) + the source alpha faces, vertex colour (baked grey
  AO multiplier) and custom normals transferred onto the reduced vertices only; material decode `floor((u + 50) / 100)`
  (tiling UVs reach below 0: the burning rock's lava turned to stripes with `u // 100`).
- `scripts/deco_swap_glb.py`: swaps the LOD0 primitives by material into the source GLB; alpha-mask/blend primitives
  (leaf cards, foam, fire) stay byte-for-byte (the glTF exporter wrote the leaves' vertex colour white); existing LODs
  kept (all coarser than the new LOD0); bounds checked; compacted.
- `scripts/deco_compare.py`: installed vs reduced, textured, `review/<name>_compare.png`, `review/batch_*.png`.
- Installed with `tools/install_model.py` (cooked); previous sources in `backup_pre_reduce/`.

| model | LOD0 before | after | saved | placements |
|---|---:|---:|---:|---:|
| tree01 | 7,957 | 7,209 | 9 % | 1035 |
| tree27 | 6,398 | 4,734 | 26 % | 233 |
| tree10 | 7,959 | 7,167 | 10 % | 406 |
| tree02 | 7,971 | 7,147 | 10 % | 302 |
| tree17 | 7,950 | 7,302 | 8 % | 306 |
| surfrock_b | 2,364 | 1,328 | 44 % | 158 |
| cac25 | 2,555 | 1,963 | 23 % | 206 |
| tree05 | 7,953 | 7,461 | 6 % | 221 |
| tree18 | 5,964 | 5,542 | 7 % | 249 |
| surfrock_a | 2,364 | 1,674 | 29 % | 150 |
| tree06 | 7,367 | 6,871 | 7 % | 179 |
| tree29 | 2,360 | 1,670 | 29 % | 123 |
| tree04 | 7,953 | 6,955 | 13 % | 76 |
| snotre01 | 5,958 | 5,626 | 6 % | 202 |
| burningrock | 1,696 | 1,036 | 39 % | 114 |
| tree28 | 5,749 | 4,267 | 26 % | 331 |
| rock01 | 2,400 | 1,320 | 45 % | 131 |
| keg | 1,916 | 1,340 | 30 % | 155 |

Regressions: `mm6_decoration_models_keep_native_animation` and `..._indoor_wall_torches` pass;
`..._map_new_sorpigal` fails on `bigbarel` (`mm6_deco_barrel.glb`, 1,760 triangles over its 1,500 budget) — that
file was changed today at 08:00 outside this work (not part of the batch). 15 outdoor lighting bakes are now stale
(`tools/lighting/stale_bakes.py`); re-bake before a release or commit.
