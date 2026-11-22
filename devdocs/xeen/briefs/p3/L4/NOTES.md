# P3 Plane of Earth of Xeen: L4 (installed in assets_dev)

A6's planes sub-agent, seventeenth session, 2026-11-21. The L1 is `../L1/` with D-58 applied (`devdocs/xeen/briefs/d7/L1/D58_DECISION.md`); L2-L4 are written by `output/studio_cal/p3/tools/gen.py` (rooms, objects, wiring, plan, project, atmosphere), the playtests by `tools/gen_playtests.py` from the build, this file and `output/studio_cal/p3/measure.json` by `tools/notes.py`. Scripts: `v.sh` (generate, validate), `b.sh` (build, playtests, install into the scratch root, audit), `run.sh` (playtests through the lane's game slots; `tools/check_scree.py`), `stage_install.sh` (install).

Installed in assets_dev on 2026-11-21 at 07:41 by `INSTALL=1 stage_install.sh` (stage audit 0 errors 0 warnings, the seven playtests 14 of 14 in the stage, `output/studio_cal/a6/s20/stage_p3.log`), then 14 of 14 again from assets_dev (session 20, S's pieces).

## What was built

- **room:bowl**: one open-air room (sky `xeen_plane_earth`, MOUNTAIN), its floor the scree at -1024 (`vlcflore` rubble), its walls raw rock to the sky: 61 corners (the studio's limit is 64), the longest wall 1,176, `ceiling_points` on every corner and up to three more on each wall (90 skyline points, 156 in all), jagged tops 2,200-3,000 over the scree; three shipped rocks by stretch (`cwb1`, `gcav1wal`, `gwspotwl`), the spurs `vlcflorb` strata.
- **The walls lean in** (D-58 P3): 12 hanging slabs high on the longer walls, each a plane whose underside rises from the wall at 1.6-1.9 for each unit to a bulging ragged lip 360-560 out over the bowl, 280 under the skyline; 8 spurs as teeth of the outline; 103 steep talus wedges (1.15-1.85: the party slides back) at the walls' foot and round every terrace and the Anvil (none round the Hollow, the stair, the links or the slopes), so nothing stands as an extruded plate.
- **The terraces**: L1's outlines as rock prisms from the scree (the bowl reads deep: the scree 1,024 under the arrival, the Hollow 768); the links ridges of rock; the Giants' Arch (link:arch_e) seven slabs, thick at its feet, thin at its crown, the scree under it walkable; 8 scree slopes (0.62 for each unit, walkable; 448 wide) from the scree up to every terrace, none to the Anvil or the Hollow (D-58 P3 Q1).
- **The Anvil** (-384): bedrock (`gn_mtl03`), a jagged crack of black strata at its middle where the guardians (11722 and two 11721) wait hidden in group 60, a ring of tapering monoliths (`gwspotwl`) with the east gate and the stair's head open; the test's plate before S's pedestal.
- **The Root Stair**: twelve steps of 32 down to the Hollow between cheeks of rock 128 thick whose tops stand level at -128 (256 over the Anvil, 288 or more over every step, 896 over the scree), two monoliths flanking its head; across the head `mover:slab`, a block of bedrock 384 high that sinks 388 into the rock on qbit 111766 (L1: 'a slab of stone across its head sinks on the test').
- **The Sleeper's Hollow** (-768, `cfb1`): under the south wall's overhang (a hanging slab whose underside rises from 880 over the floor at the wall), nine roots of stone hanging from it; the return dais a disc of grey granite (`gn_mtl01`) shown on qbit 111762; the test's chest.
- **The Pillar Field**: petrified trees (a flaring root foot, a trunk tapering to a broken top, some with a knot; `gcav1wal`), the Echo Stone a hollow pillar with a sapphire vein (`xdvsaph`, once). **The Geode Hall**: split boulders, their split faces amethyst (`xpegeode`), the Heart-geode the largest. **The Giants' Quarry**: cut steps, half-cut blocks, the last block with its slate, the quarrymen's hut fallen to its footings by their strongbox. **The Dust Ledge**: packed earth, the dust shaft's foot a disc of pale stone in a ring of standing stones. **The Stone Statue**: an ashlar plinth (S's statue stands on it).
- **Rockfall**: nine PressurePlate platforms (`xperubble`, 192 x 192) at L1's cells, none on the walk, each calling A3's `planes.rockfall` (one time in three, 50 physical, a short camera shake).

## Wiring (A3's hooks by name)

- `evt:test` (step, the test's plate): 'Accept the test of Earth?' Yes: `m38.test_earth`, show group 60, map_var test_accepted. Not asked while test_accepted or qbit 111766 is set.
- `evt:test_check` (every 1 s while accepted and not passed): `Xeen.planeTestCheck("earth", 60)` (runs `m38.test_earth_passed` once the three are dead: qbit 111766).
- `evt:gate_open` (once, with its line), `evt:gate_keep` (every 1 s once the qbit is set: the slab came back shut after a reload without it) and `evt:passed_load` (load, P-1: the slab sunk, group 60 hidden). `evt:gate`: the slab never moves by hand.
- `evt:dais_hide` (load: the dais hidden and passable until qbit 111762), `evt:dais` ('Step onto the dais and return to the Skyroads?', `leave: exit:d7_dais`, locked text until 111762), `evt:way_up` ('Rise with the dust to the Skyroads?', `leave: exit:d7_way_up`): both to D7's `entrance:p3_return` (C5).
- `evt:rockfall` (`planes.rockfall`), `evt:geode`/`evt:geode2` (`planes.geode`, both halves), `evt:echo` (`planes.echo`), `evt:last_block` (`planes.last_block`), `evt:plaque` on the plinth (`m38.plaque_earth`), the two chests (treasure 6; the quarry cache trapped, level 8).

## Figures (`output/studio_cal/p3/measure.json`)

| Figure | Target | L4 |
| --- | --- | --- |
| Monsters | 30 (27 + the test's 3) | **30** (3 hidden) |
| Kill XP per member | D-58 32.04k | **32.04k** |
| POIs (L1 census) | C8 10-12 | 10 (S's statue, sleeper and couch, pedestal and dais placed, session 20, on the plinth, plate and dais disc) |
| Chests | 2 at treasure 6 | 2 (the test's chest in the Hollow; the trapped quarry cache) and the last block's find (2 Earth Resistance, 259); the Echo Stone's sapphire is A3's |
| P-2 lips | at least 192 | **256** (the Hollow over the scree on every side); the stair's cheeks 256 over the Anvil, 288+ over the steps, 896 over the scree; the slab 384 over the Anvil; the stair's foot 256 over the scree; no higher floor within the drop reach (L1) |
| First fight from the arrival | 1,500-4,000 | 2,859 (pop:statue_west) |
| Walkable area | 44-51 M (C1) | 54.0 M units on the terraces, links, stair and slopes; the scree 69.3 M more (49 % of the bowl's 140.4 M) |
| Scree to a way up | - | at most 5,293 to a scree slope's foot, 90 % within 2,549 |
| Build | 0 warnings | 2 sectors, 2,172 faces (3,980 triangles), 2,658 vertices, 1 door record (the slab), 23 events, 2 chests, 0 lights |
| Textures | Dungeon S cap 30, 4 new | 17 distinct (the chests' own pictures aside), 2 new (`xperubble`, `xpegeode`) |
| Audit | 0 errors | 0 errors, 0 warnings; info: `gcav1wal` and `vlcflora` squashed on the steep tops of the leans and talus (meant, `uneven`) |

## Playtests (headless, `run.sh`, N=2; log `tests_r1.log`)

- `playtest.yml`: the walk: arrival, the statue's terrace, the Pillar Field, the Anvil; the slab holds: **2 of 2**.
- `playtest_hostility.yml`: 27 hostiles placed and hostile, the three guardians hidden, a quiet arrival: **2 of 2**.
- `playtest_test.yml`: the test: Yes raises the guardians, their deaths set 111766 and sink the slab, down the Root Stair into the Hollow; after a save and reload the slab sunk, the guardians dead: **2 of 2**.
- `playtest_bypass.yml`: P-2: into the slab; along both cheeks from the Anvil (off the rim into the scree); from the scree at the Hollow's west, east and north lips and at both cheeks: always the scree, never the stair or the Hollow: **2 of 2**.
- `playtest_scree.yml`: a drop off the statue's terrace is a real fall (140 HP each -> [21, 88, 67, 91]); the statue's scree slope leads back up: **2 of 2**.

## Tour

`output/studio_cal/p3/pics/contact_t3.png` (shots in `pics/t3/`, `tour3.yml`, `tour.sh`; under a bridge, the Hollow from the Anvil and the south scree in `contact_t4.png`): the arrival, the Dust Ledge from above, the statue's terrace, the Pillar Field, the Anvil from its east gate, the slab, the Root Stair, the Hollow and its overhang, the Geode Hall, the quarry, the scree under the south wall, the bowl from above. Before the look fixes: `contact_t1.png`, `contact_t2.png` (before the bridges). The sky preset resolves under the open-air BLV (brown dust, no sun).

## Deviations from L1 (each one line)

- The gate is the slab L1 names (a sinking mover), not a hinged pair: the Root Stair has no wall for leaves, and L1 says 'a slab of stone across its head sinks'.
- The Anvil's ring is ten monoliths plus the stair's two flanking ones (the east gate open).
- The terraces stand ~300 off the bowl's wall (the rim keeps 300 clear of every footprint): a narrow drop to the scree behind them.
- The way-up disc moved in to (-4710, 4736) (L1 (-4864, 4864) is near the ledge's edge).

## S's pieces (twentieth session, 2026-11-21)

- The Earth Sleeper on his couch (`xeen_sleeper_earth`, row radius 290): clicked, A3's `m38.sleeper_earth` (its three answers; awake sets the qbit, the award and 10,500 experience).
- The statue on A6's plinth (`m38.plaque_earth` on the plinth and on the statue); the test's pedestal 208 from its plate's centre, facing it.
- The return dais: S's disc on the studio disc's top, both hidden until the sleeper wakes; the dais rises the second the qbit is set (`evt:dais_show`, a 1-s timer) and on every load after (`evt:dais_load`); clicked on either, the dais's question and D7's return.
- Every binding turns by `yaw_offset` -90 (`facing` is where the front looks; the sleeper's head on the viewer's left). New playtest `playtest_sleeper` (the three answers, the dais hidden then shown, kept over a reload, Yes to D7).
- `m38.sleeper_earth` on `xeen_sleeper_earth` sets 111762 (the playtest wakes him); S's dust shaft on the way-up disc asks like it (`evt:way_up_column`).

## Blocked (no stand-ins)

- None of S's pieces.
- **The elementals' look**: S's tier skins and bindings (D-47/C6).

## Dressing exceptions

None: no props. The monoliths, trees, boulders, quarry blocks, hut footings, talus, leans, roots and the stair's cheeks are terrain, off every walking line.

## S32 (2026-11-22, A6 32nd session)

Rebuilt and installed 01:36-01:39 (merge point 41): the way up, its column, the dais and its disc move into D7 through the standard entrance window (no Yes/No: F16, `planes/pieces.py d7_return_lua`); MAW reserve rewritten; stage tests all pass (sleeper and daily lines are status lines since D-90). The plate tops still show their picture 1.5x (18 audit errors, a studio fault: A1).

## S33 (2026-11-22, A6 33rd session: merge point 42)

The plates' `top_surface` is `{texture: xperubble, size: [128, 128], fit: true}` (`size` is the picture's own size, 128;
`fit` lays it once over the 192 plate, and since merge point 42 once over its underside too). Rebuilt and installed
~02:00 through the stage (all stage tests pass); the 18 `textures.feature_repeated` errors are gone: the assets_dev
audit is 0 errors, 0 warnings. MAW reserve rewritten, `xeen_balance.py --check` passes.
