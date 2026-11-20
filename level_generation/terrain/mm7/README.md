# MM7 terrain restoration

This project restores every terrain texture used by the **13 MM7 outdoor ODM maps** in this checkout:
**102 static names plus 14 water animation frames = 116 runtime PNGs**. Land and shoreline tiles are
128→256px; hardware water frames already start at 256px and retain that runtime size. Master materials
and transition fields are authored at 512px.

[Interactive comparison gallery](index.html) · [Runtime ZIP](mm7_complete_terrain_x2.zip) ·
[Inventory](inventory.json) · [Validation](reports/validation.json) · [Native review](reports/review.json) ·
[Installation audit](reports/integration.json) · [Continuation notes](HANDOFF.md).

Run the prepared real-MM7 test stage:

```sh
./level_generation/terrain/mm7/play.sh enhanced
./level_generation/terrain/mm7/play.sh original
```

The launcher starts Emerald Island. Other MM7 maps use the same installed pack when terrain quality is `x2`.
The main development installation is `assets_dev/worlds/mm7/terrain_x2/`, alongside the originals.
Its installation does not change global settings or the separate bmodel `textures_x2` packs.
Existing sprites, decorations, event scripts and other enhanced content remain intact.

The current v5 roads reuse matching MM6 silhouettes and imagegen-fitted stone borders, with
continuous finished artwork across tile joins to remove the fragments reported in `1288.png`.
All 19 roads retain solid coverage. [Road join correction](roads_v5/README.md) · [Workflow and prompts](roads_v4/README.md) ·
[Mask checks](reports/road_masks.json). Accepted master materials and other terrain are unchanged.

## Coverage

| Family | Static textures |
| --- | ---: |
| Dirt and pebble variants | 3 |
| Grass and dirt transitions | 13 |
| Sand and dirt transitions | 13 |
| Snow and dirt transitions | 13 |
| Swamp, two variants and dirt transitions | 15 |
| Cracked wasteland and dirt transitions | 13 |
| Cobblestone roads, junctions, caps and diagonals | 19 |
| Transparent dirt shorelines | 12 |
| Water fallback | 1 |

The original palette, material feature scale, transition geometry, interleaving and contact shading guide
the restoration. Roads use a masked foreground cobblestone material. Shorelines use the same restored dirt
phase as inland tiles, with the original damp-bank colour treatment and filtered alpha over animated water.

## Verification boundaries

The final report checks every compatible tile pairing, with shores and open water evaluated at matching
animation frames. Flat native fixtures exercise islands, inverted dirt holes, roads and variants; real-map
comparisons include Emerald Island, Bracada, Mount Nighon, Deyja, Tatalia and Shoals. Water has a native timed
capture and camera-movement views. This is not an exhaustive check of every map cell, camera angle, mip level
or GPU configuration, and software-display captures are not GPU performance measurements.

The native map scan identifies **1,189 placements** whose neighbouring material edge contracts disagree.
[Exact locations](reports/native_layout_mismatches.csv) and original/restored native contexts are included.
Those map layouts remain unchanged; compatible-asset seam checks do not make incorrect map arrangements
seamless. No MM6 map correction was transplanted into MM7.

## Rebuild and review

```sh
python3 level_generation/terrain/mm7/inventory.py
python3 level_generation/terrain/mm7/prepare_masters.py
python3 level_generation/terrain/mm7/roads_v4/prepare.py
python3 level_generation/terrain/mm7/roads_v4/compose.py
python3 level_generation/terrain/mm7/build_land.py
python3 level_generation/terrain/mm7/build_water.py
python3 level_generation/terrain/mm7/roads_v4/review.py
python3 level_generation/terrain/mm7/check_roads.py
python3 level_generation/terrain/mm7/check.py
python3 level_generation/terrain/mm7/build_pose_helper.py
python3 level_generation/terrain/mm7/prepare_review.py
# Run the capture scripts under xvfb-run or a real X display; see HANDOFF.md.
python3 level_generation/terrain/mm7/review_animation.py
python3 level_generation/terrain/mm7/package.py
python3 level_generation/terrain/mm7/install.py
```

Generation itself used the built-in imagegen tool. Raw outputs and exact prompts are retained; the rebuild
scripts use those saved outputs and do not make additional AI calls. Inspect all changed artwork and refresh
native captures before packaging a new iteration.
