# P4 Plane of Water of Xeen: L4

A6's planes sub-agent, seventeenth session, 2026-11-21. The L1 is `../L1/` with D-58 applied (`devdocs/xeen/briefs/d7/L1/D58_DECISION.md`); L2-L4 are written by `output/studio_cal/p4/tools/gen.py` (rooms, objects, wiring, plan, project, atmosphere), the playtests by `tools/gen_playtests.py` from the build, this file and `output/studio_cal/p4/measure.json` by `tools/notes.py`. Scripts: `v.sh` (generate, validate), `b.sh` (build, playtests, install into the scratch root, audit), `run.sh` (playtests through the lane's game slots), `tour.sh`, `stage_install.sh`.

Installed in assets_dev on 2026-11-21 at 07:45 by `INSTALL=1 stage_install.sh` (session 20, S's pieces: stage audit 0/0, the eight playtests 16 of 16 in the stage, `output/studio_cal/a6/s20/stage_p4.log`; then 16 of 16 from assets_dev).

## What was built

- **room:sea**: one open-air room (sky preset `xeen_plane_water`), its floor the sea bed at -1024, walls and ceiling (4096) sky faces. The sea's surface is one untouchable `7wtrtyl` face at -64; under it MM9 water volumes (objects.yml `water`): `water:sea` (the inner sea, no current) and four edge bands 1024 wide past the ring of sea stacks, each a constant inward current of 256 (D-58; no radial current); `water:hold`, the wreck's hold, 40 deep (waded).
- **Terraces** (the six L1 spaces): the L1 outline with a ragged rim, marble (`gtempw1`) out of the sea with a flagstone top (`gtempflr`; the Coral Garden `xpwcoral`), on a wider foot of rough rock (`gwspotwl`) whose top is a ledge 248 under the surface, below a swimmer's feet. Broken wall stubs on the rims (brick `cdb` round the wreck, coral rock round the garden), off every walking line.
- **Colonnades** (the seven L1 links): marble slabs from the bed, broken columns along both edges (some intact with capitals).
- **Steps out of the water**: 10 flights of 32 (down to -288): at the middle of every colonnade but the Veil's and at one rim of every terrace but the Whirlpool Court and the Grotto (L1, P-2). A swimmer at the surface (feet -197) steps onto the flight and walks out (playtest_stepout).
- **The Whirlpool Court**: the whirlpool (a `7wtrtyl` disc, where the hidden guardians stand), a ring of eight mosaic slabs (`gtemprf`, once per face), a ring of broken columns, the test's floor at the east gate (S's pedestal beside it, blocked).
- **The Veil** (gate:sleeper): a falling sheet of water (`xcwisp`, translucent, flowing down) across the head of the Grotto's colonnade, solid until qbit 111767, then passable and hidden; either side broken wall stubs 384-496 over the court, 1088 along the colonnade's head (P2's curtain route; L1 has no gate leaves, so no double door).
- **The Sleeper's Grotto** (192): a raised shelf of shell and stone (the couch's place, S's, blocked), a sea arch (two rock piers outside the rim and a hanging span), the return dais (hidden and passable until qbit 111763), the test's chest.
- **The Wreck**: a hull of MM8's ship planks (`bwoodb1`) across the south court; a breach on its north-east side with a sill of 56 (a step each side) keeps the hold's water in; the hold is half flooded (40, waded: D-58 Q2, no diving); a stern deck (`bmplnk`, 96) with the ship's log (`planes.log`) and its find (two Water Resistance, 258); a broken mast on the deck, a stump amidships, a fallen mast outside; the trapped strongbox in the hold.
- **The Sea Statue's forecourt**: the fountain basin in the middle of the forecourt (D-58 correction), its water and the plinth (`m38.plaque_water`; S's statue on it, blocked); the Drowned Bell's fallen frame (`planes.bell`; S's bell, blocked).
- **The Coral Garden**: the Tide Pool in a ring of coral rock (`planes.tide_pool`, the buff device).
- **The waterspout** (the way up): a translucent column of water flowing up from a basin at the Spray Terrace's corner; clicked, 'Ride the spout back to the Skyroads?' -> `leave: exit:d7_way_up` (D7 is installed and lists `entrance:p4_return`).
- **Waves**: 9 PressurePlate platforms (`xpwspray`, 192 x 192) at L1's cells, none on the critical path, all calling `planes.wave`.
- **Sea stacks**: tapered rock stacks (two tiers, Pythagorean facings) in a ring near the room's edge with gaps, three broken arches.

## Wiring (A3's hooks by name)

- `evt:test` (step, the test's plate): 'Accept the test of Water?' Yes: `m38.test_water`, show group 60, map variable test_accepted. `evt:test_check` (1 s): `Xeen.planeTestCheck("water", 60)`. `evt:gate_open` (1 s once 111767 is set) and `evt:passed_load` (load, P-1): the Veil passable and hidden, the guardians hidden. `evt:gate`: the Veil clicked.
- `evt:dais_hide` (load, until 111763) and `evt:dais` ('Step onto the dais and return to the Skyroads?', `leave: exit:d7_dais`, locked text before the sleeper); `evt:way_up` (always open).
- `evt:wave` (nine plates), `evt:bell`, `evt:tide_pool`, `evt:log`, `evt:plaque`, the two chests.

## Figures (`output/studio_cal/p4/measure.json`)

| Figure | Target | L4 |
| --- | --- | --- |
| Monsters | 30 (27 + the test's 3) | **30** (3 hidden; 5 Great Octopods swimming) |
| Kill XP per member | D-58 32.38k | **32.38k** |
| POIs (L1 census) | C8 10-12 | 10 (S's statue, sleeper and couch, pedestal, dais and bell placed, session 20) |
| Chests | 2 at treasure 6 | 2 (the test's chest in the Grotto; the trapped strongbox in the hold) and the log's find (2 x Water Resistance) |
| P-2 lips | at least 192 | **216**: the Veil's colonnade 216 over the sea at its lowest (just beyond the flank stubs), the Grotto 256 over the sea, the flank stubs 384 over the court; a surface jump clears about 55 |
| First fight from the arrival | 1,500-4,000 | 3,371 (row 11625) |
| Octopod homes | >= 1,024 from the arrival terrace, the court, the Grotto | landing 3,906, arena 2,586, chamber 5,650 |
| Walkable area | 44-51 M (C1) | 41.6 M units; the sea 122.3 M (69 % of the room) |
| Build | - | 2 sectors, 2451 faces, 3732 vertices, 21 events, 2 chests, 0 lights; about 6,372 triangles (estimate from the shapes) |
| Textures | Dungeon S, cap 30, at most 4 new | 13 distinct (7wtrtyl, bmplnk, bwooda1, bwoodb1, gtempflr, gtemprf, gtempw1, gwspinwl, gwspotwl, xccloud, xcwisp, xpwcoral, xpwspray); new `xpwspray`, `xpwcoral` (xpwhull not made: shipped `bwoodb1`) |
| Audit | 0 errors | 0 errors, 0 warnings; info: map variables p4_bell and p4_pool set by A3's hook Lua and read there |

## Playtests (headless, `run.sh`, N=2; `tests_n2.log`)

- `playtest.yml`: arrival, the colonnades, the forecourt, the court; the Veil holds before the test: **2 of 2**.
- `playtest_hostility.yml`: 27 hostile, the test's three hidden, a quiet arrival: **2 of 2**.
- `playtest_test.yml`: Yes raises the guardians; killed (damage_actor) they set 111767; the Veil stills; into the Grotto; a reload keeps it: **2 of 2**.
- `playtest_bypass.yml`: P-2: the Veil holds; off the court into the sea; from the sea against the Veil's colonnade (both sides) and the Grotto's rim (three sides) the party stays in the water: **2 of 2**.
- `playtest_swim.yml`: 20 s at the surface: still at the surface, breath full, no drowning tick: **2 of 2**.
- `playtest_current.yml`: the east band carries a swimmer inward to the band's inner edge (x 5,630): **2 of 2**.
- `playtest_stepout.yml`: a swimmer climbs the Spray Terrace's flight out of the sea: dry, on the terrace: **2 of 2**.

## Tour

`output/studio_cal/p4/pics/contact_t1.png` (shots in `pics/t1/`, `tour1.yml`, `tour.sh`): the arrival, an overview, the north-east colonnade, the forecourt's fountain, the Tide Pool, the wreck, the court from its east gate, the Veil before and after the test, the Veil's colonnade, the Grotto, a swimmer's eye level, the stacks, under the water.

## Deviations from L1 (each one line)

- The fountain and plinth stand in the middle of the forecourt (D-58), not at L1's (256, 896).
- The ship runs from (-230, -3800) to (1330, -4760); the log and the strongbox stand on its deck and in its hold, not at L1's points (-128, -3840) and (1280, -4736).
- The test's floor stands at (-2880, 1664), off the walk line through the east gate (L1 (-2688, 1280)).
- The Great Octopods start mid-sea, 512 over the bed (-1,024), with `above_floor` (merge point 27) and `leash: 1280` (indoor leash since merge point 26); with MM9's swimmer profile they are bound to their volume (session 18).
- The waterspout, bell frame and tide pool are nudged 420 inside their terraces' rims.

## Open items

## S's pieces (twentieth session, 2026-11-21)

- The Water Sleeper on his couch (`xeen_sleeper_water`, row radius 290): clicked, A3's `m38.sleeper_water` (its three answers; awake sets the qbit, the award and 10,500 experience).
- The statue on A6's plinth (`m38.plaque_water` on the plinth and on the statue); the test's pedestal 208 from its plate's centre, facing it.
- The return dais: S's disc on the studio disc's top, both hidden until the sleeper wakes; the dais rises the second the qbit is set (`evt:dais_show`, a 1-s timer) and on every load after (`evt:dais_load`); clicked on either, the dais's question and D7's return.
- Every binding turns by `yaw_offset` -90 (`facing` is where the front looks; the sleeper's head on the viewer's left). New playtest `playtest_sleeper` (the three answers, the dais hidden then shown, kept over a reload, Yes to D7).
- The couch faces north along the shelf's 768 (at L1's north-east it overhung the 512 side).
- The Drowned Bell (`xeen_drownedbell`) on the dry forecourt by its frame, facing 282 (no pool: the bell lies on the flags); clicked, `planes.bell` as the frame.
- The two mid-sea Octopod groups are A2's 11474 (`Xeen Octopod E`, S's foam-free swimmer; 11471's numbers, the count unchanged).


## Dressing exceptions

- None: `oymap audit` reports no dressing errors or warnings (no props: the dressing is studio geometry).

## S32 (2026-11-22, A6 32nd session)

Rebuilt and installed 01:36-01:39 (merge point 41): the way up, its column, the dais and its disc move into D7 through the standard entrance window (no Yes/No: F16, `planes/pieces.py d7_return_lua`); MAW reserve rewritten; stage tests all pass (sleeper and daily lines are status lines since D-90). The plate tops still show their picture 1.5x (18 audit errors, a studio fault: A1).

## S33 (2026-11-22, A6 33rd session: merge point 42)

The plates' `top_surface` is `{texture: xpwspray, size: [128, 128], fit: true}` (`size` is the picture's own size, 128;
`fit` lays it once over the 192 plate, and since merge point 42 once over its underside too). Rebuilt and installed
~02:00 through the stage (all stage tests pass); the 18 `textures.feature_repeated` errors are gone: the assets_dev
audit is 0 errors, 0 warnings. MAW reserve rewritten, `xeen_balance.py --check` passes.
