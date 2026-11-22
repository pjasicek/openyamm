# FD-01 Alamar Depths, L4: notes

New M dungeon under the ruin of Castle Alamar on D6 (dark maze0052, aaze0052), story M39 Prince Roland, Q-F1's Key to
the Dragon Tower and Q-D26's way up to D7, built with the Map Studio from
`devdocs/xeen/mockups/act6_graphs/fd01.graph.yml` and decider D-69 (`mockups/act6_fd01_decisions.md`, which wins) by
`agent:xeen-a8-fd01` (lane A8 session 18), 2026-11-21. Key `fd01`, project `xeen_fd01`, stem `xeen_fd01.blv`,
map_stats 9179, world `xeen`, music 50.

## State and next steps

**Done (session 19, 08:56):** installed, baked, every playtest 4 of 4 from assets_dev including `playtest_in` from D6,
audit 0 errors / 0 warnings, D-71's P1-P3 and item 5 met (section "Session 19" at the end). Built from the scratch root
`output/studio_cal/fd01/root` (refresh it with `python3 output/studio_cal/a8_s17/sync_root.py fd01
output/studio_cal/fd01/root`: it was stale at the session's start). Texture budget 22/45, 0 new. `project.yml` has **no
`map_stats.slots`** (Q71: rests 0; A2's row 9179 has encounter 0, treasure 6).

**Reinstall after a change:** `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh fd01`, then
`flock output/studio_cal/a8_s5/lights/post.lock output/studio_cal/a8_s5/lights/post.sh fd01` (the default bake profile,
xd08's copy; then `four.sh` from assets_dev), then `TESTS=playtest_in ASSETS=$PWD/assets_dev
output/studio_cal/fd01/four.sh` (rewrite it with `tools/tests.py` if D6's event number of `thing:fd01_stair` changes
from 70). `four.sh` and `shoot.sh` take `LOCK=` (default the 18th session's lock).

**Resume:** `LABEL="..." output/studio_cal/fd01/cycle.sh` (gen.py, fmt, validate, build, install into the root, audit,
record; `LEVELS="L1 L2 L3 L4"` for all), then `python3 output/studio_cal/fd01/tools/tests.py` (the playtests read
`ids.lock.yml`). Diff the L4 against `.oymap/last` first if anyone edited it by hand.

**Scratch** `output/studio_cal/fd01/`: `tools/gen.py` (plan, project, diagram), `tools/geo.py` (rooms, openings,
themes), `tools/dress.py` (objects, wiring, atmosphere), `tools/tests.py` (every playtest), `tools/tour.py
rooms|things <name>` + `tools/sheet.py`, `tools/texsheet.py`, `tools/schema_dump.py`, `cycle.sh`, `four.sh` (`ASSETS=`,
`N=`, `TESTS=`, `LOCK=`; every game through `a8_s18/game.lock`), `shoot.sh <tour>`, `run/`, `shots/`, `tex/`. The
source read (`maze0052_*`, `tools/ascii_maze.py`, `regions.py`, `png/`) is kept. **Every project file of L1-L4 except
these notes is written by the generators.**

## What was built

The main level at z 0 (x east, y north); the lift foot and the stasis vault at -768. Walls `swall4` (galleries and
passages, once up the 448 wall) and `swall2` (halls and rooms, once up 512 or 640), `swankdk` floors, `swceilf`
ceilings, `swgirder` reveals; no `swll5dk` main walls, no red accents (Q72 b; A6's ancient-kit `per_site` line
matches: `swall4` galleries and passages, `swall2` halls, `swankdk` floors, `xahullbn` where the castle came down).

- **Ruin stair** (`xahullbn`): the arrival at its foot (0, 0, 0) facing west; twenty steps of 32 climb east from x 256
  to the head at 640 under the gatehouse hatch (the exit face, `swdoora` once).
- **Undercroft hall**: Alamar's teal statue (`xeen_statue_teal`) by the north wall facing into the hall, clear of the
  line from the stair to the gallery door; the plate before it.
- **The C of galleries** (512 wide, 448 high; the south, west and north galleries two rooms each): the gallery door,
  the guard door, the shaft door, the north door (`swdoorb` once, slide up); the west and north galleries' broken ends
  in `xahullbn`. The long gallery has no niches (change 9).
- **Rubble shaft**: a twelve-sided shaft 1,680 across of `xahullbn`, 2,048 high, its ceiling a sky face
  (`open_sky: xeen_darkside_day`); a steel ladder up the west flat (D-71 P1, session 19: two riveted `swgirder` rails
  24 wide standing 32-80 off the wall, sixteen `gn_mtl02` rungs 24 thick, 40-64 off the wall, every 112 from 96 to 1800,
  176 between the rails; no backplate: the whole west flat is a `panel:ladder` of the shaft's own `xahullbn`, so the
  gaps between the rungs show the scorched hull; the click on the wall strip, each rail and each rung); two fallen `gn_mtl03` slabs and two shipped rocks (`6rock01`, `6rock03`) by the wall.
- **Hall of Nine**: four `swaled` machine columns (256 square, the picture once at scale 2); the bronze plaque
  `sign22` in a riveted frame on its east wall. **Lever hall**: the two levers on the west and east walls (D-71 P2,
  session 19): on a riveted `swgirder` plate 160 x 464, a dark `gn_mtl03` pivot boss (96 square, 40 deep, centred at 248)
  and a `gn_mtl02` steel arm 32 square and 176 long standing up from it with a dark grip 48 square on top (a `parts`
  entry of the same mover); pulled, the lever swings 180 degrees about the pivot (`turn`, axis y, merge point 30;
  session 20), out from the wall and down, in one second, so it hangs thrown from its pivot with the grip at its foot. **Sealed passage** (an L) to the west slab.
- **Long workshop**: machine benches; the bolted grate (`swdoorc` once, 192 x 384, a solid leaf) in its south wall;
  the **pyramid nook** (the dead pyramid: a 384 block tapering to 16 at 352 on a 448 plinth, `gn_mtl03` faces, D6's
  travel pyramid's dark wall cladding (D-71's tone, session 20), on a riveted `swgirder` plinth; the nook's
  one light stands by its mouth, not over the pyramid: its light is out) with its chest; the **west passage** and the **assembly hall**
  (stalls of frames, the `sign128` FEWAEE plaque, the foreman's chest); the **east spur** to the east slab.
- **Key vault** (untitled racks of sealed boxes, two on the east wall and, session 20, two on the west wall clear
  of the slab's way in; the box on the south wall the only titled one), **warden's room** (consoles of `swor2`/`trekscrn`, a machine
  panel, the warden's chest on the west wall), the **skull door** (`swtrpnl | swtrdk`, each once at 1:2 on one leaf),
  the **lift head** (the cage, a `swgirder` plate, 768 down; buttons on the head's east and the foot's north wall).
- **Stasis vault**: a twelve-sided chamber 1,728 across, ten `swor2` machine panels round the ring, the `swflora`
  dais, the steel coffin (256 x 96 x 80) with its lid (a mover, slides 104 aside), the stasis field (a mover of four
  `xafield` sheets, translucent, round the coffin; sinks 232 into the dais), the chest by the north wall; the pair
  (one `swdoorb` split over two leaves parting in the middle).

## Measurements

`oymap metrics` (`metrics.json`): **23 sectors** (M 20-45), **39.16 M units²** (M 30-90; the graph's "about 43"),
1 loop (the ring by the grate), **11 doors** (12 leaves: six plain, two slabs, the grate, the skull door, the vault
pair), the lift and two movers, **4 chests** (T6) and the key box's find, 34 placed monsters. Textures
(`tools/xeen/texture_budget.py --root output/studio_cal/fd01/root --map FD-01`): **24 of 45, 0 new**.

Fit for the robots (188 and 228 high, radius 63 capped at 60): walking lines 512 wide (galleries, passages; the east
spur 512 wide), ceilings 448 or more everywhere (the lift foot and the vault 640), every door and open way 384 high
(the grate 192 x 384; open ways 384-448). The reach audit passes (23 of 23 sectors with the doors out of the way).

| Who | Row | Level | XP | Where | Count |
|---|---|---|---|---|---|
| Annihilator | 11611 | 62 | 4,464 | south 3, west 3, north 2, long 2, Hall of Nine 2, workshop 3, west passage 2, assembly 3, key vault 3, warden 2, stasis 3 | 28 |
| Autobot | 11612 | 75 | 6,375 | Hall of Nine 2, assembly 2, warden 1, stasis 1 | 6 |

**Kill XP** 163,242 for the party, **40.81k per member** (D-69 Q63). Groups 1-14 of 2-3, one faction. Quiet: the
stair, the undercroft hall, the shaft, the lever hall, the sealed passage, the east spur, the nook, the lift head and
foot (D-11.3).

**D-57 Q7 exception: 34 monsters, under M's 45 (D-69).**

## Mechanisms (A3's hooks)

- `evt:statue_near` (step on `plate:statue`, while 117840 is clear): `m39.statue` (the boast, once; the hook sets
  117840). `evt:statue` (the statue's click, hover "Statue"): the same hook; after the boast its `else_text` on the status
  bar, "The statue says nothing more. Alamar has had his say." (A3, D-71 item 5); the plate stays silent.
- `evt:plaque_nine`: `m39.plaque_nine`. `evt:plaque_fewaee`: the FEWAEE plaque (map-local, :14), a window.
- `evt:lever_west|east` (on the arm and its grip, one mover; `evt:lever_*_boss` the same on the boss;
  hover "Lever"): while the slab's bit is clear, the slab opens (drops into the floor), the lever is thrown (its one
  turning mover), the hook (`m39.lever_west|east`: the status line, 117841/117842) and the grind; after it the hook's own
  "The lever won't budge." (so no map-local line). `evt:slab_*_load` keep the slabs down and the levers thrown; `evt:slab_*` ("Bulkhead") on the
  shut leaves.
- `evt:grate_bolt` (workshop side): `m39.grate_bolt` ("You draw the bolt.", 117843) and the leaf rises for good;
  `evt:grate_bolted` (gallery side, while 117843 is clear): `m39.grate_bolted` ("Bolted from the other side.");
  `evt:grate_load`.
- `evt:keybox` (hover "Box"): item 12376 once (117844, a window), then "Nothing here." (status).
- `evt:chest_warden`: the chest and `m39.darkstone_key` (111780; then "An empty velvet cushion.").
- `evt:skull_door` (hover "Skull door"): `XeenQuests.can("m39.skull_door")` opens it, sets 117845 and calls the hook
  ("Access granted."); without the Cube the hook's "Access denied! You do not have the proper I.D."; `evt:skull_load`.
- `evt:lift_head|lift_foot` (hover "Lift"): the cage.
- `evt:coffin|field|lid` (hover "Coffin" on the coffin, the field and the lid): while 111781 is clear the field sinks,
  the lid slides, `m39.roland` (the amulet 12372, the award, 40,000, 111781), the lid sound, the field's light and the
  hum off; after it the hook's `else_text` "An empty stasis coffin, still faintly cold.". `evt:coffin_load` keeps the
  field down, the lid open, the hum and the glow off on every load with 111781.
- `evt:pyramid` (hover "Pyramid"): `m39.pyramid`.
- `evt:ladder` (the wall strip; `evt:ladder_rail_n|s` and `evt:ladder_rung_01..16` the same on the rails and rungs;
  hover "Ladder"): the map's own Yes/No "Climb up through the hatch?" with no message before it; Yes
  calls `q-d26.depths_hatch` ("Bolted from above." until 113521); true leaves at once (`leave: exit:d7_roof`) to D7's
  `entrance:fd01_roof`; No stays.
- `evt:visit_load` / `evt:visit_end` / `evt:arrival` (DD-17's in_visit pattern): a real entry arms one check one second
  in; with the party within 640 of `entrance:d7_roof` it calls `m39.shaft_arrival` (once per game, 117846, a status
  line, no line before it). A D6 arrival and a game loaded inside say nothing.
- `evt:exit_hatch` (hover "Exit Alamar Depths"): the exit preset to D6.

## Arrivals and exits

| Inside arrival | At (x, y, z), facing | Measured headless | From |
|---|---|---|---|
| `entrance:d6_stair` (= start) | (0, 0, 0), west (1024) | (0, 0, 0) facing 1024 | D6's `thing:fd01_stair` (A6, sealed until DUNGEON['fd01'] is lifted) |
| `entrance:d7_roof` | (-7744, 7168, 0), east (0) | (-7744, 7168, 0) facing 0 | D7's roof hatch (A6, `q-d26.hatch`, LIVE['fd01'] at the install) |

| This map's way out | To | Measured | Facing |
|---|---|---|---|
| the hatch at the stair's head (exit preset, OK) | D6 `entrance:fd01_stair` (-6656, 4608, 2208) | **(-6656, 4608, 2209)** | 1536 |
| the ladder's Yes with 113521 | D7 `entrance:fd01_roof` (-18688, 8448, 1536) | **(-18688, 8448, 1536)** | 1024 |

## Ids

- Map qbits (A3's names in m39.yml): statue_spoken 117840, slab_west 117841, slab_east 117842, grate_bolt 117843,
  key_box 117844, skull_door_open 117845, arrived_from_d7 117846 (117847-117879 free). Quest bits read: 111780
  (darkstone_key), 111781 (m39.done), 113521 (roof_unlocked).
- Doors (ids.lock.yml): lift 1, gallery 2, grate 3, guard 4, north 5, shaft 6, skull 7, slab_east 8, slab_west 9, vault
  pair 10-11, warden 12, works 13; movers field 14, lid 15. Chests 0 assembly, 1 pyramid, 2 stasis, 3 warden.

## Playtests

`output/studio_cal/fd01/four.sh` from the scratch root (`ASSETS=` for assets_dev), `--world xeen --map
xeen_fd01.blv`; written by `tools/tests.py`.

| Test | What |
|---|---|
| `playtest.yml` | the D6 arrival (position, facing 1024, no line); the statue's boast once (117840), not again from the plate; the click then "The statue says nothing more." on the status bar, no window (D-71 item 5); round the C; the levers west then east (status lines, bits, slabs down), then "The lever won't budge." from both; the key box (12376, 117844), then "Nothing here." and nothing more; the warden's chest (the key line, 111780, gold), then the cushion line; the skull door with the Cube ("Access granted.", 117845; open after a reload); the lift down; the pair; the coffin (field and lid open, 111781, 12372; a reload: both stay; the empty line); the stasis, nook and assembly chests; the pyramid's line |
| `playtest_levers.yml` | east then west, each its line, bit, slab and the lever thrown (its turning mover at its end); a reload (both slabs down, both levers thrown); "The lever won't budge." from both, and from each boss (the grip is the arm's mover) |
| `playtest_skull.yml` | without the Cube: "Access denied! You do not have the proper I.D.", shut, 117845 clear |
| `playtest_grate.yml` | gallery face "Bolted from the other side." (shut); workshop face "You draw the bolt." (open, 117843); a reload (open); walked through from the gallery side |
| `playtest_shaft.yml` | from D7 at `entrance:d7_roof` (position, facing 0), the arrival line once (117846), no line on a second arrival; the rails and the top and bottom rungs ask too (No); the ladder: No stays; Yes without 113521 "Bolted from above." and stays; with 113521 Yes: D7 at `entrance:fd01_roof` (position, facing 1024) |
| `playtest_exit.yml` | up the stair, the exit window's OK: D6 at `entrance:fd01_stair` (position, facing 1536) |
| `playtest_hostility.yml` | 28 + 6 hostile at load, none peaceful; both kinds spawned side by side do not take each other on |
| `playtest_in.yml` | from D6's `entrance:fd01_stair` with the Cube and m33.done, the stair's event (70), m39.depths_door's line, no question (D-72), to `entrance:d6_stair` (0, 0, 0) facing 1024; not in `four.sh`'s default list (`TESTS=playtest_in`) |

## Texture fit exceptions

None (audit: 0 texture findings). The Hall of Nine's plaque (`sign22`) sits in a riveted `swgirder` frame (the first
audit warned of its border against `swall2`).

## Dressing exceptions

None (audit: 0 dressing findings).

## Build warning and audit infos kept

- Build: "nothing tells the player on arrival why he is here": kept by D-69 (both arrivals are quiet, D-11.3; the D6
  arrival is greeted by the statue's boast a few steps in, the D7 arrival by `m39.shaft_arrival`).
- `click.silent` on the statue (event 36) is gone with A3's `else_text` (session 19, D-71 item 5); the ladder's
  events ask a Yes/No.
- `state.never_read` AmbientSound3: the coffin hum's switch, read by the engine, not by a handler.

## Waiting on

- Nothing. D6's stair (event 70) and D7's hatch into this map are live (A6, 08:39 and 08:40); `playtest_in.yml` 4 of 4
  from assets_dev (session 19). A3's `q-d26.hatch` follows m33.done with no "gone" state (D-69 change 6). Alamar's
  statue is S's `xeen_statue_teal` and reads right (D-71: off this list). No test rows.

## Lines for A3 (map-local, written inline)

- The FEWAEE plaque (aaze0052:14): "The message on the plaque reads: FEWAEEFFWAEFAWEEWWEFAW / Remember: A = Air,
  E = Earth, F = Fire, W = Water."
- The key box's find: "Inside the box, alone on its rack: a black key with a dragon's eye for a bow. The Key to the
  Dragon Tower." and its "Nothing here." (:16); the hover "Box" (:2).
- The slabs before their levers: "A shut bulkhead. Nothing on this side moves it." (hover "Bulkhead").
- The grate's "The grate stands open." (locked text, only reachable while the leaf is open).
- Hovers: "Lever" (:15), "Coffin" (:7), "Statue", "Pyramid", "Ladder", "Skull door", "Stasis vault", "Plaque",
  "Exit Alamar Depths". "The lever won't budge." (:17) is `m39.lever_*`'s else_text, so not map-local.

Hook text mismatches: none. One difference: `m39.statue` has `once: true` (the brief said it had none); the map's
condition on 117840 guards it as well, harmlessly.

## Sounds for AU

`xeen_machine_stamp_loop` beds over the Hall of Nine and the workshop (`pan: false`, volume 0.14, DD-17's, fainter);
`humming` over the east wing (`pan: false`); the coffin's hum (`humming`, an engine stand-in) stops with the field;
`whistling wind` in the shaft (shipped). The lever grind (the source's FX 35) plays the shipped `6stone door0101`
(DD-17's grind); the lid `xeen_coffin_lid`; the lift `xeen_lift`. **For AU:** the trickling grit down the shaft, the
coffin's cold stasis hum (to replace `humming`), the settling-metal groans over the bed (optional).

## DECIDE

1. **The stasis vault lies east of the lift foot** (the graph draws it west): east it sits under nothing; west it
   would lie under the Hall of Nine. Cheap to reverse (geo.py).
2. **The field is four translucent `xafield` sheets round the coffin** (no roof sheet), sinking into the dais: a roof
   sheet would pass through the coffin as it sinks. The coffin is clicked over the 224 sheets.
3. **The ladder is built in geometry**: `bemv` reads as a wooden beam and `d1ladder`'s stone background does not match
   `xahullbn`. D-71 accepted the method and changed the look (P1, done in session 19: rungs off the wall, no backplate).
4. **Lockers, not wooden chests** (`swgirder`, DD-22's D-67 item 4): four T6 lockers.
5. **The statue's click calls the same once-hook**; D-71 item 5: after the boast it shows A3's `else_text` on the
   status bar (done in session 19).
6. **The D7 arrival point is (-7744, 7168)**, 64 west of the graph's "about (-7680, 7168)", so the party stands clear
   of the shaft door's reveal.

## Pictures (looked at, scratch root, no bake)

`output/studio_cal/fd01/shots/things1_1..4.jpg` (every room's things: the arrival, the stair and hatch, the statue, the
galleries and doors, the grate from both faces, the shaft and its sky, the north door, the Hall of Nine and its plaque,
the lever hall, the slabs, the workshop, the pyramid, the assembly hall and plaque, the key vault, the warden's room,
the skull door, the lift head, the pair, the stasis vault, the coffin under the field), `fix1_1.jpg` (after: the steel
ladder, the lever plates, the shaft's slabs). Changed after looking: the ladder (a `bemv` beam that read as a pole),
the levers (tiny on a bare wall: now on riveted plates), the cage (now a riveted plate, apart from the floor).

## Test runs

All seven 4 of 4 from the scratch root (`output/studio_cal/fd01/run/four_082605`, summary `four_s18.txt`): playtest
177 checks, levers 31, skull 19, grate 34, shaft 67, exit 25, hostility 18. `playtest_in` waits on A6.

## Installed (lead, session 18)

Installed 08:28 (`output/studio_cal/fd01/b_082813`), baked 08:28 on the default profile
(`tools/lighting/baked_indoors/profiles/xeen_fd01.yml`, the xd08 copy, as DD-17/22/26), 0 stale bakes. **4 of 4 from
assets_dev**: playtest 177, levers 31, skull 19, grate 34, shaft 67, exit 25, hostility 18 passes
(`output/studio_cal/fd01/run/four_082849`). Audit of the installed map 0 errors / 0 warnings
(`output/studio_cal/a8_s18/audit_fd01.txt`; info `click.silent` on the statue after the boast, kept: DECIDE 5). Baked
tour `output/studio_cal/fd01/shots/things1_1..4.jpg` read. Waiting: `playtest_in.yml` after A6's D6 rebuild
(`TESTS=playtest_in ASSETS=$PWD/assets_dev output/studio_cal/fd01/four.sh`). Polish: the nook's pyramid reads pale
(D6's `gn_mtl02` as is), not dark; the key vault has no racks of boxes; the levers are small handles on plates.

## Session 19 (D-71 P1-P3, item 5; A8 session 19)

- **P1 ladder** and **P2 levers** as in "What was built" (geo.py, dress.py; before: `tools/*_before_s19.py`, the L4 before:
  `output/studio_cal/a8_s19/fd01_L4_before/`). Item 5: A3's `else_text` on `m39.statue` (08:37) answers the statue's
  click after the boast; `playtest.yml` asserts the plate silent and the status line. 61 events (the ladder's 18 and
  the levers' 6 sources), 22 of 45 textures (0 new: the studio lever's `BemH16a` gone).
- **Installed 08:47** (`output/studio_cal/fd01/b_084702`), **baked 08:47** (default profile), 0 stale, **4 of 4 from
  assets_dev** (`output/studio_cal/fd01/run/four_084734`: playtest 183, levers 47, skull 19, grate 34, shaft 107, exit
  25, hostility 18) and `playtest_in` 4 of 4 (`four_085138`, 22 checks). Audit of the installed map 0 errors / 0
  warnings, one info (`state.never_read`, kept); the statue's `click.silent` is gone.
- **Pictures (baked):** `output/studio_cal/fd01/shots/things2_1..4.jpg` (the reshoot of `things1`) and the polish
  tour `output/studio_cal/a8_s19/fd01/polish19b_1..2.jpg` (a menu-input tour: a screenshot tour pauses the world, so
  movers do not move in one): the ladder reads as a ladder from the arrival (10), looking up (11) and close (12, 12b-d);
  both levers up and thrown (19, 19b-d) and from the hall's middle (18b-d).
- **Shot 27's pale flat blue shape** is an Annihilator (11611) floating under the camera: its pale antenna paddle and
  dome, cut by the near plane (`polish19b` 27 and 27b, taken after the robots had moved, show the paddle and the dome
  whole; 27c from further back shows the three robots of the key vault). Not an untextured face; nothing to fix.

## Session 21 (A8): AU's sounds

`sound:coffin_hum` is AU's `xeen_stasis_hum` (still off with the field and on every load after `m39.done`); `sound:shaft_grit` (`xeen_shaft_grit`) beside the shaft's wind; `sound:metal_groan` (`xeen_metal_groan`, wait 25-60 s) over the Hall of Nine. Checked in the game (`a8_s21/sndcheck/logs/fd01_game.log`): grit and wind start in the shaft, the hum at the coffin, the hum stops at the coffin's event and does not start after a reload. Through the generator; installed 10:05, rebaked, tests 4 of 4 from assets_dev, audit 0 errors (lane log `A8.md`, "21st session").

## Session 23 (A8): review fixes (row 39)

- **The levers read as grey placeholders.** Each arm is now a slice of MM6's `swpipes` teal banded pipe (its 256 texels
  once up the 176 arm, `scale` 0.6875, `offset` [52, 0] to centre the pipe on the 32 face, `uneven`), the grip a slice
  of its red collared pipe (`offset` [186, 64]) capped with `swhz2dk`'s red disc (`scale` 0.375), the pivot boss's
  face `swildk` (a riveted plate with a domed bolt, once, `fit`), its other faces `swgirder` (geo.py `LEVER_*`).
- **The dead pyramid** is MM6's black veined marble `mystrya` (was `gn_mtl03`, which baked as plain grey): it reads as
  dark obsidian-like stone (D-71: its light is out).
- Four shipped textures added (swpipes, swhz2dk, swildk, mystrya), none new.
- Before/after: `output/studio_cal/a8_s23/shots/fd01_before2_sheet_*.jpg`, `fd01_after_sheet_*.jpg`.

## Session 26 (A8, 2026-11-22)

- F16: the 19 ladder events (foot, rails, 16 rungs) no longer ask "Climb up through the hatch?": `q-d26.depths_hatch`
  first ("Bolted from above." until roof_unlocked 113521), then the `exit:` effect's standard entrance window (OK/Close)
  to D7's entrance:fd01_roof (`tools/dress.py`; `tools/tests.py` playtest_shaft: bolted, Close stays, OK leaves).
  Audit 19 `entrance.question` errors -> 0 errors, 0 warnings. Installed 00:16, baked, 8 playtests 32/32 from assets_dev.

### Drop pockets

- `check_drops.py`: the stasis vault floor at (-181, 3893) z -768 (768 below) is reached and left by the vault's lift
  (button 25 "Lift"), which the check does not ride: by design, no ladder.

## Session 29 (A8): MP42 rebuild

Rebuilt on oymap merge point 42 (2026-11-22 ~02:30): the generator (gen.py L4 + tests.py) reproduced the L4 unchanged
and the build equals the installed map (its four chests already a set kind, not MM6's ch1; no raised fitted top),
nothing to install; audit 0/0, check_exits 0, check_drops 1 (the stasis vault, by design, see Drop pockets). Chest
pictures: output/studio_cal/a8_s29/shots/fd01_chests.jpg (all four on the floor against a wall).
