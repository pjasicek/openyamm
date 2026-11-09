# Brackenford settlement density revision

The house art accepted in the previous revision is retained. The driver's `test_img/1218.png` versus
`test_img/1219.png` comparison showed excessive plot spacing; this revision changes the town layout around those houses.

Run the fresh God snapshot:

```sh
/tmp/openyamm-brackenford-playtest-density/play.sh outdoor
```

Choose **Load Game → Scenario**. `play.sh indoor` starts the same unchanged Greywatch dungeon. Earlier snapshots and
saves remain available; they do not automatically acquire the new layout. This snapshot copies the executable and
content and shares original artwork. `/tmp` is temporary; the checked archive under `dist/` is the durable deliverable.

## What changed

- Same 24 house/service doors, 23 physical structures, 10 forms and all existing event/house IDs. Door sizes, facade
  textures, house dimensions and the joined Smiths Row roof are retained. Houses are translated/turned to face streets.
- Houses now share main, upper civic and lower residential streets. Opposing main-street fronts replace widely separated
  individual plots. The temple keeps a larger forecourt; the well occupies a side pocket at `(-10240,2560,672)`.
- The house-envelope footprint shrinks from 214,912,256 to 91,985,920 square units (**57% smaller**). Median nearest
  envelope gap drops from **1,866 to 832 units (55%)**, and coverage rises from **8.9% to 20.8%**. Ravenshore market's
  measured gap is 608 and coverage 30.1%; this is a smaller village interpretation, not a copy of its city blocks.
- The broad town terrain pad is reduced, with nearer northern/southern shoulders. House pads remain grounded on the
  quantized terrain, and the civic edge rises modestly. Existing river, bridge, dungeon sites and regional approaches remain.
- Road dirt margins are narrower, restoring grass between building groups. Gardens, stable supplies, guards and villagers
  are repositioned for the closer layout. Counts remain 563 decorations, 29 town actors and 14 distant ogres.
- The native ODM and its automap, Blender source, semantic data, town registry, Lua assembly and content archive are rebuilt.

## Evidence and scope

[Reference measurements and reusable instructions](../../SETTLEMENT_DENSITY.md) include district membership, source
hashes, measurement limitations, Ravenshore lane/market comparisons, and Garrote Gorge's village versus walled courtyard.
The compound does have stone paths within its larger dirt yard; its keep/walls provide enclosure.

![Native game street view](review/gameplay/density_main_street.png)

The main road now has close facades on both sides. This is an ordinary game capture at party eye height with no camera
zoom comparison implied. The native Blender reimport below shows the entire street arrangement, gardens and well pocket.
Its lighting is for geometry inspection. The arrangement remains more regular than Ravenshore's market; further street
character can be tuned in specific blocks without enlarging the approved house kit.

![Written ODM overview](review/brackenford_native_density_town.png)

[Same-scale comparison](review/density_revision/matched_scale_comparison.png), [after plan](review/density_revision/brackenford_after.png),
[measurements](review/density_revision/measurements.json), and [quick check](review/density_revision/quick_check.json).
The baseline native map, semantic data, Blender file, plan and placement scripts are preserved in
`review/density_revision/before/`. The earlier facade baseline remains separate.

Verification: the native writer readback matched terrain arrays, 75 BModels/2,596 faces, actor/decor records and face events.
A 0.06-second static check verified 24 door bindings and dimensions, registry positions, texture keys, arrival identities,
well clearance, house/road-center corridors and initial town-actor footprints. Native tile cells include dirt margins:
a terminal doorstep tile may share its dirt margin with a foundation; the checked road-center walking corridor is
256 units wide. This is a placement check, not a claim of exhaustive collision routing. No service/travel/combat scenario
suite was run. The two fresh God starts are created and reloaded by the snapshot installer.

Outdoor native SHA256: `942c7de0c83741dbc922070dad0348141aedd3764fe3b72783e36f60d23f7da9`.
Unchanged indoor SHA256: `b227608891142f1982f2cd6039124eaab2310775b6760760a8570baff8679fec`.
Archive SHA256: `7a73ffa91630fa4f1c775df474fb1598c6a8eda6c29f503d5520040179b70ba5`.

## Reproduce

Use the current authoring/build sequence in [REBUILD.md](REBUILD.md); regenerate `build_town_content.py` after Blender
moves the doors, and stage again after rebuilding the native automap. For this revision's final checks and packaging:

```sh
python3 level_generation/scripts/measure_settlement_density.py
python3 level_generation/projects/brackenford_greywatch/check_facade_revision.py --review-directory density_revision
python3 level_generation/projects/brackenford_greywatch/stage_runtime.py
python3 level_generation/projects/brackenford_greywatch/content_package.py
python3 level_generation/projects/brackenford_greywatch/prepare_playtest.py \
  --package level_generation/projects/brackenford_greywatch/dist/brackenford_greywatch_content.zip \
  --directory /tmp/openyamm-brackenford-playtest-density-new \
  --god-source-save /tmp/openyamm-brackenford-playtest-final/god_seed_work/saves/quicksave.oysav
```

Choose an unused snapshot directory. The God seed must predate visits to either generated map so stale map state is not
carried into the new layout. Preserve the connected Blender session's prior active scene around authoring/review calls.

## Later composition revision

The driver accepted this spacing and then supplied an irregular street sketch. [SKETCH_REVISION.md](SKETCH_REVISION.md)
replaces the parallel grid and adds raised sites, a fountain and four stat barrels; this density snapshot remains available.
