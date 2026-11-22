# P4 Plane of Water of Xeen: L1 plan (MU-3, MU-4), approved with changes (D-58)

A6's planes sub-agent, 2026-11-21. A plan only: no geometry. Decider D-58 (`devdocs/xeen/briefs/d7/L1/D58_DECISION.md`) approved the board (`level_generation/xeen_art/phase6/planes/board_p34.png`) with changes; the sixteenth session applied them to the design data and rewrote this folder ("D-58 applied" below). Where this plan and D-58 differ, D-58 wins.

`level_generation/xeen_art/phase6/planes_design.py` holds the four planes' design as data (one family: the same skeleton, one element each). `planes_render.py` draws and measures it (plan SVG and PNG, the arrival blockout, `measure.json`), `planes_brief.py` writes this folder, `planes_concepts.py` paints one `codex exec` concept, `board_planes.py` boards the pair; `planes_run.py` runs them (Python under an 8 GB cgroup cap) and `oymap fmt`, `fmt --check` and `validate --assets assets_dev`.

Validation: `fmt --check` clean, `validate` no issues (see the run log in `level_generation/xeen_art/phase6/planes/run_p34.log`).

## D-58 applied

| Change | What was done | Figure |
| --- | --- | --- |
| P-1 the test in a qbit | the gate's link, goal:test, set:test and state:test_passed read or give m38_water_test; the load event reads it: gate open, guardians hidden, pit quiet (A3's m38.test_water_passed sets it) | qbit 111767 |
| P-2 no bypass | measured round The Sleeper's Grotto and the gate's link beyond the gate: the sea lip 192; rim lip 1,400; gate flank lip 384; the gate between two broken columns of the court's ring either side of the Veil's head (384 high, 512 along the rim); the nearest higher floor (arena, 128) is 2,831 away, so no drop reaches it | lowest lip 192 (>= 192): holds |
| P-3 / C6 rows | names by the C6 pattern; ids where they exist (12 Lesser Water Elemental (11625), 7 Water Elemental (11710), 5 Great Octopod (11471), 5 Tidal Terror (11711), 1 Sleeper's Guardian of Water (11712)) | 30 hostiles, 32.38k per member (D-58 32.38k) |
| C2 arrival | lands standing at entrance:d7_fall (Xeen.PlaneArrivals.water, A3) | (3968, 3968), floor 0 |
| C3 the test | the guardians a hidden group at the pit, shown by m38.test_water; their death events call Xeen.planeTestCheck | 1 x Sleeper's Guardian of Water, 2 x Tidal Terror |
| C4 the gate | the colonnade to the chamber opens on the qbit | one gate |
| C5 two ways out | the way up and the dais, both `exit` presets to D7's entrance:p4_return (lines m38.way_up_water, m38.dais_water) | always open / after the sleeper |
| C7 S's pieces | the sleeper, couch, statue, pedestal and dais are S's; L4 builds their spots by name and marks them blocked | no stand-ins |
| C8 POIs and chests | the test's chest and one trapped cache at treasure 6, one find, one buff device (the gem device stays as drawn: its one-time gem is planes.yml's) | 10 POIs, 2 chests |
| Q1 water | MM9 water volumes; edge volumes with a constant inward `current` 256 (no radial current); Water Walk does nothing on a volume (recorded, accepted) | nothing critical swum |
| Q2 diving | none anywhere; the wreck's hold half flooded and waded | 0 dives |
| Q3 sky | `xeen_plane_water` (the lead's preset in Xeen's sky.yml) | atmosphere.yml |
| Q4 octopods | two swimmer groups, homes moved where needed | sea_octopods_e: 4,537 from the landing, 5,196 from the arena, 5,717 from the chamber; sea_octopods_n: 3,973 from the landing, 2,660 from the arena, 7,725 from the chamber |
| Concept corrections (L3) | the sky is an open sky (Q3), not an underwater ceiling; the Grotto is at the plan's scale; the statue stands in the middle of its forecourt | L3 |
| ROWS | map_stats 9118: encounter 0, treasure 6, lock 15, trap 8, perception 8, refill 672, music 7, UNDERWATER | project.yml |
| Textures | `xpwspray`, `xpwcoral`, `xpwhull` new (Dungeon S, cap 30) | about 16 |

## The source

MM5 maze 28, the Elemental Plane of Water (`dark/aaze0028`, 16 x 16, every square water; decoded, nothing copied):

- the run position (9,9); the statue and its plaque (8,8);
- the test (4,11): 'Accept the test of Water?'; yes costs 2,500 cold damage and sets a flag;
- the chest (9,1): 250 cold unless the flag is set; gold and three items;
- the Water Sleeper (3,3), the same three answers;
- nine squares of freezing waves: one time in three 50 cold damage;
- eight Tidal Terrors (the greater water elemental);
- the exit (13,13): a fall back to Skyroad A1 (map 89) at (2,13), not A4 (the source's own oddity; corners.yml returns the party to its own corner).

## The form

**A drowned temple in a shallow sea.** Water is a sea with a drowned temple standing in it: the tops of its walls and colonnades are the paths, the courts between them are flooded basins the party swims across (MM9's water volumes: swimming at the surface costs no breath), and the open sea all round runs to a fog horizon with a current that carries swimmers back. The source's plane is all water; MM8's elemw is a sea bed.

Room 26 x 26 cells (13,312 a side), north up, x east, y north, the middle at (0, 0); floors over the arrival (0).

## The walk

| Along | Where | What |
| ---: | --- | --- |
| 0 | The Spray Terrace (0) | Arrival `entrance:d7_fall` at (3968, 3968), facing sw; the way up at (4992, 4864). Quiet. |
| 1,508 | | The first fight (`pop:reef_north`), 3,291 from the arrival, 2,925 off the walk. |
| 4,817 | The Sea Statue (32) | The statue and its plaque (m38.plaque_water). |
| 7,891 | The Whirlpool Court (128) | The pedestal: 'Accept the test of Water?' (m38.test_water); the guardians rise. |
| 10,835 | | The sleeper's gate (open on the passed test). |
| 15,231 | The Sleeper's Grotto (192) | The Water Sleeper (m38.sleeper_water); the test's chest. |
| 16,206 | | The return dais (after the sleeper) to D7's entrance:p4_return. |

Legs: arrival to the test 7,891; the test to the sleeper 7,340; the sleeper to the way out 975 (16,206 in all, about 42 s walking).

Spaces:

- **The Spray Terrace** (`room:landing`) at (4224, 4224), 2,560 x 2,304, floor 0: a terrace of green-veined marble, the waterspout at its corner. Arrival from D7's south-west corner (entrance:d7_fall) and the way up (the waterspout). Quiet.
- **The Sea Statue** (`room:statue`) at (256, 768), 2,560 x 2,560, floor 32: the temple's drowned forecourt, the statue of Water rising from a fountain basin. The statue and its plaque (m38.plaque_water, Step Four); the Drowned Bell; the walks part here.
- **The Coral Garden** (`room:reef`) at (4352, -512), 2,304 x 2,816, floor 32: a terrace grown over with coral and shells, tide pools in its stone. The Tide Pool (a device); the east loop.
- **The Wreck** (`room:wreck`) at (640, -4224), 2,560 x 2,304, floor 0: the temple's south court, a sailing ship wrecked across it, its hold half flooded. The source's chest corner: the ship's strongbox in the hold and its log.
- **The Whirlpool Court** (`room:arena`) at (-4096, 1280), 3,328 x 3,072, floor 128: a round court ringed by broken columns round a pool where the water turns. The test of Water: the pedestal at the east gate asks 'Accept the test of Water?'; the guardians rise from the whirlpool. The Veil's colonnade leaves at the south.
- **The Sleeper's Grotto** (`room:chamber`) at (-4096, -4224), 2,560 x 2,304, floor 192: a grotto under a sea arch, its floor a raised shelf of shell and stone. The Water Sleeper on his couch (m38.sleeper_water); the test's chest; the return dais (after the sleeper wakes).

Places:

- `entrance:d7_fall` at (3968, 3968): Arrival from D7's south-west corner: on the Spray Terrace, facing south-west over the drowned temple.
- `exit:way_up` at (4992, 4864): The waterspout: a column of water rising from the sea into the sky. An exit preset ('Ride the spout back to the Skyroads?'), always open, to D7's entrance:p4_return (the source's (13,13), a fall back to the Skyroads).
- `poi:statue` at (256, 896): The statue of Water: a woman of green stone pouring a jar into the fountain basin at her feet. A3's m38.plaque_water: 'A message at the base of the statue reads: Step Four: Travel to the shrine on the Cloud above Darkstone Tower.' (aaze0028:2-3)
- `poi:bell` at (1152, -128): The Drowned Bell: a temple bell half under the water on a fallen frame. Clicked: it tolls under the waves; the first time, a find in its mouth: an emerald.
- `poi:tide_pool` at (4864, -128): The Tide Pool: a clear pool in the coral. Drunk from: +20 Water resistance for a day (once a day; 'The water is cool and refreshing.', the stock line, for once true).
- `poi:test` at (-2688, 1280): The test pedestal at the Whirlpool Court's east gate: 'Accept the test of Water?' (aaze0028:5). Yes calls A3's m38.test_water; the map raises the guardians from the whirlpool (set:test).
- `landmark:whirlpool` at (-4096, 1280): The whirlpool: a pool at the court's middle where the water turns, and the guardians rise.
- `gate:sleeper` at (-4096, -256): The Veil: a falling sheet of water across the colonnade's head, stilled once the test is passed (state:test_passed).
- `poi:sleeper` at (-4480, -4608): The Water Sleeper on his couch in the grotto: A3's m38.sleeper_water, three states (not Chosen; 'Awaiting Grunfeld field activation.'; awake, award 415, 10,500 XP).
- `poi:test_chest` at (-3200, -4864): The test's chest (treasure 6): the source's chest, now in the grotto the test opens.
- `exit:dais` at (-4864, -3712): The return dais: a disc of green-veined marble, shown once the Water Sleeper is awake (m38.water); an exit preset to D7's entrance:p4_return.
- `poi:wreck_cache` at (1280, -4736): The ship's strongbox (treasure 6, a cold trap) in the half-flooded hold, waded to (question 2).
- `poi:log` at (-128, -3840): The ship's log on the wreck's deck: 'Day 40. Still no land. Day 41. Found land. It was this.' (ours) A find: Water Resistance potions.

## Figures (`measure.json`)

| Figure | Target | Plan |
| --- | --- | --- |
| Size | MAPS §3: S-M dungeon scale (S 7-20 M units, M 30-90) | room 26 x 26 cells; floors span 21.9 x 21.0 cells; **43.7 M units** walkable |
| Sea | the element's ground | 97.2 M units, 69 % of the basin; farthest from a way out 5,432 (90 % within 3,605) |
| Placed hostiles | MAPS §0: 30 a plane | **30** (27 in 10 groups of 2-3, and the test's 3) |
| Levels | 55-70, the guardian 75 | 55-75, mean 60.6 |
| Kill XP per member | D-58: 32.38k (MAPS 31.0k a plane) | **32.38k** (+4.4 % on MAPS); XP = L(L+10) as D5 |
| First fight | 1,500-4,000 from the arrival | **3,291** |
| Quiet arrival | no spawns on the landing | 0 on it; nearest group to the way up 4,104 |
| Points of interest | C8: 10-12 | **10** (D-20 census, merged within 400); spacing median 1,669 (975-4,994) |
| Chests | C8: 2 (S 0-3) | **2**, treasure 6, and one find |
| Hazard cells | the source's nine | 9, 0 on the critical path, 0 on a link, 2 in the arena |
| P-2 no bypass | every lip at least 192 | lowest lip **192**; no higher floor within 1,024: holds ("D-58 applied") |
| Walk | - | 16,206 (arrival -> test -> sleeper -> way out) |
| Textures | Dungeon S cap 30 (4 new) | about 16, 3 new |

Hostiles by row:

- 12 x Lesser Water Elemental (11625)
- 7 x Water Elemental (11710)
- 5 x Great Octopod (11471)
- 5 x Tidal Terror (11711)
- 1 x Sleeper's Guardian of Water (11712)

## Hazards and never stuck

- **Waves** (the source's rule, as P1's Q2 (a)): The source's nine squares of freezing waves: wet stone where spray breaks over the walks (a small floor face each). Stepping on one: one time in three 50 cold damage to each member, 'A freezing wave breaks over you!' (resistance applies).
- **Sea** (question 1): MM9's water rules (devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md, already in the engine): surface swimming free, breath 15 s under, drowning 1/6 of maximum HP every 2 s; steps out along every walk and terrace; the walls of the Whirlpool Court and the Grotto stand 192-256 out of the water with no steps, so the test cannot be bypassed (P-2); past the stacks, edge volumes each with a constant inward `current` of 256 push swimmers back (the radial current is open engine work, not used). Nothing on the critical path needs swimming; no diving anywhere (Q2); Water Walk does nothing on a volume yet (recorded, accepted). The farthest point is 5,432 from a way out.
- **Never stuck**: the way up at the arrival is always open; Town Portal and Lloyd's Beacon work (no no_teleport); the test can be left and taken up again; the gate stays open once passed.

## Ways in and out (the corner contract)

- **In:** D7's south-west corner (Sky A4), `m38.corner_water` ('What do you seek?' 'Water'), drops the party to `entrance:d7_fall` here (common question C2: no falling damage).
- **Out, always:** the way up at the arrival, an exit preset, to D7's `entrance:p4_return`.
- **Out, after the sleeper:** the return dais in the chamber (condition m38.water), the same arrival.
- corners.yml's `default_way_out` (the lead, D-58 C5) says this; Town Portal and Lloyd's Beacon work, Fly is not cast.

## Textures (shipped first; L3 confirms)

- `gtempw1`: MM8 pale marble (Prison of the Lord of Fire's family); the temple walls and walks.
- `gtempflr`: MM8 blue-grey flags; the courts and terraces.
- `gtemprf`: MM8 gold-blue mosaic; the Whirlpool Court floor ring (once per face).
- `gtempw2`: MM8 marble panel; the Grotto shelf (once per face).
- `7wtrtyl`: MM7 water; the sea surface faces.
- `gwspotwl`: MM8's blue-grey rough rock; the sea stacks and the grotto arch.
- `cdb`: MM8 Plane of Air's brick; the wreck court walls.
- `xcorewater`: XD-19's water core (A7); the sleeper couch's glow panel.
- new `xpwspray`: wet marble under breaking spray, one per wave face (the source's nine).
- new `xpwcoral`: coral and shells grown over marble (the Coral Garden), seamless.
- new `xpwhull`: the wrecked ship's weathered planking (shipped ship planks first if one fits).

About 16 distinct textures: class S (cap 30, at most 4 new; D-58 C1). The new ones are made at L3 through xtex.py and registered by the lead.

## Original lines

- 'Water Sleeper' and the three sleeper answers (aaze0028:0-1, 6-7): m38.sleeper_water.
- 'Plaque' and the Step text (aaze0028:2-3): m38.plaque_water.
- 'Accept the test of Water?' (aaze0028:5): m38.test_water.
- 'Chest' (aaze0028:4): the test's chest's name.

## Hooks placed

- A3's, by name: `m38.plaque_water` (the statue), `m38.test_water` (the pedestal; yes shows the guardians), `m38.sleeper_water` (the couch, every click; sets m38.water, qbit 111763).
- The test (P-1, C3): each guardian's death event calls `Xeen.planeTestCheck("water", <group>)` (xeen_common.lua), which runs `m38.test_water_passed` once (sets m38.water_test, qbit 111767); the load event reads the qbit.
- The ways out (C5): `m38.way_up_water` and `m38.dais_water`, the lines the two `exit` presets' windows mean (nothing to call).
- The hazard and the places (`source/npcs/planes.yml`): `planes.wave` on the nine plates, the device, the find's note and the gem device by their names there.
- In: D7's `m38.corner_water`, then `Xeen.toPlane("water")` to `Xeen.PlaneArrivals.water` = `entrance:d7_fall` here.

## MU-4 concept

`planes_concepts.py p4`: one `codex exec`, first attempt, 59 s; raw `planes/raw/p4_arrival_v1.png` with its prompt and log. References: the arrival blockout, X9's approved concept (light and stone), MM8's `gtempw1` and `gtempflr`. It shows the colonnade walk with steps down to clear green water on both sides, the statue of Water pouring her jar into the fountain, the Sleeper's Grotto glowing blue under its arch, the Whirlpool Court's broken columns round a turning pool right, the coral terrace and the wrecked ship left, sea stacks and arches in the mist. Against the plan: the sky is painted as a rippling sea surface seen from below (an underwater ceiling): striking, but it says 'under the sea' while the party swims at a surface; question 3 decides the preset; the grotto stands nearer and larger than drawn; the statue stands at the walk's end, the plan puts it mid-forecourt.

## The questions and D-58's answers

The common questions C1-C8 are in P1's NOTES (`devdocs/xeen/briefs/p1/L1/NOTES.md`); D-58 took the drawn default on each (C6 (b)).

P4's own:

Q1. **How water works for a party without Water Walk**
   - Options:
     - (a) MM9's water volumes, already in the engine for BLVs: the party swims at the surface with no breath lost, dives at will (breath 15 s, then 1/6 of maximum HP every 2 s), no falling damage into water; steps out at every walk's foot; the outer sea's current carries swimmers back; Water Walk does nothing yet (the engine's open item); nothing on the critical path needs swimming.
     - (b) MM6-MM8's rule: deep water drowns without Water Walk (the outdoor tiles' damage); the party keeps to the walks.
     - (c) The sea as decoration under invisible walls: walks only.
   - Evidence: devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md (done: swim, dive, breath, drowning, current; open: Water Walk on a volume). The source's plane is all water and walkable.
   - Proposed default (drawn): (a)
   - Depends on it: L2 water volumes; A1 only if Water Walk should lift the party onto the sea.
   - **Decided (D-58):** (a) MM9's water volumes: surface swimming free, 15 s of breath under water, then drowning; no falling damage into water; steps out at every walk; the outer sea's push-back from edge volumes with a constant inward current of 256; nothing on the critical path needs swimming; Water Walk does nothing on a volume (recorded, accepted).
Q2. **Diving**
   - Options:
     - (a) No dive anywhere: the wreck's hold is half flooded and waded; diving is only for whoever falls in.
     - (b) One optional dive: the ship's strongbox lies in the flooded hold, 6 s under at most (breath 15 s).
     - (c) The Grotto reached by a dive under the sea arch instead of the Veil.
   - Evidence: MM9's breath is 15 s; drowning is 1/6 HP every 2 s. A plane at party 56-60 can take a short dive; a required one would be the world's first.
   - Proposed default (drawn): (a)
   - Depends on it: The wreck's L2 shape.
   - **Decided (D-58):** (a) No diving anywhere; the wreck's hold is half flooded and waded.
Q3. **Sky (no shipped plane_water)**
   - Options:
     - (a) A new Xeen preset `xeen_plane_water` (A6, data only, after approval): sea-green zenith, aquamarine horizon, no sun disc, a bright diffuse light, slow caustic cloud, below_horizon sky.
     - (b) The engine's `underwater` (no sky drawn, flat fog): reads as the sea bed, at odds with swimming at a surface.
     - (c) Shipped `plane_air` (blue open sky).
   - Evidence: WORLD_DESIGN §4 names `underwater` for the water plane; the engine library has no plane_water; `underwater` draws no sky at all.
   - Proposed default (drawn): (a); (c) until A6 writes it
   - Depends on it: atmosphere.yml; A6's sky file (a new preset).
   - **Decided (D-58):** (a) A new preset `xeen_plane_water` (A6, make_sky.py, data only); plane_air until it lands.
Q4. **Octopods on the Plane of Water**
   - Options:
     - (a) Two groups of Great Octopods (11471, 60, the swimmer profile of D-36) in the open water between the walks: a reason not to swim.
     - (b) Elementals only, as the source (eight Tidal Terrors).
     - (c) Krakens (70) instead.
   - Evidence: monsters.yml: octopods are this world's only swimmers at 50-70; D-36 gave them MM9's swimmer AI.
   - Proposed default (drawn): (a)
   - Depends on it: A2 (the D4 row reused), S (none new).
   - **Decided (D-58):** (a) Two groups of Great Octopods (11471, 60, 5 in all) as swimmers in the volumes, homes at least 1,024 from the arrival terrace, the test's court and the Grotto; fallback D-52's stationary row in the two deepest basins.

## Requests (for the orchestrator to relay; D-58 state)

- **A2**: row 9118: environment underwater, music 7; the Water rows of C6 (62, 70, the guardian 75); Lesser Water Elemental 11625 (12 placed) and Great Octopod 11471 (5 placed, swimmers) used on P4.
- **A6**: the new preset xeen_plane_water (Q3); new textures xpwspray, xpwcoral, xpwhull, registered.
- **S**: the statue of Water in a fountain basin; the Drowned Bell; the wrecked ship (hull, masts, hold); the Whirlpool Court's broken columns; the waterspout effect.
- **A1**: confirm water volumes, their current and the swimmer AI run under an open-air BLV with an outdoor view (MM9's were all roofed or regions).

## Blocked

Nothing blocks L1 or L2: A2's map_stats row 9118 and the element rows (C6) landed 2026-11-21. L4's walks from assets_dev wait on S's sleeper, couch, statue, pedestal and dais (C7; spots built by name, blocked) and D7's install (its entrance:p4_return). A3's hooks are written (m38.test_water_passed, way_up, dais, planes.yml).
