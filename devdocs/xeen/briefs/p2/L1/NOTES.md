# P2 Plane of Air of Xeen: L1 plan (MU-3, MU-4), approved with changes (D-58)

A6's planes sub-agent, 2026-11-21. A plan only: no geometry. Decider D-58 (`devdocs/xeen/briefs/d7/L1/D58_DECISION.md`) approved the board (`level_generation/xeen_art/phase6/planes/board_p12.png`) with changes; the sixteenth session applied them to the design data and rewrote this folder ("D-58 applied" below). Where this plan and D-58 differ, D-58 wins.

`level_generation/xeen_art/phase6/planes_design.py` holds the four planes' design as data (one family: the same skeleton, one element each). `planes_render.py` draws and measures it (plan SVG and PNG, the arrival blockout, `measure.json`), `planes_brief.py` writes this folder, `planes_concepts.py` paints one `codex exec` concept, `board_planes.py` boards the pair; `planes_run.py` runs them (Python under an 8 GB cgroup cap) and `oymap fmt`, `fmt --check` and `validate --assets assets_dev`.

Validation: `fmt --check` clean, `validate` no issues (see the run log in `level_generation/xeen_art/phase6/planes/run_p12.log`).

## D-58 applied

| Change | What was done | Figure |
| --- | --- | --- |
| P-1 the test in a qbit | the gate's link, goal:test, set:test and state:test_passed read or give m38_air_test; the load event reads it: gate open, guardians hidden, pit quiet (A3's m38.test_air_passed sets it) | qbit 111765 |
| P-2 no bypass | measured round The Sleeper's Aerie and the gate's link beyond the gate: sky open sky; gate flank lip 384; the gate between two standing stones of the Eye's ring either side of the stair's foot, the stilled wind between them (384 high, 512 along the rim); the nearest higher floor (stones, 256) is 2,438 away, so no drop reaches it | lowest lip 384 (>= 192): holds |
| P-3 / C6 rows | names by the C6 pattern; ids where they exist (15 Lesser Air Elemental (11624), 9 Air Elemental (11700), 5 Whirlwind (11701), 1 Sleeper's Guardian of Air (11702)) | 30 hostiles, 32.04k per member (D-58 32.04k) |
| C2 arrival | lands standing at entrance:d7_fall (Xeen.PlaneArrivals.air, A3) | (-4096, -4096), floor 0 |
| C3 the test | the guardians a hidden group at the pit, shown by m38.test_air; their death events call Xeen.planeTestCheck | 1 x Sleeper's Guardian of Air, 2 x Whirlwind |
| C4 the gate | the stairs to the chamber opens on the qbit | one gate |
| C5 two ways out | the way up and the dais, both `exit` presets to D7's entrance:p2_return (lines m38.way_up_air, m38.dais_air) | always open / after the sleeper |
| C7 S's pieces | the sleeper, couch, statue, pedestal and dais are S's; L4 builds their spots by name and marks them blocked | no stand-ins |
| C8 POIs and chests | the test's chest and one trapped cache at treasure 6, one find, one buff device (the gem device stays as drawn: its one-time gem is planes.yml's) | 10 POIs, 2 chests |
| Q1 falls | below -1,500 Xeen.skyFallTo("p2") (A3's SkyFalls key `p2`; the brief's proposed `p2_self` is not needed) to entrance:d7_fall here from 850 above, falling damage | D-54 tests at L4 |
| Q2 storm cells | nine plates calling planes.storm; two cells moved out of the Eye | 0 on bridges, 0 in the Eye |
| Q3 sky | the shipped `plane_air` | atmosphere.yml |
| Q4 monsters | elementals only | 32.04k |
| Concept corrections (L3) | the aerie is the highest island (768); no posts or pennants on the walking line; L3 dressing may put them at the edges only; the statue's plinth stands in the middle of its island | L3 |
| ROWS | map_stats 9116: encounter 0, treasure 6, lock 15, trap 8, perception 8, refill 672, music 9, PLAINS | project.yml |
| Textures | `xpascorch`, `xpastone` new (Dungeon S, cap 30) | about 14 |

## The source

MM5 maze 26, the Elemental Plane of Air (`dark/aaze0026`, 16 x 16, every square cloud; decoded, nothing copied):

- the run position (9,9); the statue and its plaque (7,7);
- the test (10,2): 'Accept the test of Air?'; yes costs 2,500 electrical damage and sets a flag;
- the chest (5,13): 250 electrical unless the flag is set; gold and three items;
- the Air Sleeper (12,12), the same three answers;
- nine storm squares: one time in three 50 electrical damage;
- eight Whirlwinds (the greater air elemental);
- the exit (2,2): a fall back to Skyroad F1 (map x109) at (12,13).

## The form

**Islands in open sky.** Air is open sky over nothing: islands of wind-carved pale stone and packed cloud, linked by cloud-stone bridges, the sky above and below. The source's plane is all cloud; MM8's elema is islands with no terrain. X8 and X9 built this route; the plane is their small, stranger cousin.

Room 26 x 26 cells (13,312 a side), north up, x east, y north, the middle at (0, 0); floors over the arrival (0).

## The walk

| Along | Where | What |
| ---: | --- | --- |
| 0 | The Gale Landing (0) | Arrival `entrance:d7_fall` at (-4096, -4096), facing ne; the way up at (-5248, -4864). Quiet. |
| 2,940 | | The first fight (`pop:statue_west`), 2,947 from the arrival. |
| 4,303 | The Wind Statue (128) | The statue and its plaque (m38.plaque_air). |
| 7,355 | The Eye of the Winds (256) | The pedestal: 'Accept the test of Air?' (m38.test_air); the guardians rise. |
| 10,555 | | The sleeper's gate (open on the passed test). |
| 16,018 | The Sleeper's Aerie (768) | The Air Sleeper (m38.sleeper_air); the test's chest. |
| 17,687 | | The return dais (after the sleeper) to D7's entrance:p2_return. |

Legs: arrival to the test 7,355; the test to the sleeper 8,663; the sleeper to the way out 1,669 (17,687 in all, about 46 s walking).

Spaces:

- **The Gale Landing** (`room:landing`) at (-4096, -4352), 2,560 x 2,304, floor 0: a flat island of white stone, the updraft's ring at its west edge. Arrival from D7's north-east corner (entrance:d7_fall) and the way up (the updraft). Quiet.
- **The Wind Statue** (`room:statue`) at (-384, -1920), 2,560 x 2,304, floor 128: a round island of packed cloud, the statue of Air on a stone plinth. The statue and its plaque (m38.plaque_air, Step Two); bridges part here.
- **The Singing Stones** (`room:stones`) at (0, 1920), 2,560 x 2,560, floor 256: a high island crowned by a ring of hollow standing stones that sing in the wind. The Singing Stones (a device); the middle of the plane.
- **The Kite Isle** (`room:kite_isle`) at (-4224, 3584), 2,560 x 2,560, floor 320: a ragged island of wind-carved stone, a wrecked basket in its rocks. The source's chest corner: a balloonist's basket with no balloon and his cache; the Whirlwinds that roam it.
- **The Eye of the Winds** (`room:arena`) at (3968, -3072), 3,328 x 3,328, floor 256: a round island ringed by twelve standing stones, the wind circling inside. The test of Air: the pedestal at the west gate asks 'Accept the test of Air?'; the guardians form in the eye. The foot of the Stair of Wind on the north side.
- **The Sleeper's Aerie** (`room:chamber`) at (4224, 3456), 2,560 x 2,304, floor 768: the highest island, a pale dome open on all sides over the couch. The Air Sleeper on his couch (m38.sleeper_air); the test's chest; the return dais (after the sleeper wakes).

Places:

- `entrance:d7_fall` at (-4096, -4096): Arrival from D7's north-east corner: on the Gale Landing, facing north-east across the gap.
- `exit:way_up` at (-5248, -4864): The updraft: a ring of white stones where the wind blows straight up, mist streaming skyward. An exit preset ('Ride the wind back to the Skyroads?'), always open, to D7's entrance:p2_return (the source's (2,2), a fall back to Skyroad F1).
- `poi:statue` at (-384, -1792): The statue of Air: a winged figure of white stone, robes streaming, on a plinth. A3's m38.plaque_air: 'A message at the base of the statue reads: Step Two: Awaken the Four Sleepers of Darkside.' (aaze0026:2-3)
- `poi:singing_stones` at (0, 2176): The Singing Stones: a ring of hollow stones. Clicked: they sing; +20 Air resistance and +10 Speed for a day, once a day ('The stones sing. You feel lighter.').
- `poi:test` at (2432, -3072): The test pedestal at the Eye's west gate: 'Accept the test of Air?' (aaze0026:5). Yes calls A3's m38.test_air; the map forms the guardians in the eye (set:test).
- `landmark:eye` at (3968, -3072): The eye: a calm circle in the middle of the standing stones, dust and leaves turning round it.
- `gate:sleeper` at (3968, -1408): The Stair of Wind's gate: a curtain of roaring wind between two stones at the Eye's north side, stilled once the test is passed (state:test_passed).
- `poi:sleeper` at (4864, 3840): The Air Sleeper on his couch under the dome: A3's m38.sleeper_air, three states (not Chosen; 'Awaiting Grunfeld field activation.'; awake, award 413, 10,500 XP).
- `poi:test_chest` at (3584, 4224): The test's chest (treasure 6): the source's chest, now in the aerie the test opens.
- `exit:dais` at (3456, 2944): The return dais: a disc of white stone, shown once the Air Sleeper is awake (m38.air); an exit preset to D7's entrance:p2_return.
- `poi:basket_cache` at (-3824, 4400): The balloonist's cache (treasure 6, a lightning trap): his strongbox wedged in the basket.
- `poi:basket` at (-3712, 4224): The basket with no balloon: a wicker gondola wedged in the rocks, a logbook: 'Wind fair. Balloon fairer. Balloon gone.' (ours) A find: Air Resistance potions.
- `poi:storm_cairn` at (1024, -2560): The storm cairn: a cairn of fused stones. Clicked: 'Lightning has struck here. Often.' The first time, a blue gem in the glass (a find).

## Figures (`measure.json`)

| Figure | Target | Plan |
| --- | --- | --- |
| Size | MAPS §3: S-M dungeon scale (S 7-20 M units, M 30-90) | room 26 x 26 cells; floors span 21.8 x 20.2 cells; **45.0 M units** walkable |
| Sky | the element | 75 % of the room; smallest unbridged gap 1,801; bridges 1,487-3,717 (D-6.2: spans up to 4,000) |
| Placed hostiles | MAPS §0: 30 a plane | **30** (27 in 10 groups of 2-3, and the test's 3) |
| Levels | 55-70, the guardian 75 | 55-75, mean 60.3 |
| Kill XP per member | D-58: 32.04k (MAPS 31.0k a plane) | **32.04k** (+3.3 % on MAPS); XP = L(L+10) as D5 |
| First fight | 1,500-4,000 from the arrival | **2,947** |
| Quiet arrival | no spawns on the landing | 0 on it; nearest group to the way up 4,331 |
| Points of interest | C8: 10-12 | **10** (D-20 census, merged within 400); spacing median 1,498 (1,286-5,753) |
| Chests | C8: 2 (S 0-3) | **2**, treasure 6, and one find |
| Hazard cells | the source's nine | 9, 0 on the critical path, 0 on a link, 0 in the arena |
| P-2 no bypass | every lip at least 192 | lowest lip **384**; no higher floor within 1,024: holds ("D-58 applied") |
| Walk | - | 17,687 (arrival -> test -> sleeper -> way out) |
| Textures | Dungeon S cap 30 (4 new) | about 14, 2 new |

Hostiles by row:

- 15 x Lesser Air Elemental (11624)
- 9 x Air Elemental (11700)
- 5 x Whirlwind (11701)
- 1 x Sleeper's Guardian of Air (11702)

## Hazards and never stuck

- **Storm** (question 2): The source's nine storm squares: scorched patches on the islands (a small floor face each). Stepping on one: one time in three 50 electrical damage to each member, 'Lightning strikes from a clear sky!' (resistance applies).
- **Falls** (question 1): A fall off any island (below -1,500): the wind throws the party back onto the Gale Landing: Xeen.skyFallTo("p2") moves it to entrance:d7_fall in this map from Xeen.SkyFallHeight (850) above it, with falling damage (D-6.2's third of HP at most; Feather Fall none; D-58 P2 Q1). Tested in D-54's shape: from three islands, two runs each, HP checked after 20 s.
- **Never stuck**: the way up at the arrival is always open; Town Portal and Lloyd's Beacon work (no no_teleport); the test can be left and taken up again; the gate stays open once passed.

## Ways in and out (the corner contract)

- **In:** D7's north-east corner (Sky F1), `m38.corner_air` ('What do you seek?' 'Air'), drops the party to `entrance:d7_fall` here (common question C2: no falling damage).
- **Out, always:** the way up at the arrival, an exit preset, to D7's `entrance:p2_return`.
- **Out, after the sleeper:** the return dais in the chamber (condition m38.air), the same arrival.
- corners.yml's `default_way_out` (the lead, D-58 C5) says this; Town Portal and Lloyd's Beacon work, Fly is not cast.

## Textures (shipped first; L3 confirms)

- `xccloud`: X8's walkable cloud top (A6); the cloud island tops.
- `xccloudsd`: X8's cloud sides (A6); the cloud islands' sides and undersides.
- `7tws1f`: X9's cloud-stone (MM7 marble); bridges, the plinth, the aerie floor.
- `gwspotwl`: MM8's blue-grey rough rock; the stone islands' rock.
- `gwsphlfl`: MM8's pale wind-carved stone; the stone islands' tops.
- `t09a01`: MM8 Plane of Air's pale brick; the aerie dome's base, the stair's cheeks.
- `gn_mtl01`: MM8 Plane of Air's grey stone; the standing stones.
- `xcoreair`: XD-19's air core (A7); the sleeper couch's glow panel.
- new `xpascorch`: a lightning scorch on pale stone, one per storm face (the source's nine).
- new `xpastone`: a hollow singing stone, pierced and wind-worn (the Singing Stones' faces).

About 14 distinct textures: class S (cap 30, at most 4 new; D-58 C1). The new ones are made at L3 through xtex.py and registered by the lead.

## Original lines

- 'Air Sleeper' and the three sleeper answers (aaze0026:0-1, 6-7): m38.sleeper_air.
- 'Plaque' and the Step text (aaze0026:2-3): m38.plaque_air.
- 'Accept the test of Air?' (aaze0026:5): m38.test_air.
- 'Chest' (aaze0026:4): the test's chest's name.

## Hooks placed

- A3's, by name: `m38.plaque_air` (the statue), `m38.test_air` (the pedestal; yes shows the guardians), `m38.sleeper_air` (the couch, every click; sets m38.air, qbit 111761).
- The test (P-1, C3): each guardian's death event calls `Xeen.planeTestCheck("air", <group>)` (xeen_common.lua), which runs `m38.test_air_passed` once (sets m38.air_test, qbit 111765); the load event reads the qbit.
- The ways out (C5): `m38.way_up_air` and `m38.dais_air`, the lines the two `exit` presets' windows mean (nothing to call).
- The hazard and the places (`source/npcs/planes.yml`): `planes.storm` on the nine plates, the device, the find's note and the gem device by their names there.
- In: D7's `m38.corner_air`, then `Xeen.toPlane("air")` to `Xeen.PlaneArrivals.air` = `entrance:d7_fall` here. Falls: `Xeen.skyFallTo("p2")`.

## MU-4 concept

`planes_concepts.py p2`: one `codex exec`, first attempt, 69 s; raw `planes/raw/p2_arrival_v1.png` with its prompt and log. References: the arrival blockout, X9's approved concept (D-50: this world's sky and cloud-stone), MM8's `gwsphlfl`. It shows the Gale Landing's wind-scoured stone, the cloud-stone bridge to the winged statue of Air, the Singing Stones' pierced ring on its island left, the aerie's open dome with the couch beyond, and the Eye of the Winds' standing stones right with leaves circling, every island on a tapering rock underside over open sky. Against the plan: the aerie stands too low (the plan puts it 768 over the arrival, the highest island); the gold posts and pennants along the bridge are not in the plan (L3 dressing may keep posts by the edge, never on the walk); the statue's plinth stands on the bridge's end, the plan puts it in the island's middle.

## The questions and D-58's answers

The common questions C1-C8 are in P1's NOTES (`devdocs/xeen/briefs/p1/L1/NOTES.md`); D-58 took the drawn default on each (C6 (b)).

P2's own:

Q1. **Falls off the islands**
   - Options:
     - (a) In the map: below -1,500 the wind throws the party back onto the Gale Landing (entrance:d7_fall) with falling damage (D-6.2's rule); the test and the plane are not lost.
     - (b) Out to D7's entrance:p2_return with falling damage (as the way up, the hard way).
     - (c) To the surface under D7's north-east corner (D6), as every sky map falls to its surface.
   - Evidence: The plane is not over the world: the source has no fall from it but its exit square (to Skyroad F1). X8, X9 and P5 fall to the surface because they hang over it.
   - Proposed default (drawn): (a)
   - Depends on it: A3's Xeen.skyFall with an in-map target; P2's fall tests (D-54's shape).
   - **Decided (D-58):** (a) Below -1,500 the wind throws the party back onto the Gale Landing: the fall goes to entrance:d7_fall in this map from Xeen.SkyFallHeight above it, with falling damage (D-6.2); D-54's tests from three islands.
Q2. **The storm cells**
   - Options:
     - (a) Nine scorched floor faces with the source's rule (1 in 3: 50 electrical to each member); none on bridges or in the Eye.
     - (b) Lightning on a timer at the storm cairn only (a set piece).
     - (c) None.
   - Evidence: maze0026: nine squares call one event: random 1-3, on 3 Damage 50 type 3 (electrical).
   - Proposed default (drawn): (a)
   - Depends on it: A3's line; xpascorch; A1's floor-event check.
   - **Decided (D-58):** (a) Nine plates: one time in three 50 electrical, 'Lightning strikes from a clear sky!'; none on bridges or in the Eye.
Q3. **Sky**
   - Options:
     - (a) MM8's shipped `plane_air` (engine library) by name: below_horizon sky.
     - (b) `xeencloud` (xeen_cloud_sea) as every Xeen sky map.
     - (c) A new Xeen preset `xeen_plane_air` (A6): plane_air with no cloud sea below, only blue.
   - Evidence: WORLD_DESIGN §4 names plane_air for the plane. The plane must not look like X8/X9/D7's cloud sea: there is no world under it.
   - Proposed default (drawn): (a)
   - Depends on it: atmosphere.yml; A6's sky file.
   - **Decided (D-58):** (a) The shipped `plane_air` (below_horizon sky).
Q4. **Only elementals on P2?**
   - Options:
     - (a) Yes: Lesser Air Elementals (55), Air Elementals (62), Greater Air Elementals (70), as the source (eight Whirlwinds); variety from the islands and the storm.
     - (b) Add a pair of Sky Golems (11594, 75) guarding the Stair of Wind's foot (over the band).
     - (c) Add Cloud Golems (11592, 50) as the A tier (under the band).
   - Evidence: monsters.yml: no other Air family at 55-70; rocs and griffins stop at 48.
   - Proposed default (drawn): (a)
   - Depends on it: A2's rows (C6); kill XP.
   - **Decided (D-58):** (a) Elementals only, 32.04k.

## Requests (for the orchestrator to relay; D-58 state)

- **A2**: row 9116: environment plains, music 9; the Air rows of C6 (62, 70, the guardian 75); Lesser Air Elemental 11624 used on P2 (15 placed).
- **A6**: new textures xpascorch and xpastone, registered; plane_air or a Xeen preset (Q3).
- **S**: the statue of Air; the Singing Stones (a ring of hollow standing stones); the wrecked basket; the Eye's twelve standing stones (shipped menhirs if they fit).

## Blocked

Nothing blocks L1 or L2: A2's map_stats row 9116 and the element rows (C6) landed 2026-11-21. L4's walks from assets_dev wait on S's sleeper, couch, statue, pedestal and dais (C7; spots built by name, blocked) and D7's install (its entrance:p2_return). A3's hooks are written (m38.test_air_passed, way_up, dais, planes.yml).
