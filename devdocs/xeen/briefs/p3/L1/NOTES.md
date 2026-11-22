# P3 Plane of Earth of Xeen: L1 plan (MU-3, MU-4), approved with changes (D-58)

A6's planes sub-agent, 2026-11-21. A plan only: no geometry. Decider D-58 (`devdocs/xeen/briefs/d7/L1/D58_DECISION.md`) approved the board (`level_generation/xeen_art/phase6/planes/board_p34.png`) with changes; the sixteenth session applied them to the design data and rewrote this folder ("D-58 applied" below). Where this plan and D-58 differ, D-58 wins.

`level_generation/xeen_art/phase6/planes_design.py` holds the four planes' design as data (one family: the same skeleton, one element each). `planes_render.py` draws and measures it (plan SVG and PNG, the arrival blockout, `measure.json`), `planes_brief.py` writes this folder, `planes_concepts.py` paints one `codex exec` concept, `board_planes.py` boards the pair; `planes_run.py` runs them (Python under an 8 GB cgroup cap) and `oymap fmt`, `fmt --check` and `validate --assets assets_dev`.

Validation: `fmt --check` clean, `validate` no issues (see the run log in `level_generation/xeen_art/phase6/planes/run_p34.log`).

## D-58 applied

| Change | What was done | Figure |
| --- | --- | --- |
| P-1 the test in a qbit | the gate's link, goal:test, set:test and state:test_passed read or give m38_earth_test; the load event reads it: gate open, guardians hidden, pit quiet (A3's m38.test_earth_passed sets it) | qbit 111766 |
| P-2 no bypass | measured round The Sleeper's Hollow and the gate's link beyond the gate: the scree lip 256; gate flank lip 384; the gate between two monoliths of the Anvil's ring either side of the Root Stair's slab (384 high, 512 along the rim); the nearest higher floor (arena, -384) is 1,146 away, so no drop reaches it | lowest lip 256 (>= 192): holds |
| P-3 / C6 rows | names by the C6 pattern; ids where they exist (15 Lesser Earth Elemental (11626), 9 Earth Elemental (11720), 5 Earth Blaster (11721), 1 Sleeper's Guardian of Earth (11722)) | 30 hostiles, 32.04k per member (D-58 32.04k) |
| C2 arrival | lands standing at entrance:d7_fall (Xeen.PlaneArrivals.earth, A3) | (-3840, 3968), floor 0 |
| C3 the test | the guardians a hidden group at the pit, shown by m38.test_earth; their death events call Xeen.planeTestCheck | 1 x Sleeper's Guardian of Earth, 2 x Earth Blaster |
| C4 the gate | the stairs to the chamber opens on the qbit | one gate |
| C5 two ways out | the way up and the dais, both `exit` presets to D7's entrance:p3_return (lines m38.way_up_earth, m38.dais_earth) | always open / after the sleeper |
| C7 S's pieces | the sleeper, couch, statue, pedestal and dais are S's; L4 builds their spots by name and marks them blocked | no stand-ins |
| C8 POIs and chests | the test's chest and one trapped cache at treasure 6, one find, one buff device (the gem device stays as drawn: its one-time gem is planes.yml's) | 10 POIs, 2 chests |
| Q1 bowl | open to `xeen_plane_earth`; drops into the scree are real falls; scree slopes back up to every terrace, none to the Anvil or the Hollow | scree -1024, Hollow -768 |
| Q2 rockfall | nine plates calling planes.rockfall (with evt.CameraShake) | 0 on the critical path |
| Q3 monsters | elementals only | 32.04k |
| Concept corrections (L3) | the bowl reads deep: the scree 1,024 under the arrival, the Hollow 768; the walls lean in like a cavern's, not quarried steps; the Pillar Field is rough pillars like petrified trees | L3 |
| ROWS | map_stats 9117: encounter 0, treasure 6, lock 15, trap 8, perception 8, refill 672, music 3, MOUNTAINS (D-58 said QUARRY; the engine has none, so a door would sound like wood: MOUNTAIN, A2's note) | project.yml |
| Textures | `xperubble`, `xpegeode` new (Dungeon S, cap 30) | about 15 |

## The source

MM5 maze 27, the Elemental Plane of Earth (`dark/aaze0027`, 16 x 16, every square earth; decoded, nothing copied):

- the run position (9,9); the statue and its plaque (7,8);
- the test (3,4): 'Accept the test of Earth?'; yes costs 2,500 physical damage and sets a flag;
- the chest (13,12): 250 physical unless the flag is set; gold and three items;
- the Earth Sleeper (12,3), the same three answers;
- nine squares of falling rock: one time in three 50 physical damage;
- eight Earth Blasters (the greater earth elemental);
- the exit (2,13): a fall back to Skyroad F4 (map x112) at (13,2).

## The form

**A cavern-like bowl under a dust sky.** Earth is a bowl of rock: terraces stepping down a great pit whose walls rise like a cavern's, under the `xeen_plane_earth` sky of brown dust with no sun and no stars. The source's plane is all earth; MM8's eleme is a cave (a BLV). The bowl keeps the cavern's weight and closure while the open-air route keeps one sky and one view; the party goes down into the earth as it went up into the air on P2.

Room 26 x 26 cells (13,312 a side), north up, x east, y north, the middle at (0, 0); floors over the arrival (0).

## The walk

| Along | Where | What |
| ---: | --- | --- |
| 0 | The Dust Ledge (0) | Arrival `entrance:d7_fall` at (-3840, 3968), facing se; the way up at (-4864, 4864). Quiet. |
| 2,946 | | The first fight (`pop:statue_west`), 2,947 from the arrival. |
| 3,906 | The Stone Statue (-128) | The statue and its plaque (m38.plaque_earth). |
| 10,414 | The Anvil (-384) | The pedestal: 'Accept the test of Earth?' (m38.test_earth); the guardians rise. |
| 13,563 | | The sleeper's gate (open on the passed test). |
| 15,870 | The Sleeper's Hollow (-768) | The Earth Sleeper (m38.sleeper_earth); the test's chest. |
| 16,870 | | The return dais (after the sleeper) to D7's entrance:p3_return. |

Legs: arrival to the test 10,414; the test to the sleeper 5,456; the sleeper to the way out 1,000 (16,870 in all, about 44 s walking).

Spaces:

- **The Dust Ledge** (`room:landing`) at (-4096, 4224), 2,560 x 2,304, floor 0: a ledge of packed earth high on the bowl's north-west wall. Arrival from D7's south-east corner (entrance:d7_fall) and the way up (the dust shaft). Quiet.
- **The Stone Statue** (`room:statue`) at (-512, 1792), 2,560 x 2,304, floor -128: a broad terrace of flat stone, the statue of Earth at its middle. The statue and its plaque (m38.plaque_earth, Step Three); the ramps part here.
- **The Giants' Quarry** (`room:quarry`) at (4096, 3840), 2,560 x 2,560, floor -64: a terrace cut into steps by an old quarry, half-cut blocks still standing. The source's chest corner: the quarrymen's strongbox and their last block.
- **The Geode Hall** (`room:geodes`) at (4352, 0), 2,304 x 2,816, floor -256: a terrace of split boulders lined with amethyst and quartz. The Heart-geode (a device); the east loop.
- **The Pillar Field** (`room:pillars`) at (512, -1536), 2,560 x 2,304, floor -320: a terrace of tall stone pillars like petrified trees, the Echo Stone among them. The way down to the Anvil; the Echo Stone (a device).
- **The Fault Ledge** (`room:west_ledge`) at (-5376, 1024), 1,792 x 2,560, floor -192: a narrow ledge along a fault in the west wall. The west loop from the arrival down to the Anvil; Earth Blasters roam it.
- **The Anvil** (`room:arena`) at (-3840, -1792), 3,328 x 3,072, floor -384: a round floor of bare bedrock ringed by twelve monoliths, cracked at its middle. The test of Earth: the pedestal at the east gate asks 'Accept the test of Earth?'; the guardians rise out of the cracked bedrock. The Root Stair's head at the south-east.
- **The Sleeper's Hollow** (`room:chamber`) at (-1792, -5120), 2,560 x 2,048, floor -768: a hollow at the bowl's bottom under an overhang of the wall, roots of stone hanging from it. The Earth Sleeper on his couch (m38.sleeper_earth); the test's chest; the return dais (after the sleeper wakes).

Places:

- `entrance:d7_fall` at (-3840, 3968): Arrival from D7's south-east corner: on the Dust Ledge, facing south-east down into the bowl.
- `exit:way_up` at (-4864, 4864): The dust shaft: a column of pale light where dust streams upward out of the bowl. An exit preset ('Rise with the dust to the Skyroads?'), always open, to D7's entrance:p3_return (the source's (2,13), a fall back to Skyroad F4).
- `poi:statue` at (-512, 1920): The statue of Earth: a squat giant of rough-hewn granite, hands on its knees, on a plinth. A3's m38.plaque_earth: 'A message at the base of the statue reads: Step three: Bring together the Cube of Power and the Scepter of Temporal Distortion.' (aaze0027:2-3)
- `poi:geode` at (4608, 256): The Heart-geode: a split boulder lined with amethyst. Touched: +20 Earth resistance for a day (once a day; 'The stone is warm.').
- `poi:echo` at (1152, -896): The Echo Stone: a hollow pillar. Clicked: 'You shout into the stone. The plane answers, slowly.' The first time, a find in its hollow: a sapphire.
- `poi:test` at (-2432, -1792): The test pedestal at the Anvil's east gate: 'Accept the test of Earth?' (aaze0027:5). Yes calls A3's m38.test_earth; the map raises the guardians out of the bedrock (set:test).
- `landmark:anvil` at (-3840, -1792): The Anvil's crack: a split in the bedrock at its middle, where the guardians rise.
- `gate:sleeper` at (-2816, -3200): The Root Stair's slab: a block of stone across the stair's head, sunk once the test is passed (state:test_passed).
- `poi:sleeper` at (-2048, -5504): The Earth Sleeper on his couch under the overhang: A3's m38.sleeper_earth, three states (not Chosen; 'Awaiting Grunfeld field activation.'; awake, award 414, 10,500 XP).
- `poi:test_chest` at (-896, -5376): The test's chest (treasure 6): the source's chest, now in the hollow the test opens.
- `exit:dais` at (-2816, -4736): The return dais: a disc of grey granite, shown once the Earth Sleeper is awake (m38.earth); an exit preset to D7's entrance:p3_return.
- `poi:quarry_cache` at (4736, 4480): The quarrymen's strongbox (treasure 6, a falling-block trap) by their hut's ruin.
- `poi:last_block` at (3584, 3200): The last block: half-cut, a pick still in it, a slate: 'Nearly done. Back after lunch.' (ours) A find: Earth Resistance potions.

## Figures (`measure.json`)

| Figure | Target | Plan |
| --- | --- | --- |
| Size | MAPS §3: S-M dungeon scale (S 7-20 M units, M 30-90) | room 26 x 26 cells; floors span 23.1 x 22.6 cells; **49.5 M units** walkable |
| Scree | the element's ground | 91.3 M units, 65 % of the basin; farthest from a way out 4,189 (90 % within 3,010) |
| Placed hostiles | MAPS §0: 30 a plane | **30** (27 in 10 groups of 2-3, and the test's 3) |
| Levels | 55-70, the guardian 75 | 55-75, mean 60.3 |
| Kill XP per member | D-58: 32.04k (MAPS 31.0k a plane) | **32.04k** (+3.3 % on MAPS); XP = L(L+10) as D5 |
| First fight | 1,500-4,000 from the arrival | **2,947** |
| Quiet arrival | no spawns on the landing | 0 on it; nearest group to the way up 3,874 |
| Points of interest | C8: 10-12 | **10** (D-20 census, merged within 400); spacing median 2,969 (1,086-5,254) |
| Chests | C8: 2 (S 0-3) | **2**, treasure 6, and one find |
| Hazard cells | the source's nine | 9, 0 on the critical path, 0 on a link, 0 in the arena |
| P-2 no bypass | every lip at least 192 | lowest lip **256**; no higher floor within 1,024: holds ("D-58 applied") |
| Walk | - | 16,870 (arrival -> test -> sleeper -> way out) |
| Textures | Dungeon S cap 30 (4 new) | about 15, 2 new |

Hostiles by row:

- 15 x Lesser Earth Elemental (11626)
- 9 x Earth Elemental (11720)
- 5 x Earth Blaster (11721)
- 1 x Sleeper's Guardian of Earth (11722)

## Hazards and never stuck

- **Rockfall** (question 2): The source's nine squares of falling rock: patches of fresh rubble under overhangs (a small floor face each). Stepping on one: one time in three 50 physical damage to each member, 'Rocks fall from above!', with a short camera shake (evt.CameraShake).
- **Scree** (question 1): A drop from a terrace into the scree is a real fall (300-1,000, the engine's falling damage; Feather Fall none); scree slopes climb back to every terrace and ramp, none to the Anvil or the Hollow, so the test cannot be bypassed. The bowl's wall closes the room. The farthest point is 4,189 from a way out.
- **Never stuck**: the way up at the arrival is always open; Town Portal and Lloyd's Beacon work (no no_teleport); the test can be left and taken up again; the gate stays open once passed.

## Ways in and out (the corner contract)

- **In:** D7's south-east corner (Sky F4), `m38.corner_earth` ('What do you seek?' 'Earth'), drops the party to `entrance:d7_fall` here (common question C2: no falling damage).
- **Out, always:** the way up at the arrival, an exit preset, to D7's `entrance:p3_return`.
- **Out, after the sleeper:** the return dais in the chamber (condition m38.earth), the same arrival.
- corners.yml's `default_way_out` (the lead, D-58 C5) says this; Town Portal and Lloyd's Beacon work, Fly is not cast.

## Textures (shipped first; L3 confirms)

- `gwspotwl`: MM8's blue-grey rough rock; the bowl's walls.
- `gwsphlfl`: MM8's pale carved stone; the terraces and ramps.
- `vlcflora`: MM6 brown rock floor; the scree.
- `cwb1`: MM7 Nighon Tunnels rock (DD-10's); the overhang over the Hollow.
- `cfb1`: MM7 Nighon Tunnels floor; the Hollow's floor.
- `t19a02`: MM8 grey ashlar; the plinth and the monoliths.
- `xdvsaph`: DD-10's sapphire vein (A6); the Echo Stone.
- `xdvruby`: DD-10's ruby vein (A6); geode linings.
- `xcoreearth`: XD-19's earth core (A7); the sleeper couch's glow panel.
- new `xperubble`: fresh rubble under an overhang, one per rockfall face (the source's nine).
- new `xpegeode`: a split geode's amethyst lining (the Geode Hall's boulders, the Heart-geode).

About 15 distinct textures: class S (cap 30, at most 4 new; D-58 C1). The new ones are made at L3 through xtex.py and registered by the lead.

## Original lines

- 'Earth Sleeper' and the three sleeper answers (aaze0027:0-1, 6-7): m38.sleeper_earth.
- 'Plaque' and the Step text (aaze0027:2-3): m38.plaque_earth.
- 'Accept the test of Earth?' (aaze0027:5): m38.test_earth.
- 'Chest' (aaze0027:4): the test's chest's name.

## Hooks placed

- A3's, by name: `m38.plaque_earth` (the statue), `m38.test_earth` (the pedestal; yes shows the guardians), `m38.sleeper_earth` (the couch, every click; sets m38.earth, qbit 111762).
- The test (P-1, C3): each guardian's death event calls `Xeen.planeTestCheck("earth", <group>)` (xeen_common.lua), which runs `m38.test_earth_passed` once (sets m38.earth_test, qbit 111766); the load event reads the qbit.
- The ways out (C5): `m38.way_up_earth` and `m38.dais_earth`, the lines the two `exit` presets' windows mean (nothing to call).
- The hazard and the places (`source/npcs/planes.yml`): `planes.rockfall` on the nine plates, the device, the find's note and the gem device by their names there.
- In: D7's `m38.corner_earth`, then `Xeen.toPlane("earth")` to `Xeen.PlaneArrivals.earth` = `entrance:d7_fall` here.

## MU-4 concept

`planes_concepts.py p3`: one `codex exec`, first attempt, 62 s; raw `planes/raw/p3_arrival_v1.png` with its prompt and log. References: the arrival blockout, the Darkside day sky (for the manner of dim amber light), MM8's `gwspotwl` and `gwsphlfl`. It shows the Dust Ledge's packed earth, the seated granite giant on its plinth left, a field of standing stones in the middle, the Anvil's cracked bedrock ringed by monoliths right, the Sleeper's Hollow glowing amber under the overhang between them, scree and boulders in the drops, crystals in the walls and a brown dust sky. Against the plan (the plan wins at L2-L3): the bowl reads shallow (the scree lies 1,024 under the arrival, the Hollow 768); the walls read as quarried steps rather than leaning cavern walls; the Pillar Field is squared monoliths, the plan's are rough pillars like petrified trees.

## The questions and D-58's answers

The common questions C1-C8 are in P1's NOTES (`devdocs/xeen/briefs/p1/L1/NOTES.md`); D-58 took the drawn default on each (C6 (b)).

P3's own:

Q1. **The form: a cavern-like bowl or open sky under xeen_plane_earth**
   - Options:
     - (a) A bowl: terraces stepping down a pit whose walls lean in like a cavern's, open to the `xeen_plane_earth` dust sky (open-air BLV); drops into the scree hurt, scree slopes lead back up.
     - (b) A true cavern: a closed BLV with a rock ceiling and no sky (MM8's eleme is a BLV); the preset unused.
     - (c) Floating rock islands in the dust sky, as P2 but heavy (falls caught).
   - Evidence: corners.yml and lanes README give P3 the `xeen_plane_earth` preset (dust, no sun); MM8's eleme is a cave; the source's plane is open ground.
   - Proposed default (drawn): (a): the preset, the closure and the way down into the earth.
   - Depends on it: L2 geometry; the preset; the drop rule.
   - **Decided (D-58):** (a) A bowl open to the `xeen_plane_earth` sky: drops into the scree are real falls, scree slopes lead back up to every terrace; P-2 holds.
Q2. **Falling rock or quakes**
   - Options:
     - (a) The source's nine rockfall cells (1 in 3: 50 physical to each member) with a short camera shake when one hits.
     - (b) Quakes: every few minutes the whole plane shakes (evt.CameraShake) and rock falls on the nine cells for a few seconds (a timed set piece).
     - (c) No hazard beyond the drops.
   - Evidence: maze0027: nine squares call one event: random 1-3, on 3 Damage 50 type 0 (physical). evt.CameraShake exists (MM9 cutscenes).
   - Proposed default (drawn): (a)
   - Depends on it: A3's line; xperubble; A1's floor-event check.
   - **Decided (D-58):** (a) Nine plates: one time in three 50 physical, 'Rocks fall from above!', a short evt.CameraShake when one hits.
Q3. **Only elementals on P3?**
   - Options:
     - (a) Yes: Lesser Earth Elementals (55, 11626), Earth Elementals (62) and Greater Earth Elementals (70), as the source (eight Earth Blasters).
     - (b) Add two Onyx Golems (11584, 85) as the Root Stair's wardens (over the band).
     - (c) Add Diamond Golems (11583, 50) in the quarry (under the band).
   - Evidence: monsters.yml: no other earth family at 55-70 (material golems stop at 50, then 85).
   - Proposed default (drawn): (a)
   - Depends on it: A2's rows (C6); kill XP.
   - **Decided (D-58):** (a) Elementals only, 32.04k.

## Requests (for the orchestrator to relay; D-58 state)

- **A2**: row 9117: environment quarry, music 3; the Earth rows of C6 (62, 70, the guardian 75); Lesser Earth Elemental 11626 used on P3 (15 placed).
- **A6**: new textures xperubble and xpegeode, registered; xeen_plane_earth checked under an open-air BLV.
- **S**: the statue of Earth; the Heart-geode; the quarry's half-cut blocks with a pick; the Anvil's twelve monoliths (shipped standing stones if they fit).

## Blocked

Nothing blocks L1 or L2: A2's map_stats row 9117 and the element rows (C6) landed 2026-11-21. L4's walks from assets_dev wait on S's sleeper, couch, statue, pedestal and dais (C7; spots built by name, blocked) and D7's install (its entrance:p3_return). A3's hooks are written (m38.test_earth_passed, way_up, dais, planes.yml).
