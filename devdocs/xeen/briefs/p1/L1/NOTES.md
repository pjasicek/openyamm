# P1 Plane of Fire of Xeen: L1 plan (MU-3, MU-4), approved with changes (D-58)

A6's planes sub-agent, 2026-11-21. A plan only: no geometry. Decider D-58 (`devdocs/xeen/briefs/d7/L1/D58_DECISION.md`) approved the board (`level_generation/xeen_art/phase6/planes/board_p12.png`) with changes; the sixteenth session applied them to the design data and rewrote this folder ("D-58 applied" below). Where this plan and D-58 differ, D-58 wins.

`level_generation/xeen_art/phase6/planes_design.py` holds the four planes' design as data (one family: the same skeleton, one element each). `planes_render.py` draws and measures it (plan SVG and PNG, the arrival blockout, `measure.json`), `planes_brief.py` writes this folder, `planes_concepts.py` paints one `codex exec` concept, `board_planes.py` boards the pair; `planes_run.py` runs them (Python under an 8 GB cgroup cap) and `oymap fmt`, `fmt --check` and `validate --assets assets_dev`.

Validation: `fmt --check` clean, `validate` no issues (see the run log in `level_generation/xeen_art/phase6/planes/run_p12.log`).

## D-58 applied

| Change | What was done | Figure |
| --- | --- | --- |
| P-1 the test in a qbit | the gate's link, goal:test, set:test and state:test_passed read or give m38_fire_test; the load event reads it: gate open, guardians hidden, pit quiet (A3's m38.test_fire_passed sets it) | qbit 111764 |
| P-2 no bypass | measured round The Sleeper's Hall and the gate's link beyond the gate: the lava lip 321; rim lip 2,400; gate flank lip 384; the gate between two obsidian piers either side of the gate's two leaves (384 high, 512 along the rim); the nearest higher floor (arena, 256) is 1,499 away, so no drop reaches it | lowest lip 321 (>= 192): holds |
| P-3 / C6 rows | names by the C6 pattern; ids where they exist (11 Lesser Fire Elemental (11620), 5 Lava Golem (11593), 9 Fire Elemental (11621), 4 Fire Blower (11622), 1 Sleeper's Guardian of Fire (11623)) | 30 hostiles, 31.54k per member (D-58 31.54k) |
| C2 arrival | lands standing at entrance:d7_fall (Xeen.PlaneArrivals.fire, A3) | (3776, -3904), floor 0 |
| C3 the test | the guardians a hidden group at the pit, shown by m38.test_fire; their death events call Xeen.planeTestCheck | 1 x Sleeper's Guardian of Fire, 2 x Fire Blower |
| C4 the gate | the portcullis to the chamber opens on the qbit | one gate |
| C5 two ways out | the way up and the dais, both `exit` presets to D7's entrance:p1_return (lines m38.way_up_fire, m38.dais_fire) | always open / after the sleeper |
| C7 S's pieces | the sleeper, couch, statue, pedestal and dais are S's; L4 builds their spots by name and marks them blocked | no stand-ins |
| C8 POIs and chests | the test's chest and one trapped cache at treasure 6, one find, one buff device (the gem device stays as drawn: its one-time gem is planes.yml's) | 10 POIs, 2 chests |
| Q1 lava | walkable `lavtyl` that burns; crust banks within 64 of every lava edge and ramps up every shelf, none to the hall or its bridge | 90 % of the lava within 1,703 of a bank |
| Q2 vents | nine PressurePlate faces `xpfvent` calling planes.vent | 9, 0 on the critical path |
| Q3 sky | the shipped `plane_fire` | atmosphere.yml |
| Concept corrections (L3) | the crater wall is ragged cliffs, not cut slabs; the statue stands about 3,700 away (along the walk), not nearer; the Crucible stands on its rise | L3 |
| ROWS | map_stats 9115: encounter 0, treasure 6, lock 15, trap 8, perception 8, refill 672, music 10, MOUNTAINS | project.yml |
| Textures | `xpfvent`, `xpfglass` new (Dungeon S, cap 30) | about 16 |

## The source

MM5 maze 25, the Elemental Plane of Fire (`dark/aaze0025`, 16 x 16 squares, every square lava; decoded from `reference/mm4_5_world_of_xeen/unpacked`, nothing copied):

- the run position (9,9) in the middle; the statue and its plaque (8,7) two squares away;
- the test (10,13): 'Accept the test of Fire?'; yes costs 2,500 fire damage and sets a flag;
- the chest (2,4): burns for 250 unless the flag is set; gold and three items;
- the Fire Sleeper (3,12): three answers (not Chosen; 'Awaiting Grunfeld field activation.'; awake, the award);
- nine vent squares: one time in three 50 fire damage;
- eight Fire Blowers (the greater fire elemental);
- the exit (13,2): a fall back to Skyroad A1 (map 89) at (3,13).

## The form

**Lava field in a crater.** Fire is a lava field: a lake of lava in a ring of black cliffs, crossed by causeways of cooled crust between basalt shelves. The source's plane is all lava; MM8's elemf is 74 % lava. A crater closes the room without walls in the sky and keeps the map compact; the lava is the hazard and the floor.

Room 26 x 26 cells (13,312 a side), north up, x east, y north, the middle at (0, 0); floors over the arrival (0).

## The walk

| Along | Where | What |
| ---: | --- | --- |
| 0 | The Cinder Shelf (0) | Arrival `entrance:d7_fall` at (3776, -3904), facing nw; the way up at (4864, -4864). Quiet. |
| 2,555 | | The first fight (`pop:statue_lesser`), 2,555 from the arrival. |
| 3,639 | The Flame Statue (64) | The statue and its plaque (m38.plaque_fire). |
| 8,836 | The Crucible (256) | The pedestal: 'Accept the test of Fire?' (m38.test_fire); the guardians rise. |
| 12,091 | | The sleeper's gate (open on the passed test). |
| 14,904 | The Sleeper's Hall (384) | The Fire Sleeper (m38.sleeper_fire); the test's chest. |
| 15,827 | | The return dais (after the sleeper) to D7's entrance:p1_return. |

Legs: arrival to the test 8,836; the test to the sleeper 6,068; the sleeper to the way out 923 (15,827 in all, about 41 s walking).

Spaces:

- **The Cinder Shelf** (`room:landing`) at (4096, -4224), 2,560 x 2,304, floor 0: a low shelf of cooled black crust in the crater's south-east, the heat column at its corner. Arrival from D7's north-west corner (entrance:d7_fall) and the way up (the heat column). Quiet.
- **The Flame Statue** (`room:statue`) at (512, -2560), 2,304 x 2,048, floor 64: a round crust shelf, the statue of Fire on its plinth in the middle. The statue and its plaque (m38.plaque_fire, Step One); the causeways part here.
- **The Ember Islet** (`room:islet`) at (-896, -256), 1,792 x 1,536, floor 96: a small crust islet in the lava, on the straight way north. The straight way to the Crucible; the Ember Font (a font of liquid fire).
- **The Basalt Spires** (`room:spires`) at (3968, 896), 2,560 x 2,816, floor 128: a shelf of basalt columns and spires, the long way round to the east. The east loop: lava golems and elementals among the columns.
- **The Crucible** (`room:arena`) at (256, 3456), 3,328 x 3,072, floor 256: a round ring of black glass on a basalt rise, lava welling in a pit at its middle. The test of Fire: the pedestal at the south gate asks 'Accept the test of Fire?'; the guardians rise from the pit. The Sleeper's Gate on the west side.
- **The Sleeper's Hall** (`room:chamber`) at (-4096, 4480), 2,560 x 2,048, floor 384: a hall open to the sky, cut into the tallest spire of the crater wall, floored in black glass, the spire's rock walling its back and sides (P-2). The Fire Sleeper on his couch (m38.sleeper_fire); the test's chest; the return dais (after the sleeper wakes).
- **The Glass Shelf** (`room:west_shelf`) at (-4480, 768), 2,304 x 2,816, floor 128: a shelf of black glass under the west wall, a lava fall beside it. The west loop: Fire Elementals and the Fire Blowers that roam it.
- **The Vent Field** (`room:vents`) at (-3712, -3840), 2,816 x 2,304, floor 0: a crust field pocked with glowing vents (the source's nine). The vents (the plane's hazard); the burnt camp of a fire-walker and his ember cache.

Places:

- `entrance:d7_fall` at (3776, -3904): Arrival from D7's north-west corner: on the Cinder Shelf, facing north-west over the lava.
- `exit:way_up` at (4864, -4864): The heat column: a pillar of shimmering air rising from a ring of fire-stones in the shelf's corner. An exit preset ('Ride the heat back to the Skyroads?'), always open, to D7's entrance:p1_return (the source's (13,2), a fall back to Skyroad A1).
- `poi:statue` at (512, -2432): The statue of Fire: a tall figure of flame in red stone on a black plinth. A3's m38.plaque_fire: 'A message at the base of the statue reads: Step One: When the time is right, activate the machines in the four corners of the other side of the world.' (aaze0025:3-4)
- `poi:font` at (-1152, -448): The Ember Font: a basin of liquid fire on the islet. Drunk from: +20 Fire resistance for a day (once a day; 'The fire is cool and refreshing.'), the world's wink on the stock well line.
- `poi:test` at (256, 2048): The test pedestal at the Crucible's south gate: 'Accept the test of Fire?' (aaze0025:6). Yes calls A3's m38.test_fire; the map raises the guardians from the pit (set:test).
- `landmark:pit` at (256, 3584): The Crucible's pit: lava welling in a ring of black glass, where the guardians rise.
- `gate:sleeper` at (-1536, 3904): The Sleeper's Gate: a portcullis of black glass at the Crucible's west side, open once the test is passed (state:test_passed).
- `poi:sleeper` at (-4352, 4864): The Fire Sleeper on his couch: A3's m38.sleeper_fire, three states (not Chosen; 'Awaiting Grunfeld field activation.'; awake, award 412, 10,500 XP).
- `poi:test_chest` at (-3328, 5248): The test's chest (treasure 6): the source's chest, now behind the gate the test opens.
- `exit:dais` at (-4864, 3904): The return dais: a disc of black glass, shown once the Fire Sleeper is awake (m38.fire); an exit preset to D7's entrance:p1_return. No walk back.
- `poi:ember_cache` at (-4736, -4352): The ember cache (treasure 6, a fire trap): a fire-walker's iron box by his burnt camp.
- `poi:camp` at (-3968, -4736): The fire-walker's camp: a burnt bedroll, a kettle and a note: 'Day 3. The boots work. The feet do not.' (ours) A find: Fire Resistance potions.
- `landmark:lava_fall` at (-6016, 1536): A lava fall pouring down the crater wall beside the Glass Shelf.
- `poi:spire_glass` at (4480, 1920): A seam of red crystal in a spire: hit with a weapon, it rings ('The spire hums. Nothing else happens.'); the first time, a shard: a red gem (a find).

## Figures (`measure.json`)

| Figure | Target | Plan |
| --- | --- | --- |
| Size | MAPS §3: S-M dungeon scale (S 7-20 M units, M 30-90) | room 26 x 26 cells; floors span 21.4 x 21.2 cells; **50.9 M units** walkable |
| Lava lake | the element's ground | 90.0 M units, 64 % of the basin; farthest from a way out 3,396 (90 % within 1,703) |
| Placed hostiles | MAPS §0: 30 a plane | **30** (27 in 10 groups of 2-3, and the test's 3) |
| Levels | 55-70, the guardian 75 | 55-75, mean 59.8 |
| Kill XP per member | D-58: 31.54k (MAPS 31.0k a plane) | **31.54k** (+1.7 % on MAPS); XP = L(L+10) as D5 |
| First fight | 1,500-4,000 from the arrival | **2,555** |
| Quiet arrival | no spawns on the landing | 0 on it; nearest group to the way up 3,954 |
| Points of interest | C8: 10-12 | **10** (D-20 census, merged within 400); spacing median 2,589 (859-4,985) |
| Chests | C8: 2 (S 0-3) | **2**, treasure 6, and one find |
| Hazard cells | the source's nine | 9, 0 on the critical path, 0 on a link, 0 in the arena |
| P-2 no bypass | every lip at least 192 | lowest lip **321**; no higher floor within 1,024: holds ("D-58 applied") |
| Walk | - | 15,827 (arrival -> test -> sleeper -> way out) |
| Textures | Dungeon S cap 30 (4 new) | about 16, 2 new |

Hostiles by row:

- 11 x Lesser Fire Elemental (11620)
- 5 x Lava Golem (11593)
- 9 x Fire Elemental (11621)
- 4 x Fire Blower (11622)
- 1 x Sleeper's Guardian of Fire (11623)

## Hazards and never stuck

- **Vents** (question 2): The source's nine vent squares: glowing cracks in the crust (a small floor face each). Stepping on one: one time in three 50 fire damage to each member, 'A vent flares!' (resistance applies).
- **Lava** (D-58 Q1): walkable and burning; crust banks and ramps everywhere but the Sleeper's Hall and its bridge (P-2); 90 % of the lava within 1,703 of a bank, the farthest 3,396 (about 9 s walking; the lava behind the Sleeper's Hall, which the spire's rock walls off from the hall).
- **No falls**: the crater wall closes the room.
- **Never stuck**: the way up at the arrival is always open; Town Portal and Lloyd's Beacon work (no no_teleport); the test can be left and taken up again; the gate stays open once passed.

## Ways in and out (the corner contract)

- **In:** D7's north-west corner (Sky A1), `m38.corner_fire` ('What do you seek?' 'Fire'), drops the party to `entrance:d7_fall` here (common question C2: no falling damage).
- **Out, always:** the way up at the arrival, an exit preset, to D7's `entrance:p1_return`.
- **Out, after the sleeper:** the return dais in the chamber (condition m38.fire), the same arrival.
- corners.yml's `default_way_out` (the lead, D-58 C5) says this; Town Portal and Lloyd's Beacon work, Fly is not cast.

## Textures (shipped first; L3 confirms)

- `lavtyl`: MM8 lava (D6's; the engine burns a floor of this name); the lava lake.
- `gcav2flr`: MM8 Plane of Fire's black lava rock; crust causeways and shelves.
- `6voltyl`: MM6 Gharik's Forge volcanic floor; the shelves round the statue and the vents.
- `vlcwl1`: MM6 volcanic wall with lava seams; the crater cliffs.
- `vlcwl3a`: MM6 dark volcanic rock; basalt spires and the Crucible's rise.
- `gnecwal1`: MM8 Plane of Fire's crackled dark stone; the Sleeper's Hall walls.
- `gcav1flr`: MM8 Plane of Fire's dark rock floor; the Sleeper's Hall floor.
- `orfyrlga`: MM6 molten lava; the two lava falls and the pit.
- `xcorefire`: XD-19's fire core (A7); the sleeper couch's glow panel.
- new `xpfvent`: a crack of glowing lava in black crust, one per vent face (the source's nine vents).
- new `xpfglass`: obsidian: black volcanic glass with red depths, the Crucible's ring and the gate.

About 16 distinct textures: class S (cap 30, at most 4 new; D-58 C1). The new ones are made at L3 through xtex.py and registered by the lead.

## Original lines

- 'Fire Sleeper' and the three sleeper answers (aaze0025:0, 2, 7-8): m38.sleeper_fire.
- 'Plaque' and the Step text (aaze0025:3-4): m38.plaque_fire.
- 'Accept the test of Fire?' (aaze0025:6): m38.test_fire.
- 'Chest' (aaze0025:5): the test's chest's name.

## Hooks placed

- A3's, by name: `m38.plaque_fire` (the statue), `m38.test_fire` (the pedestal; yes shows the guardians), `m38.sleeper_fire` (the couch, every click; sets m38.fire, qbit 111760).
- The test (P-1, C3): each guardian's death event calls `Xeen.planeTestCheck("fire", <group>)` (xeen_common.lua), which runs `m38.test_fire_passed` once (sets m38.fire_test, qbit 111764); the load event reads the qbit.
- The ways out (C5): `m38.way_up_fire` and `m38.dais_fire`, the lines the two `exit` presets' windows mean (nothing to call).
- The hazard and the places (`source/npcs/planes.yml`): `planes.vent` on the nine plates, the device, the find's note and the gem device by their names there.
- In: D7's `m38.corner_fire`, then `Xeen.toPlane("fire")` to `Xeen.PlaneArrivals.fire` = `entrance:d7_fall` here.

## MU-4 concept

`planes_concepts.py p1`: one `codex exec`, first attempt, 65 s; raw `planes/raw/p1_arrival_v1.png` with its prompt (.txt) and log (.log). References: the arrival blockout, D6's lava concept (this world's lava), MM6's `orfyrlga` and MM8's `gcav2flr`. It shows the Cinder Shelf's cracked crust, the causeway left to the statue of flame on its plinth, the lava lake with crust plates and spurts, the hall's ring of columns at the foot of the tallest spire, the Crucible's black ring right of it, the basalt columns right and a lava fall in the crater wall. Against the plan (the plan wins at L2-L3): the crater wall reads as cut slabs (the blockout's), L3 makes it ragged cliffs; the statue stands nearer and larger than drawn (about 3,700 away); two small gold boxes are the blockout's pedestal and couch, not props; the Crucible's ring is lower than the plan's rise.

## The questions and D-58's answers

Common to all four planes (asked once, here; P2-P4 refer to them):

C1. **The plane as a map: size and form**
   - Options:
     - (a) One compact open-air BLV per plane (X9's and P5's route), a room of 26 x 26 cells with about 45-50 M units of walkable floor: a small M dungeon by floor and monsters, one element's form each (Fire a lava crater, Air islands in open sky, Earth the `xeen_plane_earth` bowl, Water a flooded hall).
     - (b) Smaller, S class (at most 20 M units, 15 sectors): the test and the chamber only.
     - (c) MM8's way: whole ODMs (1 ODM each).
   - Evidence: MAPS §3: 'S-M dungeon scale each; MM8's planes were whole ODMs; these are deliberately small'. The source's planes are 16 x 16 squares each, the same as a dungeon level. 30 monsters sit between S (15-30) and M (45-75).
   - Proposed default (drawn): (a)
   - Depends on it: L2 geometry, the texture class (S cap 30), the walking length.
   - **Decided (D-58):** (a) One compact open-air BLV per plane, 26 x 26 cells, about 44-51 M walkable; Dungeon S for textures (cap 30, at most 4 new).
C2. **The arrival from D7: falling damage**
   - Options:
     - (a) None: the party lands standing on the arrival shelf (`entrance:d7_fall`); the drop is told by D7's corner text ('You step off.').
     - (b) A short real fall: the party appears 768 above the shelf and takes the engine's falling damage (Feather Fall none), D-6.2's 'a third of HP at most' rule.
     - (c) Damage by script, one line.
   - Evidence: The source's corner square moves the party to the plane's run position with no damage. D-6.2 and D-56 test every sky fall for survivability; a fall into an unknown arena would add a test per plane.
   - Proposed default (drawn): (a)
   - Depends on it: A3's corner hooks (m38.corner_x) and D7's corner script; the plane's arrival test.
   - **Decided (D-58):** (a) No falling damage: the party lands standing on the arrival shelf after D7's 'You step off.' (A3's m38.corner_<element> moves the party directly, without keepHeight: Xeen.toPlane).
C3. **What the test of the element is**
   - Options:
     - (a) 'Accept the test of X?' (A3's m38.test_x) raises the guardians in the arena: the Sleeper's Guardian (75) and two Greater elementals (70), the source's own beast; killing the three passes the test (a map variable) and opens the gate to the sleeper's chamber. Declining does nothing.
     - (b) The source's test: accepting costs every member 2,500 damage of the element (resistance applies; at party level 56-60 that kills); the guardians stand in the arena from the start.
     - (c) (a), and the guardians also stand in the arena before the test (no click needed).
   - Evidence: Source maze0025/26: the test square asks 'Accept the test of Fire?' and deals 2,500 fire (2,500 electric on Air), setting a flag that stops the chest burning. m38.yml: 'Yes calls the hook, the map opens the test (its arena and guardians)'. MAPS: 'sleepers' guardians 75'.
   - Proposed default (drawn): (a)
   - Depends on it: A3's m38.test_x text and the passed flag; A2's guardian rows; the arena's wiring.
   - **Decided (D-58):** (a) 'Accept the test of X?' raises the Sleeper's Guardian (75) and two greater elementals (70) from the pit, a hidden group; when all three are dead the test is passed and its qbit set (P-1); declining does nothing; a party that leaves mid-fight finds the guardians still shown on return.
C4. **What the passed test opens**
   - Options:
     - (a) The gate to the sleeper's chamber, where the couch and the test's chest stand: the test is the way to the sleeper.
     - (b) The chest only, as the source (its chest burns until the test is passed); the sleeper's chamber is open from the start.
     - (c) Both separately: the chamber open, the chest sealed in the arena until the test.
   - Evidence: The source's sleeper does not check the test; only the chest does. The family names the guardians 'Sleeper's Guardian'. m38.sleeper_x needs only Chosen One and M37's four reflectors.
   - Proposed default (drawn): (a): the guardian guards the sleeper; one gate, no burning chest to explain.
   - Depends on it: The chamber gate (a door with a state), A3 (no new hook: the gate reads the map variable).
   - **Decided (D-58):** (a) The gate to the sleeper's chamber, where the couch, the test's chest and the dais are.
C5. **The way out (corners.yml default_way_out)**
   - Options:
     - (a) Two ways, both to D7's `entrance:pN_return` by the corner's rest stop: the way up at the arrival, always open (the source's exit square, a fall back to its Skyroad corner), and the sleeper's return dais, shown once the sleeper is awake (no walk back).
     - (b) The return dais only, after the sleeper (the corners.yml default as written); Town Portal and Lloyd's Beacon before.
     - (c) The way up only (the source).
   - Evidence: maze0025 (13,2) and maze0026 (2,2) are fall squares to Skyroad A1 (3,13) and F1 (12,13): the source's way back is always open. A party that cannot pass the test must not be stuck.
   - Proposed default (drawn): (a)
   - Depends on it: D7's p1_return ... p4_return arrivals; one exit preset per way (D-24).
   - **Decided (D-58):** (a) Two ways out, both `exit` presets (D-24) to D7's entrance:pN_return: the way up at the arrival, always open, and the return dais after the sleeper. Town Portal and Lloyd's Beacon work; Fly is not cast.
C6. **The guardians and the greater elementals: rows and names**
   - Options:
     - (a) One family per element: A2 adds Air, Earth and Water rows for B (62), C (70) and the Sleeper's Guardian (75) beside Fire's 11621-11623 (11624-11626 exist as XD-19's lesser elementals at 55), named as the family ('Greater Air Elemental').
     - (b) As (a), with the source's names on the C rows: Fire Blower, Whirlwind, Earth Blaster, Tidal Terror.
     - (c) One neutral Sleeper's Guardian row for all four planes, skinned by element.
   - Evidence: monsters.yml: the family is Fire-typed (11620-11623); XD-19's lesser elementals of the other three elements exist (D-47). XEEN_SYSTEMS: the source's planes hold eight of one greater elemental each.
   - Proposed default (drawn): (b): the names are the source's and read well in the Xeen voice.
   - Depends on it: A2's rows; S's skins (MM6's air, MM7's water and earth elementals as in D-47).
   - **Decided (D-58):** (b) Lesser X Elemental (55), X Elemental (62), the source's name on the 70s (Fire Blower, Whirlwind, Earth Blaster, Tidal Terror), Sleeper's Guardian of X (75); nine new rows (A2), Fire's 11620-11623 renamed.
C7. **The sleepers and the statues: what stands there**
   - Options:
     - (a) One sleeper model for all four (a giant of the element lying in an Ancient stasis couch, its element in the couch's glow), four skins; one statue model per element on a common plinth with the plaque (S).
     - (b) The sleeper as a peaceful placed figure (an A2 row, unkillable as D-51) on a plain couch.
     - (c) Decorations from shipped MM6-MM8 statues only.
   - Evidence: Source: the same object sprite (46) for all four sleepers and (40) for all four statues; the sleepers speak of a 'Grunfeld field generator' (Ancient technology).
   - Proposed default (drawn): (a)
   - Depends on it: S models (4 statues, 1 sleeper with 4 skins, the couch, the pedestal, the dais).
   - **Decided (D-58):** (a) One sleeper and one couch with four element skins; four statues from the elemental models on one plinth with a plaque; the pedestal and the dais P5's disc in the element's stone (S; no stand-ins at L4).
C8. **Points of interest and chests per plane**
   - Options:
     - (a) The sparse-special band: 10-12 POIs (MAP_CRAFT §6: sparse special maps at least 10) and 2 chests (S's 0-3; MM8's planes 0-2): the test's chest and one trapped cache, each with a reason, plus one find (a camp, a wreck) and one buff device.
     - (b) The source: the test, the statue, the sleeper and one chest (4-5 POIs, 1 chest).
     - (c) MM8's planes: 0-3 POIs, 0-2 chests.
   - Evidence: MM8 elemf 3 POIs and 2 chests, elema 1 and 1, elemw 0 and 0 (MAP_CRAFT_CALIBRATION); the source has one chest a plane.
   - Proposed default (drawn): (a)
   - Depends on it: The census in totals; A2 treasure 6.
   - **Decided (D-58):** (a) 10-12 POIs and 2 chests at treasure 6 (the test's chest and one trapped cache), one find and one buff device.

P1's own:

Q1. **The lava: how much it hurts and how the party gets out**
   - Options:
     - (a) The lava is the floor: `lavtyl` faces burn as MM's lava (fire damage while standing in it, Levitate none); every causeway and shelf edge within 64 of the lava has a crust bank to walk out; the raised shelves have ramps.
     - (b) Lava kills (a death trigger, as the world rim).
     - (c) Lava is decoration under invisible walls.
   - Evidence: D-40/D6: `lavtyl`, never water, burns. The engine burns a floor face named lava*/lavtyl (IndoorMovementController) and Levitate lifts the party (as MM8).
   - Proposed default (drawn): (a)
   - Depends on it: L2 banks and ramps; the measure lava_bank_max.
   - **Decided (D-58):** (a) Walkable `lavtyl` that burns as MM lava does: crust banks within 64 of every lava edge, ramps up every shelf; P-2 holds.
Q2. **The vents**
   - Options:
     - (a) Nine small floor faces with the source's rule (1 in 3: 50 fire to each member), marked by a glowing crack texture; five in the Vent Field, four on the loops; none on the critical causeways.
     - (b) Vents erupt on a timer (a set piece every few seconds) with a visible spurt.
     - (c) No vents.
   - Evidence: maze0025: nine squares call one event: random 1-3, on 3 Damage 50 fire.
   - Proposed default (drawn): (a)
   - Depends on it: A3's line; A1's floor-event check; the new texture xpfvent.
   - **Decided (D-58):** (a) Nine small PressurePlate faces, the source's rule: one time in three 50 fire to each member, resistance applies, 'A vent flares!'; none on the critical path; marked by `xpfvent` (A3 the event, A6 the faces).
Q3. **Sky**
   - Options:
     - (a) MM8's shipped `plane_fire` (engine library) by name.
     - (b) A new Xeen preset `xeen_plane_fire` (A6): plane_fire with a lower ember glow and slow-drifting ash clouds.
     - (c) The Darkside amber day (xeendark1).
   - Evidence: WORLD_DESIGN §4: the planes' themes are plane_fire, plane_air, underwater and a new earth preset. plane_fire has no sun and no stars: a timeless plane.
   - Proposed default (drawn): (a): shipped and cheapest to reverse.
   - Depends on it: atmosphere.yml; A6's sky file.
   - **Decided (D-58):** (a) The shipped `plane_fire`.

## Requests (for the orchestrator to relay; D-58 state)

- **A2** (all four planes): landed 2026-11-21: map_stats rows 9115-9118 as D-58's ROWS, the nine C6 rows (Air 11700-11702, Water 11710-11712, Earth 11720-11722) and the Fire family's new names (11620-11623); nothing more asked but treasure 6 for the two chests a plane.
- **A3** (all four planes): written by the sixteenth session's start: m38.test_<element>_passed (qbits 111764-111767, through Xeen.planeTestCheck), m38.way_up_<element> and m38.dais_<element> (the exit presets' lines), Xeen.toPlane and Xeen.PlaneArrivals (C2), SkyFalls `p2`, and source/npcs/planes.yml (hazards, devices, finds, notes); still asked: ORIGINAL_LINES rows aaze0025:0, 2-8 and aaze0026-0028:0-7.
- **S** (all four planes): C7: one sleeper and one couch with four element skins, four statues from the elemental models on one plinth with a plaque, the pedestal and the dais (P5's disc in each element's stone), the way-up effects, the per-plane devices; the nine elemental tier skins (C6). Until they land, L4 builds their spots by name and marks them blocked (no stand-ins).
- **D7** (all four planes): the four corners' drops land on entrance:d7_fall here (Xeen.PlaneArrivals, A3); both ways out land on D7's entrance:pN_return by the corner's rest stop (corners.yml), facing the road.
- **A1** (all four planes): confirm only (D-58 relays 1, 2 and 4): hidden placed actors shown mid-visit in an open-air BLV, PressurePlate faces in an open-air sector, water volumes, constant currents and swimmers under an open-air BLV's outdoor view.
- **O** (all four planes): openAirMaps for P1-P4 at install; MAPS §0 and §3's P rows as D-58's ROWS AND NUMBERS.
- **A2**: row 9115: environment mountains, music 10; Lava Golem 11593 used at 55 (5 placed).
- **A6**: new textures xpfvent and xpfglass (Q2), registered in source/textures.yml; plane_fire or a Xeen preset (Q3).
- **S**: the statue of Fire; the Ember Font (a basin of liquid fire); the fire-walker's camp (bedroll, kettle).

## Blocked

Nothing blocks L1 or L2: A2's map_stats row 9115 and the element rows (C6) landed 2026-11-21. L4's walks from assets_dev wait on S's sleeper, couch, statue, pedestal and dais (C7; spots built by name, blocked) and D7's install (its entrance:p1_return). A3's hooks are written (m38.test_fire_passed, way_up, dais, planes.yml).
