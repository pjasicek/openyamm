# D5 Desert of Doom, L4 (2026-11-21, A6)

The approved L1 (MU-3, board `level_generation/xeen_art/phase5/d5/board_d5.png`) built to L4 with decider D-49
(`../L1/D49_DECISION.md`). The project files here (and L2, L3) are written by `output/studio_cal/d5/tools/gen.py`;
never edit them by hand. Build folder, tools, tours and logs: `output/studio_cal/d5/` (PROGRESS.md lists the commands).

## How it is written

- `gen.py` reads L1's plan, sketch and project (written by `level_generation/xeen_art/phase5/d5_brief.py` with D-49
  applied), A3's hooks with `map: D5` in `data_tables/quest_hooks.yml` (every one wired or the script stops), D4's
  installed x 19 column, D2's installed y 19 row, the shared edge file `edge_d5_d6.json` (y 106-109 to D1's corner,
  D-49 Q6) and the world's decoration bindings (S's boulder, when it exists).
- The land is a function sampled on the 4-cell grid (L1's height points, dunes in the Perishing Sands, the borders
  blended over the last four cells), with every border cell a height point (x 19 = the edge file, x 109 = D4's column,
  y 109 = D2's row falling to D4's corner), terraces (the pyramid's plinth 1,248, Gurodel's shelf 2,688, Bosco's terrace
  2,656, the tower knoll 3,008, the shrine mesa 1,888, the arrivals, the boulder rings, the fountains), the L1's
  cliffs (the rim, the Griffin Cliffs, the mesa) plus the hillside behind the hold and Bosco's crag, and three ridges.
- Doors into dungeons are live only when the BLV is installed, A2's map_stats row names it and its studio sidecar lists
  the door's entrance (`ENTRANCE` in gen.py); until then each shows a short sealed line. The west edge (D6) is built
  behind `D6_LIVE`; the boulders' model behind `BOULDER_LIVE`; AU's beds behind `BEDS`
  (`output/studio_cal/a6/beds/xeen_d5.yml`).

## What was built

- **The Great Pyramid** (DD-15, D-49 Q6 and change 7): 12 x 12 cells at the foot (6,144), 3,600 to the capstone's foot,
  six stacked battered courses (600 high, drawing in 459 a side: about 52.6 degrees, no steps, too steep to walk), each
  512-wide bay one MM6 `egybigb` picture stretched over it (`fit`: large blocks, about two dozen courses up the face, as
  the lead's review asked), a gilded capstone (`xngold6`). No frieze (D-49 allows one; none was needed). Its door at the north face's foot in a porch of `egybiga`:
  two leaves of the lead's `xdpyrdor` (the second mirrored), 448 wide by 384. `m28.door` is the door's condition (the
  Key to the Ancient Pyramid, 12348); with the key: sealed with a line until DD-15 exists. The tomb robbers' camp at
  its south-east corner (a tent, a loot box, bones).
- **The broken travel pyramid** (95, 72) by the road: an Ancient-kit (`xahull`, `gn_mtl01`) truncated pyramid with a
  ruined stub of its apex (broken open), its capstone at its foot (about 330 from its click); both call `obelisks.dark_hoard` (D-49 change 2: one spot).
- **The Parabolic Barrier** (D-49 Q4, change 4): 19 Ancient frames (a `gn_mtl01` foot and an `xaenergy` pylon 1,536
  high) on the bow from the rim at x 46 to the rim at x 100, an `xafield` curtain 1,280 high between them and an unseen
  blocking face 6,000 over the land along the same line (walking and flying). No event, no title, not a POI. Past its
  ends the rim rule (`rim: {cliff_y: 24, fall: death, sides: [north]}`).
- **Gurodel's hold**: a ring of nine standing slabs round the giants' fire (`dec24`), a heap of throwing boulders; behind
  it the hillside with **DD-24's great doors**: a doorway 768 x 512, two leaves of A7's `xdgiantd` (mirrored), into
  DD-24's `entrance:d5_hold` (live). The People: 11083 x3, 11084 x2, 11085 x1 (actors 0-5: the struck timer reads
  them), peaceful, not counted; Gurodel 5452 on 11085 at the fire.
- **Bosco's Hall** (DD-25, sealed): a doorway set into the crag at (61, 46) looking east, a double door of shipped
  `t09a03a` (two leaves, mirrored), two lanterns.
- **The Northern Tower** (DD-08, sealed): five storeys of `hkm1b1` with battlements, one `hkm1elw` window per face on
  the upper storeys, its door two leaves of `hkm1dl` (mirrored), the lead's `xdvowel` lintel once over it;
  `q-d17.tower_door` is the condition (Bosco's key, 113341).
- **DD-18's grate** (101, 102): a doorway in the hills' foot with one grated leaf (`jailc08oq3`); the first click draws the
  bolt (`dd18.d5_grate`, 116121), then the door leads into DD-18's `entrance:d5_grate` (live).
- **The Enchanted Boulders** (D-49 change 1): S's `xeen_boulder` (row 4014, radius 165, height 280: a sandstone rock
  with a weathered bearded face), each at the terrain's height with no offset and facing out of its ring's centre
  (east 88, 16, 304, 232 for boulders 3-6; west 270, 150, 30 for 1, 2, 7). The east ring by the desert road (the sign,
  boulders 3-6: five spots on a 339 circle, 399 apart) and the west ring by the west road (boulders 1, 2, 7: a 230
  circle, 398 apart; about 4,900 from the obelisk, 5,100 from the Last Water): widened in session 24 so the rocks stand
  apart (gaps about 70-100) and each ring stays chained within 400: one spot. Boulders 1-6 call `q-d24.boulder_N` and
  hide themselves once `crumbled_N` is set (and on load); boulder 7 speaks, asks "What am I?" (paladin:
  `q-d24.answer`, else `answer_wrong`) and is hidden after the answer.
- **Devices**: the obelisk (`obelisks.d5`) on its knoll; the Last Water (`d5.last_water`, +2 Luck) by the pool under
  palms; the Shrine of Great Power (a ring of stones and an altar on the mesa; "Will the party pray?" then `d5.shrine`);
  the Fountain of Might (`d5.fountain_might`) under the rim; the Fountain of Energy Resistance (`d5.fountain_energy`)
  at the Barrier's west end; two genie lamps (`Xeen.genieLamp("d5_hills"| "d5_dune", ...)`: the ruined hill shrine and
  the dune crest); the lair's lean-to ("Destroy?" then `d5.lair`); the munchies on two unseen step plates
  (`d5.munchies`, hazards). Three signposts.
- **Chests (6)**: the lair's hoard, the eyrie's satchel (three Griffins placed), the caravan's strongbox at the pan, the
  prospector's pack, the dwarves' strongbox at their abandoned camp, the robbers' loot box.
- **Scatter**: the Quivering Forest's aspens (`tree62c`, `tree63b`, `tree28`), firs at the forest's end, palms at the
  Last Water, rocks and scrub over the desert, the cliffs and the hills, snow weeds on the highlands.
- **Ground**: sand (amber `sand_ripples`), dirt (`dirt_cracked`), snow on the crest; the two roads on the road tile drawn
  as a stony earth track (`soil_stony`, D-49 (7)), the lanes dirt; Darkside rock on the slopes (terrain entry in
  `terrain_materials/world.yml`).
- Sky `xeendark1` (continent 7), no weather, view distance 1.6.
- **Sounds**: AU's beds (`level_generation/sounds/xeen_20261120/review/beds/d5.yml`, D-48): desert wind, the aspens and
  the highland wind as beds (`pan: false`), the Barrier's hum at six points along it and the hold's fire (panning).
- **Edges**: east to D4 (y 80, live; A2's travel rows D4-D5 walked both ways); west to D6 at y 64 (D6 installed at
  01:11, so the edge is open and the sign gone; A2's D5-D6 rows not written yet).

## Monsters (A2's rows)

map_stats 9112 as A2 wrote it (lock 12, trap 6, perception 6, music 6, DESERT; slots Iguanasaurus Dif 3 [2,3] w40,
Roc Dif 2 [1,3] w40, Giant Dif 1 [2,3] w20). Markers: E1 sands 8 and E2 pyramid 7 (lizards), E3 cliffs 11 and E5
Desert of Doom 10 (birds; E5 placed by hand so the D6 arrival's first fight is inside 6,000), E4 the Quivering Forest 11
(wild cyclopes 11080-11082, hostile). Placed: 3 Griffins 11562 at the eyrie (hostile); the People and Gurodel
(peaceful, not counted).

## Measured

| Figure | Target | L4 |
| --- | --- | --- |
| Hostiles at load | 110 | 110 (47 markers = 107 + 3 griffins); the People 6 + Gurodel not counted |
| Kill XP per member | 52.3k (±15 %) | 55.6k (+6.2 %; the markers and placed rows of the L1, unchanged) |
| POIs (D-20 census, chained within 400) | 20-25 (cap 25) | 21 (the L1's 24 counted the boulders' rings and the capstone apart) |
| Chests | 4-10 | 6 |
| Relief inside the box | >= 2,500 | 992-3,648 (2,656) |
| First fight from the edge arrivals | 2,000-6,000 | D4 road 5,205; D6 pass 3,979 |
| 6,000 rule | none over 6,000 | farthest 5,894 (90, 30); 0 tiles over |
| Wild land (more than 1,536 from anything) | <= 0.16 | 0.090 |
| Quiet central land | at least 1/3 | 0.73 |
| Model triangles | | 3,429 |
| Dungeon entrances | 3-6 | 5 (DD-24 and DD-18 live; DD-15, DD-08, DD-25 sealed) |

The behind-the-Barrier strip (L1's `zone:barrier_lee`) is not land in these figures.

**POI spacing** (D-49 change 5): the median of about 6,250 is accepted: 20-25 POIs on about 7,200 land cells cannot
reach a 1,300-2,600 median; the 6,000 rule and the wild-land figure hold (as D-40's line for X7).

**The four-map corner** (D-49 Q6): the installed D1 and D2 disagree at the four-map point (2,176 against 2,496); there is
no crossing there, and it is left as is.

## Tests

- `oymap audit devdocs/xeen/briefs/d5/L4 --assets assets_dev --reach --solve --dressing`: 0 errors, 0 warnings
  (`output/studio_cal/d5/run/audit.txt`).
- `playtest.yml` (`tools/gen_walk.py`, 207 steps) and `playtest_hostility.yml` (`tools/gen_hostility_d5.py`) pass on the
  stage and twice on assets_dev (logs in `output/studio_cal/d5/run/`), the D4 edge both ways included. The D6 edge is
  walked once A2's D5-D6 rows exist (the walk checks `outdoor_travels.txt` itself).
- `oymap audit assets_dev/worlds/xeen/maps/xeen_d5.odm --world xeen --assets assets_dev`: 0 errors.
- Tours: `output/studio_cal/d5/pics/sheet_final.jpg` (18 shots on assets_dev); the stages' `sheet_s1.jpg`, `sheet_s2.jpg`.

## Texture fit exceptions

None.

## Dressing exceptions

None.

## Open items

- **The Barrier's curtain is see-through** (session 15, merge point 23): `translucent: true` on
  `thing:barrier_curtain`, blended by `xafield`'s graded alpha (0.45 in the dark cells, 0.95 on the bright lines;
  `level_generation/xeen_art/field_alpha/field_alpha.py`); the land and the Northern Tower show through it
  (`output/studio_cal/d5/pics/sheet_s15curtain.jpg`). Installed with bake (session 15), walk 2/2, hostility, audit 0.
- **The road still reads dark** on the installed map: the `road` key of D5's terrain entry (soil_stony, lightened) does
  not seem to reach the road tiles; the lead's terrain review.

- **S**: the Enchanted Boulder model (row 4014 reserved): seven spots hold shipped `rock24` until it exists; a rebuild
  takes it by itself. The boulders are not done until swapped.
- **A8**: DD-15 (the green doors, event 1: `m28.door` with the key, then into `entrance:d5_door`) and DD-25 (Bosco's
  door into `entrance:d5_bosco`) live since session 18 (installed with bake 05:53; the walk goes in by both and is set
  down at `entrance:dd15_door` / `entrance:dd25_door`, the dungeons' own ways out). DD-08 (the Northern Tower's door
  with Bosco's key, into `entrance:d5_tower`) live in the reinstall of 06:09 (with bake; merge point 27's peaceful-group
  load event too); the walk goes in and is set down at `entrance:dd08_door`.
  DD-18's `exit:d5_grate` and DD-24's way out still lead nowhere on their side.
- **A2**: the travel rows D5-D6 (D6 is installed).
- The new-game/edge start of the build is `entrance:d6_pass` (the first arrival kind); the respawn and Town Portal
  anchor are `entrance:d4_road`.

## Doors and arrivals for the other lanes

Facing in the game's units (0 east, 512 north, 1024 west, 1536 south).

| Arrival on D5 | X, Y, Z | Facing | For |
| --- | --- | --- | --- |
| `entrance:d4_road` (105, 80) | 20992, -8192, 1504 | 1024 (west) | A2 (D4 to D5 travel row), the lead (D4's west edge) |
| `entrance:d6_pass` (23, 64) | -20992, 0, 1696 | 0 (east) | A2 (D6 to D5) |
| `entrance:dd24_hold` (86, 43) | 11264, 10752, 2688 | 1536 (south) | A7 (DD-24's way out) |
| `entrance:dd18_grate` (101, 101) | 18944, -18944, 1472 | 512 (north) | A8 (DD-18's exit:d5_grate) |
| `entrance:dd15_door` (64, 78) | 0, -7168, 1248 | 512 (north) | A8 (DD-15's way out) |
| `entrance:dd08_door` (69, 41) | 2560, 11776, 3008 | 1536 (south) | A8 (DD-08's way out) |
| `entrance:dd25_door` (63, 46) | -512, 9216, 2688 | 0 (east) | A8 (DD-25's way out) |

## Lead's note (A6, 2026-11-21, after the install)

- The road read as dark grey paving (its colour comes from the grey `7drsr*` road tiles): D5's terrain entry now lifts
  it to a pale stony earth track (`road: {library: soil_stony, tint_scale: [1.72, 1.41, 1.08], cavity: 0.5,
  height_contrast: 0.45}`), weights swapped; no rebake needed. Capture `output/studio_cal/a6/d5road/arrival.png`.

## D-58: the fall from D7 (A6, 2026-11-21, sixteenth session)

`entrance:d7_fall` at (1024, -4608, 1600), facing south, on the road 2,757 north of the Great Pyramid's door (zone C1-D2, `d7_cd12`). The L1's (0, -8704) lies inside the pyramid's footprint (x ±3,072, y -14,336 to -7,552, a face 600 over it) and no other whole flat cell lies within 2,700 of the door; A3's `d7_cd12` must move here. Checked against the installed map (`output/studio_cal/a6/s16/fall_points.py`): a whole flat cell (the 3 x 3 nodes level), no water or lava, no decoration or wall within 256, no hostile with a ranged attack within 5,888 (placed actors and spawn markers with their slot monsters). The entrance is kind `both` in the plan only so that it does not become the party start (the studio takes the first `arrival`). The map and its scene are unchanged by the point (byte-identical), so only the studio sidecar was installed and the bake stays valid. The fall tests (D-54's shape) run from D7.

## S32 (2026-11-22, A6 32nd session: merge point 41 and the feedback fixes)

Rebuilt on merge point 41, installed with its bake 01:28. Rows 5036, 5047, 5052, 5059, 5060. F10 (the world's worst zone, 1,276 tiles): four doom birds moved (three to (102, 28), (104, 40), (77, 37), one to (68, 73) north of the pyramid), counts unchanged; the strip behind the Parabolic Barrier (D-49: blocked to walking and flying) listed in tools/xeen/empty_zones.yml: largest zone 167 tiles. Walk, hostility pass; audits 0.

## Rim rebuild (2026-11-23, agent xeen-rimmap-c: U-12, D-106, D-109, D-113)

- The rim sea is the void (`terrain.void [[0, 0, 127, 23]]`), 32 hull pieces, 11 return points. The Parabolic
  Barrier's end pylons stand on the land's edge at y 24.2 with the curtain meeting the hull (`cap/d5_after/04`, `05`).
- Checks: audit 0 errors (1 warning, the broken pyramid back-to-back), `void.occupied` 0, doors, walls, town_fit 0,
  empty zones, props, check_wild clean, D-85 0 / DIS 0 (as before). `gate_check.py` is a stale copy of D1's: not run.
- Tests: walk x2 and hostility pass.
- Generated twice (the rescue's return points from the first build's land, `XEEN_WILD_MAPS`), built, villagers placed, recorded (`agent:xeen-rimmap-c`), checked in a private hard-link root, installed with its bake, terrain weights, the minimap re-rendered and its void painted (`tools/xeen/void_minimap.py`). Scripts `output/xeen_rimmap_c/build.sh`, `install.sh`, `tests.sh`, `tours.py`; logs `output/xeen_rimmap_c/run_<key>/`; captures `output/xeen_rimmap_c/cap/<key>_after/` (day and night, against `output/xeen_rim/before/<key>/`).

## D-142, D-157, D-162, F63 (2026-11-25, `xeen-fb4-outdoor3` sub-agent D)

- L1's four polygon populations (sands and pyramid lizards, the cliff birds, the forest cyclopes) are fixed half-cell
  circles at the spots the studio drew them on the map installed 2026-11-24 (`gen.py POLY_SPOTS`, scene spawns
  0-36), so `d142_enforce()` (common/d142.py) can move them: 9 moved a cell or two (the west start's doom birds 3,584
  < 4,096; DD-18's grate 4,087, DD-08's door 4,035, DD-25's door; five off a road, lane or path, 256-1,011 before).
  D5 is in `D142_EXITS`; no kept groups.
- F63: the eyrie's three griffins at spread 1.4 (the first stood 161 from the nest chest's face, 172 needed).
- F58's ruin course: `faces.on_land` 10 → 2 (hill_shrine gone; the Last Water's basin left).
- Left: `wall_check walls.open` on the Doom barrier at (98.05, 23.86) (the same on HEAD's map).
- 2026-11-25 (agent xeen-fb4-outdoor4, installed with its bake): the Doom barrier's `walls.open` closed. The end frames
  stand on the hull's line at y 24.2 and a walkable ledge (y 23.84-24.3) runs between the hull and the rim's cliff; it
  went on past the east end (a 32-wide slot at (98.05, 23.86)). `thing:barrier_block`'s line runs on north to
  y RIM_N - 0.8 at both ends, across the ledge into the cliff. `wall_check` 0, `towns.py --strict` 0 errors.
  Left: `check_faces` on the broken pyramid (`faces.back_to_back` 1, `shell.open_edge` 1) and the basin's 2 `on_land`.
