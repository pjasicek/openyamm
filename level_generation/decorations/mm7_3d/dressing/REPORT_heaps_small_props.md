# Report: heaps and small props (helper of the dressing builder, 2026-10-15)

All six models were built, reviewed and installed through `tools/install_model.py --engine`, after passing
`finish.py` (one mesh node, linked LODs, COLOR_0 on every primitive, base on the ground). None is bound yet.

Concurrent `finish.py` runs can lose entries in `work/installed.json`: one run dropped `mm7_deco_dec97.glb`, which was
added back. Check that file before reinstalling.

| Model | Sprite (placements, map) | LOD triangles | File | Height | Kind |
|---|---|---|---|---|---|
| `mm7_deco_7dec46.glb` | gold goblet (6, t02) | 1392 / 360 / 128 | 0.26 MB | 46 | indoor |
| `mm7_deco_dec97.glb` | metal vase (1, 7d18) | 2304 / 648 / 100 | 1.47 MB | 66 | indoor |
| `mm7_deco_dec96.glb` | gold eagle on a ball (1, 7out13) | 2068 / 756 / 296 | 0.64 MB | 52 | outdoor |
| `mm7_deco_7dec16.glb` | dead snag and fallen logs (1, out11) | 1744 / 564 / 144 | 1.24 MB | 127 | outdoor |
| `mm7_deco_7dec11.glb` | earth mound with rocks and dead shrubs (1, 7d29) | 4628 / 1204 / 376 / 110 | 5.34 MB | 185 | indoor |
| `mm7_deco_7dec10.glb` | junk heap (1, 7d29) | 5912 / 1848 / 966 / 290 | 5.80 MB | 127 | indoor |

Review sheets: `review/<sprite>/compare.png` and `lods.png`.

## Where the sprites differ from the brief

- **7dec16** is a gnarled dead snag standing in a criss-cross of fallen logs, not a pile of logs.
- **7dec10 and 7dec11** are seen from above. Their art heights (202 and 185) include the heap's depth. 7dec10 binds at
  its model height (127) and keeps the sprite's 256-unit width.

## Suggested bindings

```yaml
# indoor_decorations.yml
- name: 7dec46
  model: engine/models/mm7_deco_7dec46.glb
  height: 46
- name: dec97
  model: engine/models/mm7_deco_dec97.glb
  height: 66
- name: 7dec11
  model: engine/models/mm7_deco_7dec11.glb
  height: 185
- name: 7dec10
  model: engine/models/mm7_deco_7dec10.glb
  height: 127
# decorations.yml (outdoor; re-bake 7out13 and out11)
- name: dec96
  model: engine/models/mm7_deco_dec96.glb
  height: 52
- name: 7dec16
  model: engine/models/mm7_deco_7dec16.glb
  height: 127
```

## Build

- **Measurement.** Procedural Blender models traced from the x2 sprites. `scripts/small_measure.py` measures
  half-widths and colours per 5 % of the height.
- **Textures.** CC0 Poly Haven sets in `textures/source/<asset>/` (`scripts/small_fetch.py`), turned into
  `textures/misc_*` by `scripts/small_textures.py`. The procedural `bonelight` texture is read from
  `../../mm6_dungeons_3d/hanging/textures`.
- **Colour.** Dungeon models get COLOR_0 = occlusion × a tint per part group. Outdoor models get occlusion × a grade
  fitted with `review.py --outdoor`.

Per model:
- **Goblet and vase** (`small_lathe.py`): lathes of the measured profiles. Painted bands of reflection stand in for
  the metal look.
- **Eagle** (`small_eagle.py`): stepped wing rows, a shield breast, a hooked-beak head, legs and talons on a ball, a
  two-step plinth, and gold with `openyamm_specular` 0.7.
- **Snag and logs** (`heap_logs.py`): swept tubes along traced branch paths, with bark_platanus.
- **Earth mound** (`heap_mound.py`, `heap_lib.py`): a height-function mound with soil above gravel, displaced
  rocks and three bare shrubs.
- **Junk heap** (`heap_junk.py`): a mound carrying 16 barrels, 9 open crates, pots, lids, red cloths, bones and a
  jug, stacked by downward ray casts.
  - LOD1 and LOD2 turn the crates into blocks and drop the small items.
  - LOD3 keeps the mound and five barrels.

**Sources.** Poly Haven, CC0: rusty_metal_02, gravelly_sand, brown_mud_rocks_01, brown_mud_dry, wooden_barrel,
weathered_planks, rusty_metal_05, green_metal_rust, dirty_carpet, bark_platanus, rock_boulder_dry and
rock_pitted_mossy. rough_wood and metal_plate_02 were fetched but not used. All geometry is our own.

## Rebuild

Run from this folder:

```
python3 scripts/small_fetch.py && python3 scripts/small_textures.py
blender -b --python scripts/small_lathe.py -- 7dec46     # and dec97
blender -b --python scripts/small_eagle.py -- 0.55 0.56 0.44
blender -b --python scripts/heap_logs.py -- 0.76 0.59 0.45
blender -b --python scripts/heap_mound.py
blender -b --python scripts/heap_junk.py
blender -b work/<prop>.blend --python scripts/review.py -- <prop> 0 <elevation> [--outdoor]
python3 scripts/sheet.py <prop> <x2 sprite file>
python3 scripts/finish.py <prop> --install                # table scripts/finish_misc.py
```

Review elevations: 7dec46 8, dec97 14, dec96 6 (`--outdoor`), 7dec16 6 (`--outdoor`), 7dec11 20, 7dec10 25.

## Compromises

- **7dec46, dec97:** the metallic shine is painted as bright and dark vertical bands, which turn with the
  placement's yaw.
- **dec96:** the gold is matte ochre with less sparkle than the sprite.
- **7dec16:** the log ends are flat caps, not splintered.
- **7dec11:**
  - The gravel is smoother and finer than the sprite's.
  - The mossy rocks are lumpy blobs.
  - The edge between soil and gravel is ragged along the mesh triangles.
- **7dec10:**
  - It has fewer pieces than the sprite's clutter.
  - At LOD1 and LOD2 the crates are solid blocks.
  - At LOD3 one barrel rides slightly above the coarser mound.
