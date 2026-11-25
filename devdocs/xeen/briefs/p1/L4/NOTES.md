# P1 Plane of Fire of Xeen: L4 (installed in assets_dev; the look pass of 2026-11-21)

A6's planes sub-agent, sixteenth session, 2026-11-21. The L1 is `../L1/` with D-58 applied (`devdocs/xeen/briefs/d7/L1/D58_DECISION.md`); L2-L4 are written by `output/studio_cal/p1/tools/gen.py` (rooms, objects, wiring, plan, project, atmosphere), the playtests by `tools/gen_playtests.py` from the build, this file and `output/studio_cal/p1/measure.json` by `tools/notes.py`. Scripts: `v.sh` (generate, validate), `b.sh` (build, playtests, install into the scratch root, audit), `run.sh` (playtests through the lane's game slots), `stage_install.sh` (the lead's install).

Installed in assets_dev on 2026-11-21 at 04:44 (the look pass), 06:02 (the way up asks) and 07:42 (S's pieces, session 20: stage audit 0/0, the eight playtests 16 of 16 in the stage, `output/studio_cal/a6/s20/stage_p1.log`, then 16 of 16 from assets_dev). Session 25: S's Ember Font, burnt camp and the font's light installed 09:46:56 (stage 18 of 18 with the daily test, from assets_dev 18 of 18, audit 0/0) (`output/studio_cal/a6/s25/`).

## What was built

- **room:crater**: one open-air room (sky `plane_fire`), its floor the lava lake at -40 (`lavtyl`, the floor's `lava` kind: it burns), its walls ragged cliffs to the sky (the look pass below). The shelves are L1's outlines standing in the lava, skirted with crust; the floor-0 ground (the Cinder Shelf, the Vent Field) is a bank, 40 over the lava (D-58 Q1: within 64); every raised shelf has ramps (11 in all) whose feet stand 32 over the lava; the causeways are crust wedges.
- **The Crucible** on its rise (256): a ring of black glass (`xpfglass`) round the pit, a pool of lava 24 under the glass (burning); the test's plate at its south gate (before S's pedestal); the guardians (11623 and two 11622) the hidden group 60 in the pit.
- **room:hall**, the Sleeper's Hall (floor 384): its own open-air room behind the crater's wall, walls to the sky on every side; the only way in is `open:gate`, a hinged pair of black-glass leaves (`door:sleeper`, two leaves, the right mirrored) at the end of the obsidian bridge from the Crucible.
- **Vents**: nine PressurePlate platforms (`xpfvent`, 192 x 192) at L1's cells, none on the walk, each calling A3's `planes.vent` (one time in three, 50 fire).
- **The Basalt Spires**: basalt columns; the tallest's red seam (`xdvruby`) calls `planes.spire`.

## The look pass (2026-11-21, the lead's review of contact_t1: D-58 P-4)

- **Cliffs**: the rim is 64 corners (the studio's limit on an outline is 64), each with its own inset (no long straight runs: the longest rim wall 1,216); the sky is `ceiling_points` on every corner and up to three more on each wall between (92 skyline points, 147 in all with a near ring and a ring at 2,960 over the middle), and the walls end on that line: jagged tops 1,400-2,800 over the lava, the hall's notch the tallest (2,800). The generator emulates the studio's ceiling triangulation (shortest lines first) and drops the points that would make a sliver steeper than a ceiling may be. Three shipped rock faces by stretch of the rim: `vlcwl1` (lava seams), `gcav2wal` (MM8 Plane of Fire's black strata), `vlcwl3a`; the spurs `vlcwl2` (basalt columns).
- **Spurs and ledges**: 8 spurs as teeth of the outline reaching 400-960 into the lava, their noses 400-700 lower than their flanks (ridges running down); 5 stepped ledges (a block tapering back, a jagged-topped ledge on it jutting past its front: leaning in and out; the tapered blocks are turned to Pythagorean directions so their leaning faces keep whole-unit corners), 2 rock needles before them; the cliffs' batter at their foot (below, session 28-29), so no wall rises from the lava as a flat slab.
- **Lava falls**: 2 gullies cut 448 into the cliff, the back wall molten `orfyrlga` flowing down from a lip 600-700 under the gully's flanks, a glowing pool (`orfyrlga` drawn as a picture, burning by its `floors` entry) filling the gully's mouth, ringed with crust boulders. Lane S's `xeen_lavafall` is bound for outdoor maps only (no indoor binding), so the falls are geometry.
- **The Sleeper's Gate**: framed on the crater's side: black-glass jambs (176 x 160) from the lava to 1,056, a basalt lintel over the doorway (its underside glass), a rough gable of glass over it (two wedges to 1,472) and two tapering obsidian shards beside it (to 1,560); the hinged pair, qbit 111764 and the P-2 walls unchanged.
- **Shelves and causeways**: 94 crust skirts on their sides (steep, 1.15-1.75, `steep_floor`: the party slides back into the lava; the floor-0 banks' skirts walkable), each edge its own run, so the outlines are broken and no side reads as an extruded plate. Steep skirts' crust is drawn out down the slope (`uneven`).
- Rock over the lava: 13.2 M units; the hall's sky raised to 2,760 (the notch's corners).

## Wiring (A3's hooks by name)

- `evt:test` (step, the test's plate): 'Accept the test of Fire?' Yes: `m38.test_fire`, show group 60, map_var test_accepted. Not asked while test_accepted or qbit 111764 is set.
- `evt:test_check` (every 1 s while accepted and not passed): `Xeen.planeTestCheck("fire", 60)` (A3; runs `m38.test_fire_passed` once the three are dead: qbit 111764 and its line).
- `evt:gate_open` (every 1 s once the qbit is set) and `evt:passed_load` (load, P-1): open the gate; the load event also hides group 60 (the pit quiet). `evt:gate`: the leaves never move by hand.
- `evt:vents`, `evt:spire`, the two chests (treasure 6; the ember cache trapped, level 8).
- `evt:way_up` (the heat column's fissure in the cliff at the Cinder Shelf): **sealed** with a line until xeen_d7.blv is installed and lists entrance:p1_return (`P1_D7_LIVE`, D4's pattern); then the `exit` preset (D-24) with A3's `m38.way_up_fire` as its meaning.

## Figures (`output/studio_cal/p1/measure.json`)

| Figure | Target | L4 |
| --- | --- | --- |
| Monsters | 30 (27 + the test's 3) | **30** (3 hidden) |
| Kill XP per member | D-58 31.54k | **31.54k** |
| POIs (L1 census) | C8 10-12 | 10 (S's statue, sleeper, pedestal and dais placed, session 20; the Ember Font and the burnt camp, session 25) |
| Chests | 2 at treasure 6 | 2 (the test's chest in the hall; the trapped ember cache) and the camp's find (2 Fire Resistance, 256) |
| P-2 lips | at least 192 | the hall's walls 2,800 over the lava and 2,376 over its floor (to the sky); the gate's sill 424 over the lava; no floor higher than the hall's (the Crucible 258) |
| First fight from the arrival | 1,500-4,000 | 2,585 (pop:statue_lesser) |
| Walkable area | 44-51 M (C1) | 52.9 M units (crater 127.0 M) |
| Lava | the element's ground | 66.2 M, 52 % of the crater; to the nearest way out (a floor-0 bank or a ramp's foot) at most 3,127, 90 % within 1,815 |
| Build | - | 3 sectors, 2538 faces, 3249 vertices, 1 portal, 2 door records, 20 events (no triangle count from the build; faces are convex polygons) |
| Audit | 0 errors | 0 errors, 0 warnings; info: `gcav2flr` squashed on the steep skirts (meant, `uneven`), `vlcwl3a` on 2 faces (the seam's ends), `p1_spire` set by A3's hook Lua and read there |

## Playtests (headless, the scratch root, `run.sh`, N=2)

- `playtest.yml`: the walk: arrival, the statue's spot, the islet, the Crucible, the bridge; the gate shut: **2 of 2**.
- `playtest_hostility.yml`: 27 hostiles placed and hostile, the three guardians hidden, a quiet arrival: **2 of 2**.
- `playtest_lava.yml`: standing on lavtyl the HP drops, on the crust it does not; out of the lava onto a floor-0 shelf: **2 of 2**.
- `playtest_test.yml`: the test: Yes raises the guardians, their deaths set 111764 and open the gate, into the hall; after a save and reload the gate open, the guardians dead: **2 of 2**.
- `playtest_bypass.yml`: P-2: a party in the lava pushed west into the hall's east wall (north of the gate's frame) and north into its south wall stays in the lava: **2 of 2**.

Logs: `output/studio_cal/p1/xrun/` (the N=2 run named in `tests_look.log`; before the look pass `tests_n2.log`).

## Tour

`output/studio_cal/p1/pics/contact_t2.png` (shots in `pics/t2/`, `tour2.yml`, `tour.sh`): the arrival, the Crucible, the gate's frame, the crater from above, the Glass Shelf's fall in its gully, the Vent Field, the north-east fall, the south cliffs. Before the look pass: `contact_t1.png`.

## Deviations from L1 (each one line)

- Lava at -40, not -64: the floor-0 shelves are then a step (the engine's step is 50) out of the lava.
- The gate stands in the Sleeper's Hall's wall at the bridge's far end, not at the Crucible's west rim: a door needs a wall, and the hall as its own room makes P-2 hold by construction.
- The Glass Shelf's top is `xpfglass` (L1: black glass); the vents' plates stand 4 over their shelf.
- The spire's gem device keeps its one-time gem (A3's planes.spire); C8's 'one find' is the camp.

## S's pieces (twentieth session, 2026-11-21)

- The Fire Sleeper on his couch (`xeen_sleeper_fire`, row radius 290): clicked, A3's `m38.sleeper_fire` (its three answers; awake sets the qbit, the award and 10,500 experience).
- The statue on its own black plinth, its plaque `m38.plaque_fire` clicked on the decoration (radius 224); the test's pedestal 208 from its plate's centre, facing it.
- The return dais: S's disc on the studio disc's top, both hidden until the sleeper wakes; the dais rises the second the qbit is set (`evt:dais_show`, a 1-s timer) and on every load after (`evt:dais_load`); clicked on either, the dais's question and D7's return.
- Every binding turns by `yaw_offset` -90 (`facing` is where the front looks; the sleeper's head on the viewer's left). New playtest `playtest_sleeper` (the three answers, the dais hidden then shown, kept over a reload, Yes to D7).
- P1 had no dais: `platform:dais` (black glass, 224, 8 high) added in the Sleeper's Hall at L1's exit:dais (-4864, 3904), as on P2-P4, its exit to D7's `entrance:p1_return` (A3's `m38.dais_fire`).
- S's heat column at the foot of the molten sheet's middle (on the lava, 4 off the wall, facing out); it asks like the sheet (`evt:way_up_column`). The walk now stops before the statue (solid) and reads Step One.
- The studio's `liquid and flow` warning now counts the three decorations in the lava room (224 wanted, 3 not found: the map's 221 liquid faces all found, as before): A1.

## The Ember Font and the burnt camp (session 25)

- S's `xeen_emberfont` (row 4056, radius 90, solid) on the islet at (-1152, -448), z 96, facing 0; clicked, `evt:font`: A3's `planes.font` (once a day for the party, +20 Fire resistance until rest; `playtest_daily.yml`, written by `output/studio_cal/a6/s25/gen_daily.py`).
- S's `xeen_firecamp` (row 4057, radius 0: walked over) at (-3968, -4736), z 0, facing 90; clicked, `evt:camp`: A3's `planes.camp` (the note). The find (2 Fire Resistance) lies by the bedroll; the ember cache 870 north-west.
- `light:font`: a warm pulsing light 200 over the islet at the font (radius 720-800, [255, 120, 40]); S's pieces carry no light. A scene light: the build counts 0 light records.

## The batter and the way up's vent (sessions 28-29, G3 review rows 57 and 34)

- **Batter** (`gen.py` `batter()`, replacing the scree wedges): along every plain rim wall, pieces 420-760 long, each a stack of rock tiers rising toward the wall: 49 scree feet (480-900 up the wall, at most half the wall there, slopes 1.15-1.5, crust tops), 45 ledges with an upright face and a top leaning back, 11 steps higher and narrower again; every piece its own depth, heights and front line. 10 ribs of basalt columns (`vlcwl2`) stand at joints and climb most of the way up. Each tier's back stands its own distance off the wall (ledge 2, rib 9, feet 16 and 23 in turn, step 30) and the ledges and steps stand from the lava, so no faces share a plane and nothing rests on nothing (session 29).
- **The way up's vent** (`way_up_vent()`, row 34: the heat shimmer was lost against the lava): a disc of molten rock (`orfyrlga`, burning by `floors`) at the heat column's foot in a low lip of black glass (16-32 over the disc), two obsidian shards either side of the fissure's mouth, seen across the crater, and `light:way_up` (pulsing, radius 960-1,100).
- Installed 17:23 (stage 18 of 18 runs, N=2); from assets_dev 9 of 9; audit (`--dressing`) 0 errors, 0 warnings, faces in one plane 0. Before/after `output/studio_cal/a6/s29/p1/sheet_p1_before_after.jpg`.

## Blocked (no stand-ins)

- None. The elementals' look (checked in game, session 30, `output/studio_cal/a6/s30/p1/sheet.jpg`): the fire elementals (11620-11623) draw on S's `xeen_fie1` flame body (MM6's fie1, skins fie1_a/b/c, the Guardian's xfie_d), the Lava Golems (11593) on their golem model; every actor textured, none a placeholder (the session-21 line read the gold-cored flames as placeholders).

## Dressing exceptions

None: no props. The basalt columns, spurs, ledges, needles, scree, skirts, the falls' boulders and the gate's frame are terrain, off every walking line (the skirts lie beside the causeways and ramps, never on them).

## S32 (2026-11-22, A6 32nd session)

Rebuilt and installed 01:36-01:39 (merge point 41): the way up, its column, the dais and its disc move into D7 through the standard entrance window (no Yes/No: F16, `planes/pieces.py d7_return_lua`); MAW reserve rewritten; stage tests all pass (sleeper and daily lines are status lines since D-90). The plate tops still show their picture 1.5x (18 audit errors, a studio fault: A1).

## S33 (2026-11-22, A6 33rd session: merge point 42)

The plates' `top_surface` is `{texture: xpfvent, size: [128, 128], fit: true}` (`size` is the picture's own size, 128;
`fit` lays it once over the 192 plate, and since merge point 42 once over its underside too). Rebuilt and installed
~02:00 through the stage (all stage tests pass); the 18 `textures.feature_repeated` errors are gone: the assets_dev
audit is 0 errors, 0 warnings. MAW reserve rewritten, `xeen_balance.py --check` passes.

## 2026-11-25, xeen-fb4-dungeon6: the test plate's lid

The "254 glass face" (dungeon5's last `floor.lid` on P1) was the test plate's own bottom: the plate straddles the
Crucible's halves (east top z 256, west z + 2) and was sunk SINK under the west half's top, so its bottom lay 2 under
the east half's. `gen.py` `crucible()`: base z - SINK (its top unchanged). `floor.lid` 3 -> 2 (the gate's lintel and
gables, out of reach); 9/9 playtests; installed, MAW reserve.
