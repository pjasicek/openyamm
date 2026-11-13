# Castle Darkmoor (mm6 cd2.blv) rebuilt as a Map Studio project: notes

Run of 2026-11-12, by the procedure in `devdocs/map_studio/REBUILD_PROCEDURE.md`. Project id `calib_darkmoor`, map
table row 9715, reference `cd2.blv`. The project is in the original's own frame.

## How this rebuild was made (read this before judging it)

The map has 195 sector records (193 with a floor worth drawing). They were not drawn by hand. `rooms.yml`,
`objects.yml` and `wiring.yml` are written by scripts that measure the original's export and say what they find in
the vocabulary:

- `output/studio_cal/mm6_cd2/tools/gen.py` (rooms and openings), `gen_objects.py` (objects and wiring),
  `overrides.py` (the room list with wing and name per sector, and every decision made by hand), `run.sh` (generate,
  format, validate, build, install into the mount). `cmpo.sh` runs `oymap compare` and `rep.py` sums it by sector;
  `frontier.py` lists the openings the walk does not pass; `wings.py` writes the table at the end of this file.
- A room's outline is the outer line of one sector's floor at one height, with points in a line removed (212 of the
  309 rooms have 4 points, the largest has 22). That is a measurement by tool of the room's shape, not a copy of a
  face's vertex list, but it is nearer to tracing than a person's description would be: the rule against traces is
  kept in its letter (no outline over 30 points, every room one simple shape) and the reviewer should decide whether
  in its spirit. Editing `rooms.yml` by hand is lost on the next `run.sh`; change `overrides.py`.
- The scripts need `shapely`, which was installed into the session's scratch folder (`pip install --target`); the
  path is the first line of `tools/lib.py`.
- `oymap install` reads `<project>/build`, so the build's output folder `L4/build/` exists beside the project files.

What the measurement does with a sector: a thin sector between two parallel portals becomes the thickness of one
opening (37 sectors); a floor of several heights becomes one room per level, a run of narrow treads a stepped room
with its top tread as a landing, a sloped floor a ramp (cut in parts where its ceiling climbs with it); a level
inside another becomes a `levels` entry, a hole in the floor a pillar; where a floor runs a wall's thickness into a
doorway that part belongs to the opening; an arched portal becomes `shape: arch`; ceilings are the lowest level tier
that covers a fifth of the room with higher tiers as `ceiling_levels`, or for a vault the height half of it lies
under with its crown raised; wall, floor and ceiling textures are read off the original per room and per wall
(17 themes). The eight caves are their level floor, with the rock banks round them as sloped rooms.

## Where it stands

| | first | last |
|---|---|---|
| `oymap compare` score | 79.9 % (round 2, the first run after the command appeared) | **87.8 %** |
| distances agree | 80.2 % of 425,550 rays | 87.7 % of 415,400 |
| textures agree | 79.4 % | 95.4 % (97.4 % where distances agree) |
| points without a floor in the rebuild | 9 of 8,520 | 212 |
| mean ceiling difference | 156 | 97 |
| castle alone (all but the 8 cave sectors, 3,802 points) | 92.8 % | 94.7 % |
| caves alone (4,718 points) | 69.4 % | 82.1 % |

Round by round (compare score): 79.9 shell with one theme; 80.3 textures read off the original and caves cut back
to their level floor (texture 79 to 96, but 763 bank points lost their floor); 87.2 rock banks as sloped rooms;
87.4 vault ceilings by their median; 87.8 pillars of the throne hall, teleporter cubes, ambient 13. Before
`oymap compare` existed the stand-in `tools/cmp.py` (18 rays from 600 points) gave 76.9 % geometry and 87.3 %
texture for the first shell, and 96.9 % and 96.5 % for wing 1 alone.

`compare.py`: counted (structure, scale, play): 20 in, 11 near, 4 out. The "near" and "out" rows are counts that
grow because one sector is several rooms here (309 sectors against 194, 330 doorways against 220).

Rooms: **all 193 floor sectors are drawn** (156 as 309 rooms, 37 as openings; sector 194, a desk side of 1,024
square units, is left out). **All of them are in the comparison** (166 sectors carry points; the rest are the
doorway sectors). Reached on foot from the start with every door out of the way: 283 of 309 rooms, which is 140 of
the 156 drawn sectors; the original reaches 179 of its 194. Not reached here: the wall walk and its towers
(98 to 101, 184 to 191), the teleport chamber (192) and the lich's study (193), all of which the original reaches
only through its teleporters; the two barred rooms 30 and 121, which the original does not reach either.
`oymap solve` opens the rebuild as the original opens: the keep first (123 of 309 rooms; the original 84 of 194
sectors), then the lever, the portcullis and everything behind it, then the doors behind doors.

Playtest (`playtest.yml`, run from `output/studio_cal/mm6_cd2/run`, about 15 minutes): **passes, 60 steps.** On foot from the gate through the crypt, up to the stair hall, the lever (portcullis shut before, open after), the keep's halls, the great hall, the stair door (clicked), the north cavern, the gatehouse, the throne hall and its north gallery, the long ramp to the west lever (forcefield shut before, open after), the west ward and through the forcefield's doorway into the west court; heights asserted at every stop. It does not use the teleporters (they cannot be wired), the exit or the chest (in a room only a teleporter reaches). Monsters are killed as they come (`clear_hostiles`), the party is immortal.

In-game pairs (`ingame_compare.py`, 11 cameras of `output/studio_cal/mm6_cd2/shots.yml`, sheets in
`output/studio_cal/mm6_cd2/ingame/diff`): edge agreement 0.83 on the first take, 0.85 on the last. Looked at: the
crypt rooms, the entry and the throne hall (0.96 after its six pillars were drawn) read as the original; the great
hall lacks its vault and the shaft the cube hangs from; the south cavern shows upright castle walls where the
original has a dome coming down to rock banks; every original picture has the floor mist and the rebuild none.

## The five worst remaining differences

1. **South cavern (sector 1), 58 %, a fifth of all loss.** A dome whose ceiling comes down from 2,160 to the floor's
   level at the rim, over a floor with rock rising inside it. Drawn as a level floor under a flat ceiling at 1,170
   (it must reach the battlement gallery's openings at 588 to 1,170) with seven banks. Needs a shaped ceiling and
   uneven ground.
2. **The four outer caverns (72, 73, 66, 71), 81 to 89 %, half of all loss.** Their banks are drawn as one
   parallelogram of slope behind each cave wall, each between its own side walls, with wedges of solid rock between
   neighbours; their vaults step 630, 900, 1,170 toward the middle and the rebuild has one height (two in 66).
3. **Great hall (56), 82 %, ceiling 280 too high on average.** A vault from 356 at the walls to a flat crown at
   1,920: drawn as 1,392 with the crown raised. The rock that climbs its north-west corner is flat floor. The east
   balcony's second arch and the gallery window over the north arches are not drawn (one opening per stretch of
   wall).
4. **Far arms of the south cavern (142, 143), 45 to 57 %.** Tunnels whose floor and ceiling both slope; drawn level.
5. **Battlement gallery (4), 79 %, and the rooms that look into a taller room from above** (176 into 8 through a
   window, 59 into 56, 164 into 144): of two openings one above the other in the same stretch of wall only one is
   drawn, so the upper room has a blank wall.

## Gaps in the vocabulary, most harmful first

1. **An event needs a door, switch, chest or exit as its source.** The original has 32 floor plates and touch faces
   (11 traps that cast spells, 7 summons, 14 teleports) and none can be wired: the three teleporter cubes that are
   the map's main puzzle and its only way to the wall walk, the teleport chamber and the lich's study are blocks
   with placeholders (`ph:event28` and so on, 41 placeholders). Done instead: the east lever lowers the portcullis
   and the west lever opens the forcefield directly. Wanted: `plates` in objects.yml (a floor outline or a block's
   faces as an event's source, `trigger: step | touch`), and a `cast` and a `summon` effect.
2. **A room's floor is level or one slope across a convex room.** Cave banks, the rock in the great hall's corner,
   the south cavern's ground, tunnels 142 and 143. Done instead: banks as separate slope rooms, the rest flat.
   Wanted: `levels` entries that may touch the walls and may slope (`slope` on a level), or a `relief` list of
   height points as the outdoor sketch has.
3. **A ceiling is flat, with raised parts that may not touch walls or each other.** Domes and vaults of every cave
   and of the great hall, the coved ceilings of the keep's halls, ceilings that climb with a ramp (93, 109: cut into
   three ramps each so the corridor underneath fits). `ceiling_levels` inside one another are refused
   (`rooms[0].ceiling_levels[1]: the region cannot be cut out`) while `levels` inside one another are accepted.
   Wanted: nested ceiling levels, a `ceiling_slope`, a `vault: {spring, crown}`.
4. **An opening cannot say which wall it is in, and a wall takes one opening per stretch whatever the heights.**
   The build takes the longest pair of facing walls. A ramp beside the room it also meets at its foot gets its side
   chosen and no opening (144's ramp, fixed by cutting a 48-deep landing from the ramp; 163's long ramp); 11 of the
   original's doorways sit on another pair than the one chosen (listed in `gen_log.txt`); 5 openings above or below
   another are dropped (1 to 4, 56 to 58, 56 to 57, 8 to 176, 163 to 165). Wanted: `wall:` and `to_wall:` on an
   opening, and holes compared in height as well as along the wall.
5. **A ramp or flight is a room with walls on both sides.** The 96-wide ramp that climbs 790 along the open side of
   the tall corridor (163), the ramp into the west ward (144), stairs open to the hall they descend into (145).
   Wanted: an opening along a slope's side (a `width: full` opening whose sill follows the floor), or `flights` that
   may be ramps and may start at a wall.
6. **A stair that turns.** The spiral (52 to 55) is a fan of 20 level triangles each 30 above the last; each is a
   room here, which is the wedge-room trick the procedure warns against. Wanted: `slope` on a room given as a path
   (a stair or ramp that follows a curve).
7. **A step in a doorway.** Where the doorway's own floor is a step between two rooms 60 apart (76 and 147) the opening's sill is the higher floor and the party cannot climb it; the doorway sector is drawn as a
   room 96 deep. Wanted: `steps: n` on an opening.
8. **Doors slide up, down or swing; the original's seven real doors slide sideways into the wall**, two of them
   whole wall panels (secret doors 6, 7, 8, 9). Drawn as `slide_up`. A door in a wall without thickness is refused
   (record 5; its pocket was cut from the stair room). Wanted: `kind: slide_left | slide_right`, `secret: true`.
9. **A blocker that is not a door.** The forcefield to the west court is an invisible face made passable by an
   event; drawn as a lava-textured `slide_up` door, which the original does not show. Wanted: `barriers` (an opening
   closed by an unseen or textured face that events switch).
10. **Sunk levels cannot hold one another; raised blocks cannot hang from the ceiling.** The west ward's ring steps
    down 30, 60, 90; only the first is drawn. The teleporter cubes hang on shafts; the cube is a platform with a
    `base`, the shaft is missing.
11. **No floor mist** (the original's `cd2_mist.scene.yml`): `atmosphere.yml` has fog distances and a ceiling only.
12. **No fixed actors, no items on the floor, no tier on a spawn.** The lich guardian with its item (placeholder),
    72 floor items and 5 item spawns (placeholder), 22 spawns whose index fixes the tier (noted on each).
13. **A switch changes one texture by cog number; the levers and the sign change five faces each** (orange water to
    lava on the cube) and set face bits. Not wired.
14. **Wall textures cannot be shifted.** The same stone sits a few courses off on many walls (the sunken chamber
    pair), which the in-game edge measure counts.

## Tool defects

- `oymap validate` passes a project that `oymap build` refuses: a sloped room whose low and high walls are not
  parallel gives `rooms.yml: the indoor compiler refused the lowered map: indoor native face is non-planar after
  coordinate quantization: 3067`, with a face number and no room. Shown by any convex four-sided room with
  `slope` whose `toward` wall is not parallel to the opposite one. Validation should require it or the lowering
  should triangulate.
- `oymap install <project> --mount m --assets a` after `oymap build <project> --out elsewhere` fails with
  `could not read <project>/build/<id>.blv (build the project first)`: install has no `--from`.
- `oymap assets orwtrtyl --assets assets_dev --world mm6 --kind texture` and the same for `lavatyl` answer
  `"matches": 0`, though both are on the original's faces and the build takes them.
- `oymap solve cd2.blv --world mm6 --assets assets_dev` calls the opening action `door 1 close`, and lists sector
  94 (the west court) as never reached: it does not follow `SetFacetBit` making the forcefield faces passable.
  `oymap metrics` on the original reports a doorway 1 unit wide (portals squeezed by a shut sideways door).
- `oymap audit <project> --reach` and `oymap solve` say how many sectors are not reached but not which opening
  stops the walk. The first shell reached 5 of 224 sectors because of one 90-unit sill; finding it took probes room
  by room. A list of the openings with a reached room on one side only (as `tools/frontier.py` makes from
  `solve --json`) belongs in the audit.
- The game's `walk_to` from the lever gallery to the west ward (-6000, 12500, -240) planned 502 waypoints and then
  stood against the side wall of the steps out of the south-west hall (stuck at -5065, 11483, -60, aiming at
  waypoint 463 at -4905, 11564, -150, which is past that wall); `oymap probe` from the same point finds a route
  round by the landing. With a waypoint on the landing the walk passes (`output/studio_cal/mm6_cd2/leg_test.yml`).
- `ingame_compare.py` installs into `output/studio_slice_root` by default: five agents at once would overwrite one
  another's map_stats row there (`--root` in the agent's own folder avoids it).
- `oymap build` prints one warning per zero-thickness opening that leaves wall beside it (dozens here) and the
  placeholders after them; a count per kind would read better.
- `oymap compare` scores a point with no floor in the rebuild as zero, so cutting the caves back to their level
  floor (right for every ray from the floor) cost as much as it gained until the banks were drawn; worth knowing
  when reading a score.

## Unsure of in the original

- Spawn index to slot: indices 1 to 3 are taken as slots 1 to 3, 4 to 12 as slot (index - 4) / 3 + 1 with a fixed
  tier. Not checked against the engine.
- Door records 11 to 14 (moves of 16 to 32 units) are the levers' own plates and two small panels beside them; not
  built. Record 10 was read as the portcullis in sector 67.
- Events 61 to 63 (sarcophagi: "Steal from the dead?") test map variables nothing sets; event 58 on the forcefield
  runs a long chain of tests that `oymap flow` truncates. Placeholders.
- The floor at 600 between the two gate towers (face 3949) stretches with door record 9; it was read as the bridge
  of the wall walk, and record 9 as a panel from it out over the cave.
- A tread nearest a doorway can be taken for the doorway's thickness by the measurement (the lowest tread to the
  west ward, sector 145): the rebuild then drops 60 in the doorway instead of stepping twice.
- Wall votes look through a wall at one height; walls with two textures one above the other (bands) were not read.

## What a full rebuild would still need

The shell is whole; what is missing is what the gaps name. In order: plates and touch faces (then the teleporter
puzzle, the traps, the summons and the three rooms behind teleports can be played); shaped ceilings and uneven
floors for the eight caves and the great hall (55 % of the comparison's points); openings one above another; open
ramp sides; a hand pass over each wing with the in-game sheets (only 11 cameras were looked at); names and notes
per room beyond the sector's name; wall bands; chest 0's real contents; the mist.

## The room list


### Wing 1: entry, crypt level and ground floor of the keep

46 sectors: 37 drawn as 55 rooms, 9 as the thickness of an opening; compare score 96.6 % over 627 points.

| Sector | What it is | Drawn as | Score |
|---|---|---|---|
| 2 | Cross hall, south arm | 1 room | 90 % |
| 3 | Cross hall, portal slot | opening | 83 % |
| 5 | Cross hall | 1 room | 92 % |
| 6 | Arrow slit | opening | - |
| 7 | Arrow slit | opening | - |
| 8 | East tall hall | 1 room | 95 % |
| 9 | Middle tall hall | 1 room | 96 % |
| 10 | West tall hall | 1 room | 96 % |
| 11 | Guard room doorway | opening | 94 % |
| 12 | Guard room | 1 room | 99 % |
| 13 | Arrow slit | opening | - |
| 20 | Long ramp from the stair hall down to the crypt | 5 rooms | 90 % |
| 21 | East room | 1 room | 95 % |
| 22 | East anteroom | 1 room | 95 % |
| 23 | Doorway to the east hall | opening | 95 % |
| 24 | Cell block | 1 room | 100 % |
| 25 | Cell block passage | 1 room | - |
| 26 | Cell | 1 room | 100 % |
| 27 | Cell doorway | 1 room | 100 % |
| 28 | Cell | 1 room | 98 % |
| 29 | Cell doorway | opening | 97 % |
| 30 | Arrow slit | 1 room | - |
| 31 | South crypt hall | 1 room | 98 % |
| 32 | Stepped crypt landing | 6 rooms | 99 % |
| 33 | East side chamber | 1 room | 97 % |
| 34 | Doorway to the side chamber | opening | - |
| 35 | South-east crypt hall | 1 room | 97 % |
| 36 | Ramp from the crypt to the ground floor | 3 rooms | 83 % |
| 37 | Crypt corridor | 1 room | 95 % |
| 38 | Sunken chamber with the broad steps | 6 rooms | 100 % |
| 39 | South-west vault | 1 room | 100 % |
| 40 | Cell passage | 1 room | 98 % |
| 41 | Cell doorway | opening | 96 % |
| 42 | Trap-floor cell | 1 room | 98 % |
| 43 | Cell | 1 room | 96 % |
| 44 | Stepped cell | 3 rooms | 94 % |
| 45 | Cell | 1 room | 99 % |
| 46 | Cell corridor | 1 room | 100 % |
| 47 | East vault | 1 room | 100 % |
| 48 | West crypt chamber | 1 room | 100 % |
| 49 | Crypt passage | 1 room | 96 % |
| 50 | Entry gallery | 1 room | 100 % |
| 51 | Entry hall (the way out to the Darkmoor region) | 1 room | 97 % |
| 63 | Great arch between the west and middle halls | 1 room | 94 % |
| 64 | Great arch between the middle and east halls | 1 room | 95 % |
| 65 | Great arch to the great hall | 1 room | 89 % |

### Wing 2: stair hall, spiral, upper floor and the south cavern

27 sectors: 20 drawn as 49 rooms, 7 as the thickness of an opening; compare score 67.3 % over 765 points.

| Sector | What it is | Drawn as | Score |
|---|---|---|---|
| 1 | South cavern | 8 rooms | 58 % |
| 4 | Battlement gallery over the south cavern | 1 room | 79 % |
| 14 | Stair hall | 1 room | 96 % |
| 15 | Steps from the guard room to the stair hall | 2 rooms | 95 % |
| 16 | Lever closet | 1 room | 100 % |
| 17 | North passage of the stair hall | 1 room | 97 % |
| 18 | Stair hall doorway | opening | - |
| 19 | Octagon at the stair head | 1 room | 96 % |
| 52 | Spiral ramp, first quarter | 4 rooms | 98 % |
| 53 | Spiral ramp, second quarter | 5 rooms | 100 % |
| 54 | Spiral ramp, third quarter | 5 rooms | 99 % |
| 55 | Spiral ramp, last quarter | 6 rooms | 99 % |
| 142 | South cavern, west arm | 2 rooms | 57 % |
| 143 | South cavern, far west arm | 1 room | 45 % |
| 151 | Tower room at the top of the spiral | 1 room | 99 % |
| 152 | Upper passage from the tower | 3 rooms | 98 % |
| 173 | Doorway from the battlement | opening | - |
| 174 | Upper west passage | 1 room | 94 % |
| 175 | Upper doorway | opening | 90 % |
| 176 | Upper hall | 1 room | 95 % |
| 177 | Upper doorway | opening | - |
| 178 | Upper east passage | 1 room | 99 % |
| 179 | Upper south room | 1 room | 98 % |
| 180 | Upper doorway | opening | 97 % |
| 181 | Ramp from the upper floor down to the balcony | 3 rooms | 100 % |
| 182 | Balcony doorway | opening | 97 % |
| 183 | Window from the upper hall into the east tall hall | opening | - |

### Wing 3: great hall, its galleries, low tunnels and the north cavern

27 sectors: 21 drawn as 37 rooms, 6 as the thickness of an opening; compare score 85.4 % over 1641 points.

| Sector | What it is | Drawn as | Score |
|---|---|---|---|
| 56 | Great hall | 1 room | 82 % |
| 57 | East balcony of the great hall | 1 room | 95 % |
| 58 | North passage under the gallery | 1 room | 89 % |
| 59 | North gallery | 1 room | 98 % |
| 60 | North-east corner room | 1 room | 100 % |
| 61 | Balcony arch | opening | - |
| 62 | Balcony arch | opening | - |
| 66 | North cavern | 6 rooms | 82 % |
| 67 | Portcullis | opening | - |
| 68 | Arch to the north passage | opening | 89 % |
| 69 | Arch to the north passage | opening | 29 % |
| 70 | Gallery window | opening | - |
| 153 | North-west room over the hall | 2 rooms | 100 % |
| 154 | Ramp passage down to the skull room | 3 rooms | 100 % |
| 155 | Skull room | 1 room | 99 % |
| 156 | Ramp behind the skull door | 2 rooms | 96 % |
| 157 | Door passage | 1 room | 96 % |
| 158 | Long low tunnel | 1 room | 74 % |
| 159 | Stair down to the low tunnels | 3 rooms | 98 % |
| 160 | Low tunnel, east-west | 1 room | 100 % |
| 161 | Low tunnel, north-south | 1 room | 100 % |
| 162 | Low tunnel end | 1 room | 97 % |
| 166 | North-east stair | 3 rooms | 99 % |
| 167 | North-east ramp | 3 rooms | 90 % |
| 168 | North-east ramp, upper leg | 2 rooms | 96 % |
| 169 | North-east cellar | 1 room | 100 % |
| 172 | Tunnel end | 1 room | 96 % |

### Wing 4: gatehouse, throne hall and the inner ranges

62 sectors: 48 drawn as 90 rooms, 14 as the thickness of an opening; compare score 96.7 % over 1026 points.

| Sector | What it is | Drawn as | Score |
|---|---|---|---|
| 75 | Gatehouse | 2 rooms | 95 % |
| 76 | Gatehouse step | 1 room | - |
| 77 | Gatehouse stair | 4 rooms | 99 % |
| 78 | Inner court | 3 rooms | 94 % |
| 79 | Gatehouse stair doorway | 1 room | 93 % |
| 80 | Throne hall | 1 room | 97 % |
| 81 | North gallery of the throne hall | 1 room | 89 % |
| 82 | South gallery of the throne hall | 2 rooms | 90 % |
| 83 | North-west gallery stair | 3 rooms | 99 % |
| 84 | South-west gallery stair | 3 rooms | 99 % |
| 85 | North-west tower room | 1 room | 100 % |
| 86 | South-west tower room | 1 room | 100 % |
| 87 | Gallery passage | 1 room | 97 % |
| 88 | South-east upper hall | 4 rooms | 86 % |
| 89 | Upper east room | 1 room | 98 % |
| 90 | Closet | 1 room | 98 % |
| 91 | Closet doorway | opening | - |
| 92 | Window over the cavern | opening | 94 % |
| 93 | Ramp from the south range up to the upper hall | 4 rooms | 92 % |
| 95 | Gatehouse step | opening | - |
| 96 | Gatehouse stair | 4 rooms | 99 % |
| 97 | Gatehouse stair doorway | 1 room | 97 % |
| 103 | North-east upper hall | 4 rooms | 90 % |
| 104 | Secret room behind the sliding wall | 1 room | 86 % |
| 105 | Upper stair | 3 rooms | 98 % |
| 106 | North-east tower room | 1 room | 98 % |
| 107 | Tower window | opening | - |
| 108 | Tower window | opening | - |
| 109 | Ramp from the north range up to the upper hall | 4 rooms | 94 % |
| 110 | North-east lower room | 1 room | 98 % |
| 111 | Closet | 1 room | 100 % |
| 112 | North-east passage | 1 room | 99 % |
| 113 | Alcove | 1 room | 100 % |
| 114 | North-east corridor | 1 room | 100 % |
| 115 | North room | 1 room | 99 % |
| 116 | North stair room | 3 rooms | 96 % |
| 117 | North range room | 1 room | 100 % |
| 118 | North range corridor | 5 rooms | 100 % |
| 119 | North range room | 1 room | 100 % |
| 120 | North range end room | 1 room | 100 % |
| 121 | Barred room | 1 room | 100 % |
| 122 | South-east room | 2 rooms | 100 % |
| 123 | Doorway | opening | 96 % |
| 124 | South-east corridor | 1 room | 99 % |
| 125 | East lower room | 1 room | 100 % |
| 126 | South range hall | 1 room | 99 % |
| 127 | South range room | 1 room | 99 % |
| 128 | Doorway | opening | - |
| 129 | South range room | 1 room | 99 % |
| 130 | South range room | 1 room | 99 % |
| 131 | South corridor under the gallery | 1 room | 100 % |
| 132 | Doorway | opening | - |
| 133 | South range closet | 1 room | 97 % |
| 134 | South-east lower room | 1 room | 100 % |
| 135 | South range cross passage | 1 room | 99 % |
| 136 | Doorway | opening | 97 % |
| 137 | South range stepped passage | 8 rooms | 99 % |
| 138 | Doorway | opening | 99 % |
| 139 | Doorway | opening | 97 % |
| 140 | Doorway | opening | 99 % |
| 141 | Doorway | opening | - |
| 171 | Doorway | opening | - |

### Wing 5: west ward, west court, wall walk and the outer caverns

29 sectors: 28 drawn as 75 rooms, 1 as the thickness of an opening; compare score 88.8 % over 4440 points.

| Sector | What it is | Drawn as | Score |
|---|---|---|---|
| 71 | North-west cavern | 7 rooms | 87 % |
| 72 | West cavern | 10 rooms | 89 % |
| 73 | South cavern before the gate | 10 rooms | 82 % |
| 74 | East cavern | 3 rooms | 87 % |
| 94 | West court | 4 rooms | 99 % |
| 98 | Wall walk, south | 2 rooms | 100 % |
| 99 | Wall walk, south-west corner | 1 room | 100 % |
| 100 | Wall walk, west | 1 room | 95 % |
| 101 | Wall walk, north-west room | 1 room | 99 % |
| 102 | Wall walk doorway | opening | - |
| 144 | West ward with the sunken ring | 4 rooms | 96 % |
| 145 | South-west hall | 3 rooms | 96 % |
| 146 | Passage to the south range | 2 rooms | 90 % |
| 147 | Doorway | 1 room | - |
| 148 | North-west end room | 1 room | 92 % |
| 149 | North-west hall | 3 rooms | 97 % |
| 150 | North-west great room | 1 room | 95 % |
| 163 | Tall corridor with the long ramp | 3 rooms | 89 % |
| 164 | Lever gallery at the head of the ramp | 2 rooms | 94 % |
| 165 | Cellar under the lever gallery | 5 rooms | 100 % |
| 170 | Crystal chamber | 3 rooms | 90 % |
| 184 | Gate tower, west | 1 room | 99 % |
| 185 | Gate tower, east | 1 room | 93 % |
| 186 | Hidden room behind the gate tower | 1 room | 100 % |
| 187 | Hidden passage | 1 room | 99 % |
| 188 | Secret passage | 1 room | - |
| 189 | Secret passage | 1 room | 95 % |
| 190 | Secret passage | 1 room | - |
| 191 | Secret treasure room | 1 room | 99 % |

### Reached only by teleport

2 sectors: 2 drawn as 3 rooms, 0 as the thickness of an opening; compare score 95.4 % over 21 points.

| Sector | What it is | Drawn as | Score |
|---|---|---|---|
| 192 | Teleport chamber (reached only by teleport) | 1 room | 96 % |
| 193 | The lich's study (reached only by teleport) | 2 rooms | 95 % |

Totals: {'sectors': 193, 'drawn': 156, 'open': 37, 'compared': 166}

## Round two (2026-11-12, the vocabulary after ceilings, slopes, plates and step events)

From this round on the project files are the source: `rooms.yml`, `objects.yml` and `wiring.yml` were edited
directly, and what the sections above say about `run.sh` and `overrides.py` holds for round one only (do not run
them over the project). Where one change touched many rooms it was made by a script that edits the files in place
and whose diff was read: `output/studio_cal/mm6_cd2/tools/apply_lean.py` (the lean rooms of the outer caverns),
`rehome.py` (objects moved to the piece of their sector they stand in), `events_r2.py` (plates, panels, events).
`tools/loop.sh` is the round's loop (fmt, validate, build, compare, per-sector summary); `ceil.py`, `vault.py`,
`edges.py`, `offs.py` and `sec.py` only read and measure. The project as round one left it is in
`output/studio_cal/mm6_cd2/backup_r2_start/`.

### Scores

| | start of round two | end |
|---|---|---|
| `oymap compare` score | 87.7 % | **92.1 %** |
| distances agree | 87.7 % of 415,050 rays | 92.7 % of 418,550 |
| textures agree | 95.4 % | 95.9 % (97.3 % where distances agree) |
| points without a floor in the rebuild | 212 of 8,513 | 142 |
| mean ceiling difference | 97 | 32 |
| castle alone (3,795 points): score, distances, textures | 94.7, 94.6, 95.1 % | 96.1, 96.1, 96.0 % |
| caves alone (4,718 points): score, distances, textures | 82.1, 81.5, 95.6 % | 88.9, 89.9, 95.9 % |

Step by step (score): 87.7; 89.7 the south cavern as one room under its dome and the two tunnels to their rim;
90.8 lean rooms in caverns 71 to 74; 91.2 cavern 66 in three parts; 91.4 the great hall's vault and west rock;
91.7 the gate ramp read as a ramp; 91.9 the cubes hanging (round one's blocks stood on the floor); 92.1 the
dropped arches and the window. By sector: 1 58 to 87 %, 143 45 to 83 %, 142 57 to 77 %, 56 82 to 89 %,
72 89 to 93 %, 71 87 to 90 %, 73 82 to 87 %, 66 81 to 85 %, 74 87 to 88 %, 57 95 to 99 %, 170 90 to 96 %;
4 (the battlement gallery) stays at 79 %.

Rooms: 335 (309). Reached on foot with every door out of the way: **322 of 335** (283 of 309): the wall walk and
its towers are now reached as the original reaches them, by the ramp before the gate and door record 9. `oymap
solve` opens the rebuild in the original's order and now by the original's means: step 1 the stair door and the
great hall's cube (teleports, and the portcullis once the lever is thrown), step 2 the doors behind, the throne
hall's cube (the forcefield) and the chamber's panels, step 3 the crystal chamber's cube; 323 of 335 in the end (the original 180 of 194).
`compare.py`: 15 in, 15 near, 5 out (more rooms per sector than round one, so more counts drift).

### What changed

- **South cavern (1)**: one convex room whose outline is the rim; the dome as three ceiling levels one on another
  (rim -40, the original's ring at 828, its ring at 1,746, the point at 2,160 against the castle wall), upright
  along the castle wall. The seven bank rooms are gone: the floor is level to the rim and the rim is a wall 200
  high. The two steps before the door are platforms against the wall.
- **Tunnels 142 and 143**: read again. Their floors do not slope: they are tubes (level floor about 500 wide,
  banks to the rim, a ceiling leaning in to a ridge strip that climbs toward the cavern in 142). Drawn to the rim
  with upright walls; 142's ridge climb is a `ceiling_slope`, 143's ridge a level ceiling at 180.
- **Outer caverns (71, 72, 73, 74 and the west of 66)**: the main room now ends where the original's ceiling
  reaches its flat top (1,170); between it and each bank stands a lean room (level floor, `ceiling_slope` from
  1,170 down to the height measured over the old edge, 590 to 940), 29 of them, and each bank's ceiling slopes on
  down to the rim. Depths (350 to 1,400) and heights are measured per edge from the original's ceiling faces.
- **Cavern 66** is three rooms: the west part under the flat top, a middle room whose ceiling comes down to 828,
  and the east chamber at 828 with its own vault (a leaning ceiling level from the ring at 828 to the ridge at
  1,128).
- **Great hall (56)**: 828 at the walls, two leaning ceiling levels one on the other (1,428, the crown at 1,920
  along the south wall), the west rock as two rooms whose ceilings slope down to the floor at the west wall, the
  shaft of the cube as a beam; the second balcony arch and the west arch under the gallery window (`from_wall`,
  `to_wall`, an opening over another).
- **The gate ramp (73)**: round one drew the ramp along the castle wall as a rock bank sloping toward the cave
  (and door record 9 in a drop of 780). It is a ramp from the cave floor up to a landing at 600, door record 9
  in the wall behind the landing, the bridge between the gate towers behind it.
- **The three teleporter cubes** hang (three blocks one on another with a `base`); round one's `levels` under
  them, which made them stand on the floor, are gone.
- **The window from the upper hall (176) into the east tall hall (8)**, over the door to the anteroom.
- **Events**: 38 floor plates, 5 panels as switches, 31 new events (45 in all). Of the 32 plates and faces that
  were placeholders, 28 are wired: the 11 traps (2, 3, 19 to 25, 27, 46) on plates where the original's
  pressure-plate faces lie, the 7 summons (26, 47 to 52, with `not: {qbit: 1033}`), the teleport chamber's panels
  (43) and the study's (44) as switches with the `teleport` preset, and the three cubes' twelve sides (28 to 31,
  33, 35, 36, 38 to 41) as a plate on the floor before each side. The levers now do what the original's do: they
  light a cube (a map variable), and the cube then lowers the portcullis or clears the forcefield instead of
  teleporting; the crystal chamber's sign sends its cube's travellers to the lich's study. Still placeholders
  (8 events): the cubes' undersides (32, 37, 42: a plate under a hanging block is refused), the podium (34: a
  clicked desk top; so quest bit 1033 is never set and the summons never stop), the forcefield's face (58, 59),
  the sarcophagi (61 to 63: a question), and the crystal (57, a clicked decoration, never listed).

Playtest (`playtest.yml`, run from `output/studio_cal/mm6_cd2/run`, about 13 minutes, log
`output/studio_cal/mm6_cd2/playtest_r2.log`): **passes, 107 steps** (round one: 60). It plays the puzzle as wired: the great hall's cube
before the lever (the party is sent to the teleport chamber; a panel there sends it back to the cross hall), the
east lever (the portcullis stays shut), the cube again (the portcullis opens and the party stays), the north
cavern, gatehouse and throne hall, the west lever (the forcefield stays shut), the throne hall's cube (the
forcefield opens), the west ward and court, the crystal chamber's sign and cube (to the lich's study), the chest
(`chest_opened`), the study's panel (to the end of the low tunnels) and the exit (its prompt answered, the map
changes to outc3.odm). The exit is run from the tunnels' end by its event, not walked to. Things learnt on the
way: a `via` point on a teleport plate needs a small `radius` on the walk; after a run down a ramp the party is
still in the air for a moment (a `wait(1)` before the height is asserted); the planner aims at the 210 step
between the west ward's floor and the forcefield's landing instead of the ramp beside it (waypoints added: the
same kind of defect round one met at the south-west hall's steps).

In-game pairs (`ingame_compare.py --root output/studio_cal/mm6_cd2/root`, 9 cameras of
`output/studio_cal/mm6_cd2/shots_r2.yml`, sheets in `output/studio_cal/mm6_cd2/ingame_r2/diff`): edge agreement
0.90 (0.85 at round one's cameras). Looked at: the south cavern reads as a cave now (the dome comes down to the
rim on every side; toward the castle the wall is blank where the original shows the gallery's two openings and
lights, and the door is a plain rectangle where the original's has cut corners); the great hall shows the cube
hanging on its shaft at the original's size and the vault's lean; the outer caverns show the lean of the roof
toward the rim (a strip of castle stone shows through at one lean room's edge in `07-gate-cavern-lean`: two
walls in one plane, as the build warns); the gate ramp is a walled slab against the castle wall where the
original's ramp is open; the original's floor mist is missing everywhere, as before.

`L4/build/` holds round one's build (kept because `oymap install` once read it); this round built into
`output/studio_cal/mm6_cd2/build` and installed with `--build`.

### New features: what worked

`ceiling_levels` without an outline (standing on the walls) with `top_outline`, and levels on a level's flat top
to three deep (the dome); a leaning level with an outline of its own inside a room that bends (66 east, 56);
`ceiling_slope` in level rooms, over slopes (the banks: `slope` and `ceiling_slope` toward the same wall with
different rises) and with openings in the raking side walls; `from_wall`/`to_wall` (five openings); an opening
above another in one wall (176 over the anteroom door, the gallery window over the west arch); platforms
against a wall and hanging blocks stacked with `base`; a beam 1,530 deep as a shaft; plates; `trigger: step`
with `sources`; `condition` with `not` and `else_effects`; the effects `summon`, `teleport`, `cast` (with a
target) and `lua`; the `teleport` preset with a switch as its source and with a plate; `solve` following
teleports and step events.

### New features: what did not work (repro projects in `output/studio_cal/mm6_cd2/repro/`)

1. **A leaning side that is not flat passes `validate` and is refused by `build`** (`repro/nonplanar_side`):
   `rooms.yml: the indoor compiler refused the lowered map: indoor native face is non-planar after coordinate
   quantization: 5`. With `top_outline` every side must lie in one plane (the top edge parallel to the outline
   edge, or one point, or the whole side upright with its top points moved along the wall, never left on the
   corners while the next side leans). The schema says none of it and the message names a face number, not the
   room or the level. Either triangulate such sides or refuse them in `validate` with the level and side. (The
   dome of sector 1 has sides that are not exactly flat and builds; where the limit lies was not found.)
2. **Two rooms under ridge or dome ceilings cannot be joined over their whole section** (`repro/tube`):
   `width: full, height: full` between two whole-ceiling levels with the same upright end builds an opening up
   to the eaves and leaves both gable ends walled above it; `shape: gable` with its apex in the gable is refused
   (`a gabled opening's apex ... at least 16 below the lower of the two ceilings`). Since a whole-ceiling level
   needs a convex room, a bent tunnel under a ridge (142, 143) and a cave of several convex parts under one
   leaning ceiling cannot be said. Wanted: `height: full` between two upright ends follows their common top
   line.
3. **An opening may rise into the upright end of the first whole-ceiling level only, and must begin under the
   eaves** (`repro/nested_gable`, `repro/gable_window`): `the opening reaches 1000 but ... the wall over it (the
   upright end of a ceiling level) takes an opening up to 584`, though a second level's upright end stands above
   it on the same wall; and `an opening that rises above the ceiling into the upright end of a ceiling level is
   a rectangle that begins at least 16 under the ceiling`. So the battlement gallery's two openings into the
   south cavern (588 to 1,170 in the castle wall, which is the dome's upright side from -40 up) are still not
   drawn, and sector 4 keeps its blank wall.
4. **The same holds beside a sloping ceiling**: an opening in a wall a ceiling rakes along ends at the ceiling's
   lower side, so every lean room and every bank stands between triangles of wall (29 lean rooms: a rib of rock
   under the leaning roof every 1,000 to 4,000 units, where the original has one unbroken lean). This is the
   round's largest remaining artefact. Wanted: an opening whose top follows the raking ceiling, or ceilings
   that lean in a room that is not convex (a `ceiling_levels` entry whose sides lean, standing on the walls of
   any room).
5. **A plate under a hanging platform is refused** (`repro/plate_under_platform`): `the plate lies on a level,
   platform or flight of room:a`, though the block hangs 308 above the floor; and the wiring check then adds a
   wrong second message: `plate:under is a plate, which is clicked: a step event's source is a room, a level or
   platform with an id, or a plate (put a plate in front of it)`.
6. **A plate with corners exactly 16 from the walls is refused** (`repro/plate_16`) with a message that asks
   for "at least 16"; 17 is accepted.
7. **Three rooms opening side by side into one wall of a fourth cannot all be `width: full`**: `two openings
   in one wall of room:s066_m overlap or stand closer than 16 units`. Posts 17 wide stand between the lean
   rooms' ends and the west part of cavern 66 where they meet the middle room.
8. **`cast` needs a `to` point and a mastery of normal to grandmaster**; ten of the eleven traps give no target
   (0, 0, 0) and three pass 8 or 10 where the mastery goes: said with `lua` as the original's own call.
9. **A beam's check reads a wrong ceiling under nested levels** when the sides are not flat: with the first
   (refused) form of the great hall's vault it reported `the ceiling of room:s056 at that place is at 1791`
   under what the project gave as the flat top at 1,920. Not seen again with flat sides.
10. `beams[].notes` is refused (`unknown key`) where rooms, levels and platforms-by-id take notes.

### Gaps still open, most harmful first

1. **Rock banks and uneven floors** (as before): the banks of the five outer caverns are still slope rooms
   between walls with wedges of solid rock between neighbours, and about ten stretches of rim have none (two
   banks round a corner overlap; a mitred bank would need a slope room that is not a parallelogram and openings
   in its sloping sides). 142 of the comparison's points have no floor in the rebuild, nearly all here; the
   south cavern's, the tunnels' and the great hall's rising ground is level.
2. **Leaning ceilings over rooms that are not convex, and openings under them** (points 2 to 4 above): the ribs
   between lean rooms; the walls that stand upright to 828 round the east chamber of 66 and the great hall's
   north and east sides start too low or too high; 142 and 143 keep upright walls.
3. **Windows high in the end wall of a vaulted room** (point 3): the battlement gallery over the south cavern.
4. **A ramp open to the room it climbs along**: the gate ramp is a walled box against the castle wall (the
   in-game picture `08-gate-ramp` shows a slab where the original has an open ramp); 163's long ramp as before.
5. **A clicked face that is not a door, a chest or a panel on a wall**: the cubes' sides are stood in for by
   plates before them (the party is sent off by walking up to a side, not by clicking it; walking under a cube
   crosses its plates), the podium and the crystal not at all. Wanted: `source:` a platform's side or top with
   `trigger: click`.
6. **Events that ask** (the sarcophagi), **texture changes on a block** (the cubes' water turning to lava is
   the puzzle's only hint), **levers that switch back** (the original's toggle a variable; `sets` only sets).
7. As round one: sideways sliding doors, the forcefield as a door, the turning stair, floor mist, fixed actors
   and floor items, wall texture offsets.

Unsure of: whether a zero target in the original's `CastSpell` means "at the party"; the height of the dome's
rim (the original's rim runs from -30 to -90 and to +60 in the two north corners; -40 was taken); 142's ridge
height at the cavern's mouth (450 to 540; 500 taken).

## Round three (2026-11-12, events, moving parts, climbing paths and surfaces)

The project files stay the source. Changes that touch many entries were made by helpers that edit the files in place
and take every number from the original's export (`output/studio_cal/mm6_cd2/tools_r3/orig_r3.json`); their diffs
were read: `cubes.py` (the three teleporter cubes), `objects_r3.py` (podium, lever covers, the second plate of event
20), `doors_r3.py` (sideways doors and leaf textures), `portcullis_r3.py` (sector 67 and the portcullis block),
`ramps_r3.py`, `ramps_r3b.py`, `ramps_r3c.py` (rejoined ramps), `threshold_r3.py` (doorway floors), and
`merge_events.py`, which merges the hand-written `events_r3.yml` into `wiring.yml`. `yio.py` reads and writes the
YAML (keeps `on`/`off` as strings); `loop.sh` is the round's loop. Read-only measuring: `evfaces.py` (every face and
sprite of the original with an event), `secfaces.py`, `rampceil.py`, `ceilgrid.py`, `texarea.py`, `mixedwalls.py`,
`pieces.py`, `where.py`. The project as round two left it is in `output/studio_cal/mm6_cd2/r3_backup/`.

### Scores

| | start of round three | end |
|---|---|---|
| `oymap compare` score | 92.1 % | **92.3 %** |
| distances agree (shape) | 92.7 % of 418,550 rays | 92.9 % of 418,550 |
| textures agree | 95.9 % (97.3 % where distances agree) | 96.3 % (97.7 %) |
| mean ceiling difference | 32.3 | 31.8 |
| castle alone (3,795 points): score, distances, textures | 96.1, 96.1, 96.0 % | 96.4, 96.4, 96.5 % |
| caves alone (4,718 points): score, distances, textures | 88.9, 89.9, 95.9 % | 89.0, 89.9, 96.1 % |

By sector: 20 (the long ramp) 90 to 99.6 %, 36 83 to 93 %, 93 92 to 98 %, 109 94 to 99 %, 167 90 to 100 %, 104 (the
secret room) 86 to 98 %, 58 (north passage) 94 to 99 %, 103 90 to 95 %; the caves did not move (nothing this round
touches them). `compare.py`: 16 in, 14 near, 5 out. Comparison output: `output/studio_cal/mm6_cd2/compare_r3` (start)
and `compare_r3_end`.

Rooms: **331** (335): sector 67 (the portcullis arch) and the closet of sector 104 are rooms now; seven ramp pieces
were joined into their ramps. Reached on foot with every door out of the way: **318 of 331**. The 13 not reached:
the arrow slit s030 and the barred room s121 (the original does not reach them either), the teleport chamber s192 and
the lich's study s193 (reached only by teleport, as in the original), and nine raised ledges and window bays whose
sill is above a step (s075_a, s078_a, s078_b, s082_a, s098_a, s164_a, s170_a, s170_b and one more). `oymap solve`:
**321 of 331** in the original's order: wave 1 door record 1 and the great hall's cube (which lowers the
portcullis), wave 2 door records 4, 8, 9 and the throne hall's cube (the forcefield), wave 3 door records 6 and 7 and
the crystal chamber's cube; the original's waves are the same. Door record 5 opens in wave 1 here and in wave 2 in
the original, because the original's leaf faces both belong to sector 159 (behind it) while the rebuild's door is in
the passage's wall; a player clicks it from the passage in both. Never reached by `solve`: the five raised ledges and
the barred room.

Playtest (`playtest.yml`, run from `output/studio_cal/mm6_cd2/run`, log `output/studio_cal/mm6_cd2/playtest_r3.log`):
**passes, 150 steps** (107). New in it: every cube is used by clicking its panel from the floor (`set_pose` and
`press_interact`, which also proves the panels are clickable); the east sign lowers the stone over the east lever,
the lever is pulled off and on again (the original's toggle); the portcullis is the block in the arch; the secret
room's sliding block (door record 8) is opened and the closet behind it walked into; the west sign and lever likewise;
the throne hall's cube clears the forcefield and sets the "used" variable; the crystal chamber's cube is clicked; the
podium is clicked and quest bit 1033 is checked; the chest's window is closed before walking on. The levers
themselves are pulled by event (`click`): the headless keyboard pick finds no target once the cover has moved (see
tool defects); the desktop game's use key pulls the uncovered lever
(`output/studio_cal/mm6_cd2/tools_r3/cover_tour2.yml`, picture `tools_r3/caps/lever-after-trigger.png`).

In-game pairs (`ingame_compare.py --root output/studio_cal/mm6_cd2/root`, 12 cameras of
`output/studio_cal/mm6_cd2/shots_r3.yml`, sheets in `output/studio_cal/mm6_cd2/ingame_r3/diff`): edge agreement
0.85. Looked at: the three cubes read as the original's (stone frame, water panels flush, the shaft; 0.92 in the
great hall); the arch with the portcullis block shows the same wall and opening above it; the four ramps and the
secret room read as the original (remaining edges are wall courses a few units off, a known gap); the podium stands
where the original's does with a flat top where the original's slopes; the floor mist is missing everywhere, as
before. The original's lever closet shows two red patches on its west wall that the rebuild lacks; every face there
is plain castle stone in the original's data, so it is not geometry or texture (a highlight or a light effect: not
understood).

### Events: each of the original's handlers and how the rebuild has it

Read with `oymap flow cd2.blv --world mm6 --assets assets_dev` and the faces and sprites that carry each number
(`tools_r3/evfaces.py`). 54 of the original's numbers are bound to a face or a sprite; 59 and 64 are bound to nothing
(face 4522, the forcefield, carries 58), and 65000/65001 are MMerge's global events for Nicolai, not this map's.
**41 do the same thing under the same condition; 6 do the same but miss a texture change or show their text as a
status line; 3 differ in where or how far; 4 are missing.**

| Original | What it does | Rebuild | |
|---|---|---|---|
| 1, 4 to 7, 9 | sideways doors (records 1, 4, 5, 6, 7, 9) | `door` presets on `slide_left`/`slide_right` doors with the leaf textures | same |
| 8 | door record 8, a stone block that slides 255 of its 381 and shows a closet | `door` on the closet's doorway (room:s104_c), 222 wide at the passage's east end | differs: the doorway opens 222 where the original's opens 258 |
| 10 | chest | `chest` | same |
| 2 | toxic cloud of skill 10 from the south cavern, from three floor faces and from clicking the portcullis | plate:trap02 and an event on mover:portcullis, the original's call | same |
| 3 | ice blast, skill 8, four plates | four plates, the original's call | same |
| 19 | four fireballs of skill 10 | plate, the original's calls | same |
| 20 | toxic cloud from two floor faces (cell 42, the doorway of cell 45) | plate in cell 42 and one just inside cell 45 (a doorway has no floor); `cast` | differs: the second plate is the first 96 of the cell behind the doorway |
| 21, 22 | three ice bolts | two plates, one event; `cast` to [0, 0, 0] | same |
| 23, 24, 25, 27, 46 | fireballs | plates; `cast` (25 with its targets) | same |
| 26, 47 to 52 | three monsters of slot 1, tier b, until the Book of Liches is destroyed | plates; `summon` under `not: {qbit: 1033}` | same (the podium now sets the bit, so the summons stop) |
| 28 to 32 | the great hall cube's five panels, clicked: unlit, teleport (four places); lit, lower the portcullis and say so | five movers clicked (`switch`, `condition`, `else_effects: teleport`, `opens: [mover:portcullis]`) | same |
| 33, 37 | the throne cube's north, south and under panels: with the variable at 1, raise it to 2 and clear the forcefield; otherwise teleport | three movers; "1" is west_embers set and west_way_cleared not, "2" both set | same |
| 35, 36 | the throne cube's west and east panels: at 0 an explosion and a longsword (SummonObject), at 1 clear the forcefield, at 2 nothing | two movers; the third outcome by a Lua line in `else_effects` | same |
| 38 to 42 | the crystal cube's five panels: with its sign read, to the lich's study; otherwise four places | five movers, `teleport` with `condition` and `else_effects` | same |
| 34 | the podium: destroy the Book (quest bit 9, 1033 merged) and change the desk top's texture | a mover clicked, `effects: [{qbit: 1033}]`, `locked_text` | differs: the desk top keeps its texture |
| 43 | the teleport chamber's four panels | four switches, `teleport` | same |
| 44 | the study's lava panel, clicked (the wall also has the pressure-plate bit) | switch, `teleport` | same |
| 45 | the crystal chamber's sign, a toggle: lit (message, lava textures, the water bit on the cube's faces) or unlit | switch with `condition`, `sets`, `else_effects: set 0` | differs: no texture change |
| 53, 55 | the signs: a message box, and the stone over the lever's niche moves (records 13, 11) | switch with `text` and `toggles: [mover:cover_e / cover_w]` | differs: a status line, not a message box |
| 54, 56 | the levers, toggles: the cube lit or unlit, the handle moves (records 14, 12), the cube's textures | switches with `condition`, `sets`, `else_effects` (and the switch's plate texture set back by Lua) | differs: no cube texture change; 56's slips (it moves record 14 and resets face 4269 twice) not copied |
| 57 | the crystal (a sprite, clicked): Memory Crystal Delta, quest bit, sprite change | none | missing: a decoration cannot be an event's source |
| 58 | on load: textures and sprite by the variables, the forcefield's bits | none | differs: the forcefield is a door whose state the save keeps; textures and sprite cannot be said; a `trigger: load` event with this condition made `solve` open the forcefield at the start (see tool defects) |
| 60 | the way out | `exit` | same |
| 61 to 63 | the sarcophagi: a question, then an item and a reputation loss | none (placeholders) | missing: a handler cannot ask a question and continue with the answer |

### What changed

- **The three teleporter cubes** are built as the original's: a 256 frame of stone (four corner columns, four
  strips round the underside's panel and the top slab, as platforms) with five water panels flush in it, each a mover
  the player clicks, and the shaft to the ceiling as a beam (the throne hall's and the crystal chamber's shafts were
  missing). The twelve plates in front of the cubes and the three placeholders for the undersides are gone.
- **Events**: 53 (45); see the table.
- **Doors**: the seven sideways doors are `slide_left`/`slide_right` with their leaf textures. Door record 8 was on
  the wrong doorway (rounds one and two closed the plain doorway from room:s103 with it); it is now the block in
  front of the closet that the original hides with it, and sector 104's closet is a room (ceiling 810). The
  portcullis is what the original has: a block 1216 by 80 by 180 that sinks into the floor of the arch (sector 67,
  now a room), with the arch open above it, instead of a door filling the doorway. The levers hide behind stone
  panels that the signs beside them lower (door records 13 and 11).
- **Ramps**: the straight ramps of sectors 20, 36, 93, 109 and 167, cut in two or three pieces with stepped
  ceilings, are single ramps under sloping ceilings; 93 and 109 keep one cut where a corridor runs under their high
  ends (both pieces in the same planes). The vaults over 36, 93 and 109 are their mean plane.
- **Surfaces**: `threshold` on the 36 doorways that stand for the original's doorway sectors (their floor tile:
  crdrf2, castle stone on the balcony arches, d2flor4 on the wall walk), where the doorway floors had taken the wall
  stone; two `panels` (castle stone over the gate tower's door, a corner strip and a trim in the study).

### New features: what worked

Movers clicked as event sources (`switch` and `teleport` presets with `condition` and `else_effects`), hanging over
a platform's top, given by `outline`, side by side and touching platforms; a mover that sinks (the portcullis, the
covers) and is toggled and opened by events and walked over once sunk; `slide_left`/`slide_right` doors (their
direction checked against the original's records); `else_effects` with `set` (toggles, three-state variables);
`cast` with a target of [0, 0, 0] (the original's: the game aims at the party); `threshold`; `panels`; ramps with
`ceiling_slope` rejoined. Not used, because Darkmoor has none: `leaves: 2`, `stretch`, `kerbs`,
`auto_return_seconds`, lifts with `thickness`, `back_surface` (the original's leaves carry one texture on both
sides), `tread`/`top_surface` (the original's treads are its floor tile), `ends` (the original's corner strips have
two textures, `d2wlale` left and `d2wlare` right; `ends` takes one).

The climbing `path` room has no honest use here: Darkmoor's tunnels that bend (142, 143) are level tubes, its
passages that climb (118, 137) step up and down, the straight ramps are better said as ramp rooms, and the spiral
stays 20 rooms. Uneven cave floors still cannot be said; the caves are as round two left them.

### New features: what was refused (repro projects in `output/studio_cal/mm6_cd2/repro/`)

1. **A block the player clicks that does not move** (`repro/mover_static`): `objects.yml: movers[0].travel: the
   travel is nothing: give at least one of x, y and z a whole number other than 0`. The cubes' fifteen panels and the
   podium are movers with `travel: [0, 0, 1]` that no event ever sends (a stand-in, said in each one's notes).
   Wanted: `source:` a platform (with an `id`) and `trigger: click`, or `travel` optional on a mover.
2. **A ceiling level in a room with a sloping ceiling** (`repro/ramp_vault`): refused with `rooms[1].ceiling_levels[0].
   ceiling: a ceiling level is a simple counter-clockwise outline at a ceiling height above the room's` (the message
   ends there); with a height above the slope's top it builds a level that is flat at that height. So a vault that
   climbs with its ramp (36, 93, 109) is a plane at the vault's mean.
3. **A sloped room over a room that runs under its high end** (`repro/ramp_stack`): `rooms room:ramp and room:under
   overlap: two rooms cannot share space`, though the ramp's floor is 113 above the lower room's ceiling there: the
   check takes the ramp's lowest floor. Sectors 93 and 109 stay in two pieces for it.
4. **`notes` on a panel**: `rooms.yml: rooms[133].walls[0].panels[0].notes: unknown key` (as `beams[].notes` in
   round two). Shown by `oymap validate` on any project with a panel that has `notes`.

### Gaps still open, most harmful first

1. **Rock banks and uneven floors** in the five outer caverns, the south cavern, tunnels 142/143 and the great hall's
   west rock (as round two): 142 comparison points without a floor; the caves are 89 % against the castle's 96 %.
   Wanted: levels that may slope and touch walls, or height points.
2. **Leaning ceilings over rooms that are not convex, and openings under them**: the ribs between lean rooms (29
   lean rooms), the battlement gallery's blank wall (round two's `nested_gable`, `gable_window`).
3. **A fan vault from an off-centre apex** (the great hall, 7.7 % of the loss: triangles from (14848, 6784, 1920) to
   the east wall at 1218, to the north-east corner at 828 and a flat crown along the south wall to its east end; the
   rebuild's crown ends 2,000 short of the east wall and its east part is 500 to 1,000 too low). Nested whole-ceiling
   levels can lean each side by one plane only (round two's `nonplanar_side`); the fan needs sides that are not
   planar quads or levels with any number of sides.
4. **The upright side of a whole-ceiling level takes the ceiling's surface** (tool defect 2 below): the castle wall
   in the south cavern (810 units of area) and the great hall's south wall above 828 show rock where the original
   shows castle stone; this is most of those two sectors' texture loss.
5. **A clicked block** (refusal 1), **a decoration as an event's source** (the crystal, event 57), **a question with
   an answer** (the sarcophagi, 61 to 63), **texture changes on faces other than a switch** (the cubes' water turning
   to lava, the only hint of the puzzle; the podium's desk top), **an invisible blocking face** (the forcefield, drawn
   as a lava-textured door; its second face across the foot of the court's corner stair is not drawn).
6. **A sideways door that moves less than its width** (door record 8: 255 of 381) and **a door leaf lower than its
   opening** (the portcullis was one; now a mover, which works because sector 67 is a room).
7. **A step inside a doorway** (76 and 147): `threshold` gives the doorway floor a surface, not a step; the doorway
   sectors stay rooms 96 deep.
8. As before: the turning stair, floor mist, fixed actors and floor items, wall texture offsets, `ends` with two
   surfaces, a sloping top on a block (the podium).

### Tool defects

1. **`cast` writes mastery and level in the wrong order.** The game's `evt.CastSpell(spell, skill, mastery, ...)`
   (as the shipped `cd2.lua` calls it: `CastSpell(90, 10, 1, ...)` is skill 10 at novice;
   `IndoorWorldRuntime::castEventSpell(spellId, skillLevel, skillMastery, ...)`) gets `CastSpell(spell, mastery,
   level, ...)` from `core/IndoorLowering.cpp`. `oymap build output/studio_cal/mm6_cd2/repro/cast_order --assets
   assets_dev --out <dir>` writes `evt.CastSpell(6, 1, 10, ...)` for `mastery: normal, level: 10`, which casts skill 1
   at mastery 10. Any `cast` with a level above 1 is wrong in the game; events 2, 3 and 19 keep the original's call.
2. **The upright side of a whole-ceiling level is built with the ceiling's surface**, where the schema says `edge`
   defaults to "the room's wall for upright ones": `oymap build output/studio_cal/mm6_cd2/repro/upright_edge
   --assets assets_dev --out <dir>` builds the upright south side in d2ceil3.
3. **A mover's `bottom` is measured from the top of the highest platform at its place, even one above the mover**
   (`repro/mover_under_platform`: `the mover's top at its start is at 1103, above the ceiling ... (1000)` for a
   mover 334 above the floor under a stack whose top is at 564); the schema says "from the room's floor at its
   place", and movers have no `floor_height`. The cubes' panels are given bottoms of -230 and -256 for this.
4. **A mover's half-unit `at` is rounded before its `size` is applied** (`repro/mover_half_at`: a 205-wide block at
   512.5 stands at 411 to 616; a platform with the same numbers at 410 to 615). The panels are given by `outline`.
5. **`solve` takes every branch of a condition**, so a `trigger: load` event whose condition nothing has set yet opens
   its doors in wave 1 (`oymap solve output/studio_cal/mm6_cd2/repro/solve_load_condition --assets assets_dev`:
   `event 1 (run by the map): door 1 open`). Darkmoor's load event (58) is left out for this.
6. **`solve` could not open door record 6 from the gate tower** while its opening ran from the hidden room
   (room:s187) to the tower: the leaf's faces belonged to the hidden room's sector only, and the walk never reached
   it. With the opening turned round (from the tower) wave 3 opens it, as the original's. A two-room project does not
   show this (the door there is credited to the start room), so the cause is not pinned down; before the change
   `oymap solve devdocs/map_studio/briefs/mm6_cd2/L4 --assets assets_dev` listed 186 and 187 as never reached.
7. **Headless `press_interact` does not see a mover where it has moved to**: with the stone over the east lever
   lowered, `output/studio_cal/mm6_cd2/tools_r3/lever_test2.yml` (run like the playtest) finds no target; with it up,
   the lever is picked through it. The desktop game picks the uncovered lever (`cover_tour2.yml`). This is the game's
   scenario runner, not the studio.
8. `oymap solve <project>` on a project without `map_stats` fails with `invalid node; first invalid key: "map_stats"`
   (any repro without it).
9. The built door records carry the direction opposite to the original's for the same movement, and state 2 where
   the original's carry 0 (`oymap export <built blv> --world mm6 --assets <installed root>` beside the original's
   export): consistent in the game, but anyone comparing the two exports must know it. And `oymap export` of a built
   map lists its doors only after `oymap install --root` into a scratch root (with `--world`).

Round two's repros (`nonplanar_side`, `tube`, `nested_gable`, `gable_window`, `plate_under_platform`, `plate_16`)
behave as before.

### Unsure of

- Whether the original's keyboard (space bar) interaction can pull a lever behind its stone cover: in this engine the
  keyboard pick saw the lever through the shut cover in one headless run; a mouse click hits the cover.
- The red patches on the lever closet's west wall in the original's picture (above).
- Whether the forcefield's second face (4575, across the foot of the court's stair) mattered to play: with both faces
  the stair corner between them is shut off from both sides until the forcefield is cleared; here the court can walk
  up to the doorway.

## Round four (2026-11-12, night: uneven floors and roofs, tunnels, `cast`)

The project files stay the source. Edits over many rooms were made by helpers in `output/studio_cal/mm6_cd2/tools_r4/`
that take every number from the original's export (`tools_r3/orig_r3.json`, read with `secv.py`); their diffs were
read: `caves_r4.py` (the five outer caverns and the south cavern: outlines, floor and roof points, openings),
`caves_r4_lib.py` (the original's own triangle edges between the points kept, as `floor_lines`/`ceiling_lines`, and
T-vertices left out), `hall_r4.py` (the great hall), `ramps_r4.py` (36, 93, 109), `coves_r4.py` (80, 81, 82),
`ward_r4.py` (144), `cast_r4.py` (events 2, 3, 19); the low tunnel (158), door 5 and s044's coffer edge were edited by
one-off snippets recorded in the same notes. Read-only: `secv.py`, `pts.py` (sums `points.json`), `bisect_s001.py`,
`bisect_win.py`. `loop.sh` is the round's loop. The project as round three left it is in
`output/studio_cal/mm6_cd2/r4_backup/`.

### Scores

| | start of round four | end |
|---|---|---|
| `oymap compare` score | 92.3 % | **94.9 %** |
| shape (distances agree) | 92.8 % of 418,300 rays | **98.6 %** of 425,300 |
| textures agree | 96.4 % | **86.6 %** (see below) |
| mean ceiling difference | 31.8 | 7.0 |
| points without a floor in the rebuild | 146 | 6 |
| castle (3,794 points): score, shape, textures | 96.5, 96.4, 96.6 % | 98.4, 98.5, 98.1 % |
| caves (4,718 points): score, shape, textures | 88.9, 89.8, 96.2 % | 92.1, 98.6, 77.4 % |

By sector (score; shape): 73 86.0 to 92.5 (88.7 to 98.8), 66 85.3 to 91.6 (86.7 to 98.8), 71 89.8 to 92.8 (92.0 to
99.0), 72 93.2 to 92.4 (92.7 to 99.4), 74 88.2 to 92.0, 1 87.8 to 91.8 (86.6 to 97.8), 56 89.4 to 98.2, 4 (the
battlement gallery) 78.9 to 97.4, 158 73.6 to 100, 36 93.1 to 98.8, 93 98.1 to 99.4, 80 98.2 to 99.7, 81 89.2 to
97.3, 82 90.8 to 99.0, 144 96.2 to 99.1. Comparisons: `output/studio_cal/mm6_cd2/compare_r4_start` and
`compare_r4_end` (steps between: `compare_r4_a` to `compare_r4_l`). `compare.py`: 25 in, 5 near, 5 out (16, 14, 5).

**Where score and the original's shape pulled apart.** The caves' shape went from 89.8 to 98.6 % and their textures
from 96.2 to 77.4 %: an uneven floor takes one surface, so the rock banks (the original's d2ceil3) are drawn in the
level floor's crdrf2 (50,718 rays, 12 % of all; drawing the whole floor in d2ceil3 instead scores the same, 46,491
rays the other way, so the floor's own tile was kept). Sector 72 scores lower than at the start (93.2 to 92.4) with
its shape 92.7 to 99.4. The honest shape was kept. Round three's banks as slope rooms had the right tile because each
was a room; they stood between walls.

Rooms: **258** (331): the caverns are one room per original sector (74 is part of 66's room, see below), the great
hall one room, the ramps 36, 93 and 109 one room each, the west ward one room. Reached on foot with every door out of
the way: **245 of 258**; the 13 not reached are round three's (the arrow slit, the barred room, the teleport chamber
and the lich's study, nine raised ledges and bays). `oymap solve`: **248 of 258 in three waves, in the original's
order**: wave 1 door records 1 and 5, the east sign's panel and the great hall's cube (the portcullis); wave 2 door
records 4, 8 and 9, the west sign's panel and the throne hall's cube (the forcefield); wave 3 door records 6 and 7 and
the crystal chamber's cube (log `tools_r4/solve_r4.txt`). As in round three, door record 5 opens in wave 1 here and in
wave 2 in the original.

Playtest (`playtest.yml`, run from `output/studio_cal/mm6_cd2/run`, log `output/studio_cal/mm6_cd2/playtest_r4_end.log`):
**passes, 169 steps** (150). New: a walk into the south cavern under its dome and back, and a loop round the outer
caverns: the east cavern, the south cavern before the gate, up the ramp block along the castle wall to the landing at
600 before door record 9 (height asserted), the west cavern, and back to the gatehouse. The west ward's ramp (now a
block open to the ward) is walked as before.

In-game pairs (`ingame_compare.py --root output/studio_cal/mm6_cd2/root`, 16 cameras of
`output/studio_cal/mm6_cd2/shots_r4.yml`, sheets in `output/studio_cal/mm6_cd2/ingame_r4/diff`): edge agreement 0.89
(0.85 at round three's). Looked at: the south cavern's dome comes down to the rim as the original's, with the
battlement gallery's two openings and their lights over the door (rounds two and three: a blank wall); from the
gallery the cavern is seen through the window as in the original; the gate cavern's roof leans down to the rim on
the south and the ramp runs up along the castle wall open to the cave; the great hall's vault and the throne hall's
coves match the original's lines (throne hall 0.99); the low tunnel is the original's section; the west ward's ramp
is open to the ward. At each junction between caverns a rock wall stands across the bank and the roof's lean
(`08-junction-73-72`), where the original's cave runs on. The original's floor mist is missing everywhere, as before.

### What changed

- **The outer caverns (72, 73, 71, and 66 with 74)**: one room per sector, the outline being the rim and the castle
  walls; the floor level at -180 out to the foot of the rock bank and rising to the rim at 360 (204 round 66's east
  chamber) by `floor_points`, the foot as `floor_lines`, `steep_floor`; the roof flat at 1,170 inside the ring where
  its lean begins, leaning down to the rim by `ceiling_points` (66's east chamber its own vault, 828 ring to a ridge
  at 1,128; the roof's line over its south wall). The roof stands 16 above the floor along the rim (the original's
  meet; the build keeps a ceiling 16 over the floor). The original's own triangle edges between the points kept are
  the creases. 29 lean rooms, 30 bank rooms and 66's middle and east rooms are gone, with their ribs. The rock
  against the castle wall east of the gate (73, up to 450 under a roof down to 750) is floor and roof points too.
  The gate ramp and its landing are blocks (a wedge with `top_slope`, a block 780 high) open to the cave, as the
  original's; door record 9 is in the castle wall over the landing.
- **The south cavern (1)**: its floor level to the banks, the banks to the rim, the terrace at -90 in the north-west;
  its dome from the rim through the rings at 828 and 1,746 to the point at 2,160 on the castle wall, the castle wall's
  top as the roof's edge; the east rock wall upright to 510. The **battlement gallery's two openings** onto it are
  drawn (arches with a level top, `shoulders: [[0.34, 1]]` and `[[0.09, 1]]`, sill 588 to 1,170).
- **The great hall (56)**: one room under the original's fan vault (the flat crown at 1,920 along the south wall out to
  the apexes (12928, 6784) and (14848, 6784), the points at 1,428, the 828 ring along the north, 1,218 on the east
  wall), the west rock down to the floor at the west rim and the north-west rock rising to 204 under a roof that comes
  down to it. Round three's variant that stood 390 too high in a corner is not used: every height is the original's.
- **Ramps 36, 93, 109**: one room each (landing and ramp by `floor_points`, the vault by `ceiling_points`), the
  ramp_stack overlap no longer refused; their mouths are two openings one over the other (to the vault's springing,
  and the crown's band over it).
- **Throne hall (80)**: the coved ceiling (1,035 at the long walls, 1,215, 1,305); the galleries 81 and 82 slope from
  1,035 to 780 as the original's.
- **The low tunnel (158)**: a `path` room with the original's `section` (upright walls 126, a vault in four steps; its
  crown point 9 lower, flat at 315), mouths `shape: section` at both ends.
- **The west ward (144)**: one room; the north-west landing (-30) and the ramp down from it along the north wall are
  blocks open to the ward (rounds one to three: rooms walled to the ceiling).
- **Events 2, 3 and 19** use `cast` with the original's level (10, 8, 10) and mastery; the built Lua's 43
  `CastSpell` calls are the original's 43, call for call.
- **Door record 5** is two half leaves (`leaves: 2`): the north cavern's bank corner leaves 224 of wall north of the
  doorway, the great hall stands south of it, and a sideways leaf moves its whole width (the original's leaf folds
  toward one side: one edge moves 250).

**Rooms whose points are the original's own vertices one for one** (the rule asks that they be named): s001 (31
floor points, a few over the procedure's 25: the foot where it meets the east rock wall was left out, the terrace
kept), s066 with 74 (27 floor, 40 roof), s071 (15, 18), s072 (19, 18), s073 (28, 21), s056 (7 floor, 33 roof), s036,
s093, s109, s080 (the cove's 12). Points left out: T-vertices (points on another face's edge) and the slivers by the
rim. **Points moved** for the build's limits (floor at most 2 rise per run, roof at most 4): 71's bank foot (5686,
19479) by 90 to (5642, 19400); 1's foot (17185, -4293) by 45 to (17170, -4250); the great hall's north-west rock foot
(11851, 8970) by 111 to (11899, 8870) (the original's rises 2.3 to 3.6 per run there); the floor feet on 1's east rock
wall left out; 1's east wall upright to 510 where the original's roof faces stand nearly upright (normal z -0.2); the
great hall's crown point (16753, 5088) left out (its drop to 1,218 rises 4.9 per run); 66's corner (15697, 10368)
on the floor (the original's face there rises 4.4 per run). Under the gallery's two windows 1's floor was levelled
(11359 and 12241 at -55, from -26 and -84; 12625 and 14833 at -240, from -165 and -210): see tool defect 2.

### Targets of the task, one by one

1. The caverns: done as above.
2. Ramps 93 and 109 rejoined, vaults by `ceiling_points`: done (36 as well).
3. The great hall's fan vault: done from the original's points; 56 is 98.2 %.
4. Upright sides of narrowing ceiling levels: the south cavern and the great hall no longer use ceiling levels. The
   four coffers left (s012, s014, s033, s044) have upright sides of wall in the original too (d2wctra; s044's
   d2wlactr, now given as its `edge`).
5. Events with words: 2, 3, 19 as `cast`; the built calls equal the original's. Tunnels 142, 143 left.
6. The 15 cube panels and the podium stay movers with `travel: [0, 0, 1]`, notes kept.
7. `points.json` after the targets: the throne hall's coves, the galleries, the low tunnel, the west ward's ramp
   (done); what it still names is below.

### New features: what worked

`floor_points`, `floor_lines`, `steep_floor`, `ceiling_points`, `ceiling_lines` in large non-convex rooms (66 with 74:
17 corners, 27 floor and 40 roof points, 56 creases); `floor_points` with `slope`-free ramps and level landings in one
room; `ceiling_points` over a room with pillars, platforms and a beam (80, 56); `ceiling_slope` on galleries;
`platforms[].top_slope` as a ramp open to a cave and a ward; a `path` room with `section` and `shape: section`
mouths; two openings one over the other as one mouth (six mouths of the ramps); an arch with `shoulders: [[s, 1]]`
(level top) as a window; `cast` with level and mastery; `leaves: 2`; rooms stacking by their true surfaces (93, 109
over the corridor).

### New features: what was refused or fell short (repro projects in `output/studio_cal/mm6_cd2/repro/`)

1. **A mouth across a bank and the roof's lean** (`repro/bank_mouth`): `the uneven floor of room:a is not level along
   this opening: it runs from 0 to 360 between the opening's sides at [1024, 0] and [1024, 1024]. An opening stands on
   a level sill ...`. With a narrower opening over the level part, the opening also ends at the lowest roof over it,
   so the mouth is drawn only where floor and roof are both level and the rest of the cave's section is a wall across
   the cave (three junctions here, 1,150 to 1,350 wide; `ingame_r4/diff/08-junction-73-72.png`). Merging 74 into 66's
   room removed one; merging all five caverns would have taken about 90 floor points, against the procedure's 25.
2. **An arch into a vault said by `ceiling_points`** (`repro/vault_mouth`): `the gabled opening leaves the wall of
   room:a: 192 units from its side it reaches 315 but the room's ceiling is at 240 there (a sloped ceiling) ...: keep
   apex at 224 or less`. An opening ends at the vault's lowest point over it; the ramps' mouths are two openings one
   over the other, the gatehouse (75) and the inner court's alcove (78) keep their flat ceilings, since the gatehouse's
   arch onto the north cavern (1,026 high) would end at 723.
3. **A window over an uneven floor** (`repro/window_uneven_floor`): `the uneven floor of room:a is not level along this
   opening: it runs from 0 to 50 ...` though the window's sill is 700 above that floor (the gallery's windows over the
   south cavern: the floor under them was levelled, by up to 75).
4. **A section whose top is one point** (`repro/section_point_top`): `rooms[0].ceiling_slope: at point 0 of the path
   the ceiling (324) comes within 16 units of the section's sides, which stand to 315 there ...` (the room has no
   `ceiling_slope`). 158's crown is drawn flat at 315.
5. **Steeper than the build makes**: the original's banks rising more than 2 per run (71, 1, 56's north-west rock) and
   roof faces rising more than 4 (1's east wall, 56's east wall): points moved or left out (above).

### Gaps still open, most harmful first

1. **One surface for an uneven floor**: every bank of the five caverns and the south cavern is the level floor's
   crdrf2 where the original's is d2ceil3 (50,718 rays; textures 96.4 to 86.6 %). Wanted: a surface for the floor's
   triangles steeper than a given rise, or a surface per region bounded by `floor_lines`.
2. **Mouths through uneven sections**: the junctions 72|73 (x -13774), 73|66 (x 3121) and 66|71 stand as rock walls
   across the bank and the lean; the south cavern's mouth into its west arm (142) ends at 136 where the original's
   rises to 540. Wanted: `width: full, height: full` between two rooms whose floor and roof points agree along the
   shared wall, the mouth following them.
3. **Mouths of vaults said by points** (repro 2): the gatehouse's barrel vault (75) and the inner court's west alcove
   (78), and the arch passages inside 8 and 63 to 65 (a vault cannot step up to a flat ceiling inside one room either).
   Wanted: an opening that may rise to the ceiling over each of its points (an arch whose outline follows the vault).
4. Tunnels 142 and 143 (left, as the task says: no single section; they could be uneven floor and roof rooms, 16 and
   26 points for 142).
5. **Still without words** (not faked): the crystal as an event's source, the sarcophagi's question, texture changes on
   faces (the cubes' water to lava, the podium's desk), a sideways door that moves less than its width (record 8) or
   folds (record 5), a step inside a doorway (76, 147), the turning stair; the clicked blocks that do not move (15
   panels, the podium); a sunken level inside a sunken level (144's rings at -300 and -330); floor mist; fixed actors
   and floor items; wall texture offsets.

### Tool defects

1. **`validate` passes, `build` fails** with `rooms.yml: the indoor compiler refused the lowered map: indoor derived
   geometry requires a non-degenerate face: 3` (a face number, no room) when an opening's side falls exactly on a floor
   point of a diagonal wall: `oymap build output/studio_cal/mm6_cd2/repro/mouth_side_on_point --assets assets_dev --out
   <dir>`. The same happened with an arch's shoulder over a floor point of the wall (the gallery's east window,
   shoulder at 14641 over the floor point there; 0.09 instead of 0.087 builds).
2. **A window high over an uneven floor is refused** as if it stood on it (`repro/window_uneven_floor`, validate).
3. **Misleading messages**: `repro/vault_mouth` says the ceiling "is at 240 there" where it is 315 (the check takes the
   lowest point over the whole opening); `repro/section_point_top` names `ceiling_slope`, which the room does not have;
   for a T-vertex (a ceiling point on another face's edge), `two lines of ceiling_lines cross at [11752, 9059]: ... add
   that point to ceiling_points` while the point is already in `ceiling_points`.
4. Round three's defects 3 to 9 were not looked at again.

### Unsure of

- Whether the 16 between floor and roof along the caves' rim shows in the game (the original's floor and roof meet
  there): the pictures show no gap.
- Door record 5: the original moves only the leaf's south edge (250 north), so the leaf folds into the doorway's north
  side; the two half leaves are the nearest the vocabulary has without leaving the wall.

## After round four, by the lead (2026-11-12, about 23:50)

Two changes taken over from the code agent's trial on a copy of this project (`output/studio_obj/cd2/`), once the
words existed: the five caverns' floors have `floor_surfaces: [{steeper_than: 0.1, surface: d2ceil3}]`, so their
rock banks show the original's rock instead of the floor tile; and the three junctions between caverns are
`width: full` mouths that follow both rooms' floors and roofs, where they had stood as rock walls 1,150 to 1,350
wide. Still to undo in the next round: the south cavern's floor levelled by up to 75 under the two gallery windows
(a window over an uneven floor builds now), and the points moved by 45 to 111 for the slope limits.

## Round five (2026-11-13, night: contents, click sources, vaults by points, the round's warnings)

Briefed by `devdocs/map_studio/rounds/ROUND_FIVE.md`. The project files stay the source; the project as round four
and the lead left it is in `output/studio_cal/mm6_cd2/r5_backup/`. Edits over several entries were made by helpers in
`output/studio_cal/mm6_cd2/tools_r5/` that take every number from the original (`cd2.scene.yml`, the export in
`tools_r3/orig_r3.json`) or from the build's own warnings, each diff read: `contents_r5.py` (the lich and the 72
items), `panels_r5.py` (the 16 clicked blocks), `load58_r5.py` (event 58), `vault_r5.py` (a barrel vault as
`ceiling_points` from a sector's ceiling faces, used for 63, 64, 65, 75, s008_v and s078_v), `gate_r5.py`,
`hall8_r5.py`, `court78_r5.py`, `court78b_r5.py`, `pin_r5.py` (the 22 wall pairs), `steps88_r5.py`, `ramp163_r5.py`.
The south cavern's four floor points, the east window's shoulder, the 142 mouth, the chest and the playtest were
edited by hand. `trial.sh` builds and compares a copy (`trial_r5/`) before a change goes into the project; `tot.py`
and `pairs_r5.py`, `where_items.py` only read.

### Scores

| | start of round five | end |
|---|---|---|
| `oymap compare` score | 98.8 % | **99.1 %** |
| shape (distances agree) | 99.0 % | **99.3 %** |
| textures agree | 98.8 % | **99.0 %** |
| mean ceiling difference | 7.0 | 4.6 |
| points without a floor in the rebuild | 6 | 6 |

By sector (score): 8 95.8 to 99.8, 9 96.5 to 99.4, 10 97.1 to 99.4, 63 93.9 to 98.2, 64 94.9 to 99.0, 65 95.3 to
99.6, 75 94.9 to 99.8, 78 94.7 to 99.4, 88 86.6 to 95.3, 146 89.9 to 99.1, 148 92.0 to 100, 150 95.4 to 99.4, 145
95.8 to 98.1, 163 89.4 to 100, 176 98.1 to 99.8, 1 96.7 to 97.1, 142 79.7 to 80.6. Two fell a little: 79 92.6 to
92.0 and 97 96.6 to 96.0 (rays from the stairs into the court's new bays, whose ceiling at 384 is the original's).
Comparisons: `output/studio_cal/mm6_cd2/compare_r5_start`, `compare_r5_a` to `_c`, `compare_r5_end`. `compare.py`:
17 in, 13 near, 5 out.

Rooms: **261** (258): s008_v, s078_v, s078_n, s078_s new, s163_b joined into s163_a. Reached on foot with every door
out of the way: 248 of 261 (the 13 of round four's kind: arrow slit, barred room, teleport chamber, study, raised
ledges). `oymap solve`: **251 of 261 in three waves in the original's order** (`tools_r5/solve_r5.txt`); event 58 no
longer opens the forcefield in wave 1 (the `solve` defect of round three is fixed).

### Contents

- **Placed monsters: 1 of 1.** The original's one actor (`cd2.scene.yml` actor 0): a Power Lich (monster 570) of
  600 hit points named Lich King (place_mon.txt row 134; the build finds the name there), group 85, in the west court
  at (-14016, 14880), hostile by its kind. Not said: the Dragon Wand of Incineration (item 1761) he carries (no word
  for a placed monster's item). The placeholder `ph:lich_guardian` is gone.
- **Lying items: 72 of 72**, each at the original's place: 55 Potion Bottles in the north-west end room (s148), 8
  Rejuvenation potions in the south-east corridor (s124), 4 Armageddon books and 2 Decks of Fate in the secret
  treasure room (s191), one Deck of Fate each in the west cavern (s072), the cell block (s024) and the north-east
  cellar (s169). Seen in the game (`ingame_r5/diff/10-bottles-148.png`, `tour_r5/t2/01-treasure-low.png`). The
  placeholder `ph:floor_items` is gone; the 5 item spawn points stay spawn points.
- **Chests with the original's contents: 1 of 1** (record 0, the study's, the only one an event opens; the other 19
  records are empty): now trapped as the original's (flags 1; `trap_level: 5`, the map row's Trap column) with three
  random rolls of level 6. The original's third roll is of level 7: `random_levels: [6, 6, 7]`, which the indoor
  build reads and writes as the game's own record, is refused by the objects schema
  (`repro/chest_random_levels`: `objects.yml: chests[0].random_levels: unknown key`). No quest item is in a chest.
- **The summons** (events 26, 47 to 52) stay as the original's handlers have them: three monsters of slot 1 tier b
  under `not: {qbit: 1033}` (the podium sets it). The original has no handler on the lich's death, so no `kills`.

### Behaviour

- **The 15 cube panels and the podium are platforms with an `id`, clicked** (round three's movers with `travel:
  [0, 0, 1]` are gone, and the 15 "mover over several floors" warnings with them; 12 door records instead of 28).
  Same outlines and heights as the original's faces; the podium's desk top now slopes from 96 to 128 (`top_slope`),
  as the original's. The keyboard's use key picks them from the floor in the playtest.
- **Event 58, run when the map is entered** (`trigger: load`, condition west_way_cleared): opens the forcefield again,
  as the original's SetFacetBit does with MapVar1 at 2. A save and a reload after the forcefield is cleared are in
  the playtest. Its textures and the crystal's sprite are not said.
- **The forcefield.** The original's faces 4522 (LAVATYL) and 4575 are both invisible (attribute 0x2000), solid
  until event 33/35/36/37 sets their Untouchable bit (SetFacetBit 4522 and 4575). A platform may now be solid and
  unseen (`visible: false`), but nothing switches it: `opens`, `closes` and `toggles` take doors, lifts and movers
  only (`repro/unseen_barrier`: `wiring.yml: events[0].opens[0]: there is no door, lift or mover platform:forcefield
  in objects.yml`), no effect switches `solid`, and a platform's faces have no number a Lua `SetFacetBit` could name.
  So it stays a `slide_up` door with the lava texture (seen, where the original's is not), and the second face across
  the court's stair foot is still not drawn (an unseen platform there would never clear). Wanted: `visible: false` on
  a mover or door, or `{solid: false}`-switching effects on a platform with an `id`.
- **Secret doors:** none of the original's door faces carries the secret bit (0x2), so no `secret: true`.
- No lights, ladders or placed sounds in the original's events or scene.

### Events: each of the original's handlers and how the rebuild has it

54 of the original's numbers are bound to a face or sprite (59 and 64 to nothing; 65000/65001 are MMerge's).
**41 the same; 6 the same but without a face texture change or with a status line for a message box; 3 differ; 4
missing.** Changes since round three in bold.

| Original | What it does | Rebuild | |
|---|---|---|---|
| 1, 4 to 7, 9, 10, 60 | sideways doors, the chest, the way out | presets | same |
| 2, 3, 19, 21 to 25, 27, 46 | traps (`cast` with the original's levels) | plates and the portcullis | same |
| 26, 47 to 52 | summons until the Book is destroyed | plates, `summon` under `not: {qbit: 1033}` | same |
| 28 to 33, 35 to 43 | the cubes' panels | **platforms with an `id`, clicked** (round three: movers that never moved) | same |
| 43, 44 | the chamber's and the study's panels | switches, `teleport` | same |
| 34 | the podium: the Book destroyed, desk top to deskside | **a platform clicked, its top sloping as the original's**; the texture change not said | same but no texture |
| 45 | the crystal chamber's sign (cube to lava) | switch with `sets` | same but no texture |
| 54, 56 | the levers (cube to lava and back) | switches | same but no texture |
| 53, 55 | the signs: message box, the stone panel moves | switch, `text`, `toggles` | status line, not a message box |
| 8 | door record 8 slides 255 of 381 | a door 222 wide | differs (no sideways door that moves less than its width) |
| 20 | toxic cloud from two floor faces, one in a doorway | the second plate inside the cell (a doorway has no floor) | differs |
| 58 | on load: forcefield bits, cube textures, crystal sprite | **`trigger: load`, opens the forcefield door** | differs: the forcefield is a door; textures and sprite not said |
| 57 | the crystal (a sprite) gives Memory Crystal Delta | none | missing: `repro/decoration_source` (`wiring.yml: events[0].source: a script preset cannot have the decoration deco:crystal as its source`; the same for switch, text, teleport) |
| 61 to 63 | the sarcophagi ask "Steal from the dead?" and on Yes give an item and cost reputation | none (placeholders) | missing: `repro/question` builds `evt.AskQuestion(...)` but the built handler is `function()` without the continuation step the shipped `cd2.lua` reads, so the answer never arrives |

Texture changes: `texture: {cog, name}` and `evt.SetTexture` reach only faces with a cog, which only switches get
(ids.lock.yml `cogs`); the cubes' water faces and the desk top are platforms. A `condition: {lua}` was not needed: the
three outcomes of events 35 and 36 stay a condition with a Lua guard in `else_effects`.

### Shapes

- **Arches and vaults said by points** (task 6): the arch passages 63, 64, 65 under their barrel vaults (120 at the
  sides to 660, ten strips; mouths `width: full, height: full` follow them); the east tall hall's arch to the great
  hall (s008_v, a room of its own: a vault cannot step up to the hall's flat 912 inside one room), the great hall's
  mouth into it `height: full` (round four: an `arch` 330 + 840 under a flat ceiling); the gatehouse (75) under its
  vault (543 to 846, the side bays down to 396 in rock by `ceiling_surfaces` `at`), its mouth onto the north cavern
  up to the vault point by point (round four: a rectangle to 846); the inner court's west alcove (s078_v, 723 to
  1026, side bays to 576) with the throne hall's arch into it `height: full` (round four: `arch` 723 + 1026), and the
  court's two east bays before the stair doorways at the original's 384 (s078_n, s078_s; rounds one to four: 1050).
  **Rooms whose points are the original's vertices one for one:** s063, s064, s065, s008_v, s075, s078_v, s163_a
  (and round four's list).
- **The south cavern's mouth into tunnel 142** (task 6): `width: full, height: full` from rim to rim; its sill follows
  the cavern's banks and its top the lower roof, so it reaches 500 at 11377 where the original's reaches 540 (the
  arm's flat-across ceiling at that wall). Round four: 800 wide, ending at 136.
- **The long ramp of 163** joined with its foot as one room by `floor_points` and open along its west side to the
  tall corridor (the original's side wall stands under the ramp only): 163 89.4 to 100 %. Two rooms side by side
  cannot both open into one wall (16 units of wall between them), hence the join.
- **The stepped stand of 88** (treads at 450 to 540 up to the window into the court): its treads' diagonal arms are
  opened too (six openings; rounds one to four opened only the middle of each tread, the arms stood as walls).
- **Two openings on the wrong walls**, found through the new wall-pair warnings: 148 to 150 (the original's portal
  2971 at y 18528; the build had taken the pair 288 apart and put the doorway 600 west of it) and 145 to 146
  (portal 3176 at x -5326; the build had put it in the hall's north wall): both pinned to the original's walls, 148
  92 to 100 %, 146 90 to 99 %.

### Warnings answered

- **22 of the 23 "faces each other across N pairs of walls"** pinned with `from_wall`/`to_wall`; each pair checked
  against the original's portal between the two sectors (`pairs_r5.py`): 20 as the build had taken, 2 (above) on
  the other pair. The 23rd (56 to 8) went with s008_v.
- **The 11 (15 at this build) "mover over several floors"** went with the clicked platforms.
- **Left: 12 "opening in a wall without thickness and leaves wall round it"** (open:s001_s002, s066_s067,
  s084_a_s086, s085_s083_a, s094_s170, s142_s143, s157_s156_a, s170_s170_a, s170_s170_b, s187_s186, s191_s190,
  s193_s193_a): all are the original's zero-thickness sector borders, and the warning is false where it is tested:
  `repro/full_mouth_thin_warning` (a bay opening `width: full, height: full` off a hall) builds without it, and
  warns as soon as the hall's wall carries a per-wall `surface` (same geometry, same face count). Moving the rooms
  16 apart would depart from the original. And the three sarcophagus placeholders.

### Compromises of round four

- **Undone:** the south cavern's floor under the gallery's two windows is the original's again (11359 at -26,
  12241 at -84, 12625 at -165, 14833 at -210: on the original's line between its vertices; round four: -55, -55,
  -240, -240); with it the east window's shoulder is the original's 192 (0.087; round four 0.09, refused over the
  floor point at 14641 then, built now). The 142 mouth (above).
- **Kept, the limits unchanged** (each tried again in `trial_r5/` and refused): 71's bank foot (5686, 19479) moved 90
  to (5642, 19400): `rooms.yml: rooms[87].floor_points: the floor of room:s071 rises 2.86 for each unit of run
  between [8305, 18240] at 360, [3121, 21120] at 360, [5686, 19479] at -180 ... At most 2`; 1's foot (17185, -4293)
  moved 45 to (17170, -4250): `... room:s001 rises 3.35 ...`; the great hall's north-west rock foot (11851, 8970)
  moved 111 to (11899, 8870): `... room:s056 rises 3.63 ...`. Left out as round four: the floor feet on 1's east rock
  wall and that wall upright to 510 (the original's roof faces there stand nearly upright: 1's worst points, 77 to
  79 %), the great hall's crown point (16753, 5088) (a roof rise of 4.9), 66's corner (15697, 10368) on the floor.

### Playtest

`playtest.yml`, run four times at once from `output/studio_cal/mm6_cd2/run` (`tools_r5/play4.sh`, logs
`playtest_r5_end_1.log` to `_4.log`): **passes four of four, 184 steps** (169). New: the Deck of Fate in the cell block picked up
(`pick_up`, PICKUP line); the Lich King counted alive behind the shut forcefield, met in the west court and killed
(`clear_hostiles` over the court: he does not always keep his place once the party is in, and a first try with a
radius of 1,500 at his place missed him in one run), counted dead; a save and a reload after the forcefield is
cleared (it stays open); the chest looted after room is made in the packs (trapped now: `loot_chest` clicks again
when the trap leaves it shut; a roll may come out as gold, which the check allows); the cube panels and the podium
clicked as platforms. The ramp of 163, now open on its side, is walked up as before.

In-game pairs (`ingame_compare.py --root output/studio_cal/mm6_cd2/root`, 13 cameras of `shots_r5.yml`, sheets in
`ingame_r5/diff`; and `ingame_r5b`): edge agreement 0.88. Looked at: the arch passages (63, hall 8), the court's
alcove and the cube read as the original's, edge for edge; the bottles in 148 and the books and decks in 191 lie where
the original's do; the podium's top slopes as the original's (its paper sheet is the desktop texture's other part);
the study's wall shows the sarcophagus niche texture twice where the original shows it once with plain wall above
(wall texture offsets/bands, a known gap); from the south cavern the mouth into 142 is dark where the original's
glows with its mist.

### New features: what worked

Placed `monsters` (`hp`, `name` from place_mon.txt, `group`) and `items` by number; platforms with an `id` as click
sources (16, from the keyboard's use key); `top_slope` on a clicked platform; `trigger: load` with a condition (and
`solve` reading it); `width: full, height: full` mouths following uneven floors and roofs on both sides (142);
`height: full` under vaults by points (63 to 65, 75, s008_v, s078_v); `ceiling_surfaces` by `at`; `from_wall`/
`to_wall` on 22 openings; `floor_points` ramps opening along their side; `trap_level` on a chest. Round four's repros
`bank_mouth`, `vault_mouth`, `window_uneven_floor`, `mouth_side_on_point`, `section_point_top`, and round two's
`plate_under_platform` build now.

### Refused (repros in `output/studio_cal/mm6_cd2/repro/`)

1. `unseen_barrier`: an unseen platform switched by an event (above).
2. `decoration_source`: a decoration as an event's source (the crystal).
3. `question`: a question whose answer the handler reads (the sarcophagi): builds, cannot work.
4. `chest_random_levels`: `random_levels` refused by the schema though the build reads it.
5. `stair_open_side`: stairs (`slope` with `steps`) open along their side to the hall beside them, as the original's
   steps of 145 and 149 are: `rooms.yml: openings[0]: the opening is in a wall the floor rises along; put it in the
   wall at the low or the high end of the slope`. (A `slope` ramp likewise: 163 was turned into `floor_points`.)

### Gaps still open, most harmful first

1. **Tunnels 142 and 143** (80 and 83 %, the worst points after 88): bent tubes whose banks and leaning roof follow
   a curve; without a word (not faked).
2. **Texture changes on faces that are not switches**: the cubes' water turning to lava (the puzzle's only hint),
   the desk top. Wanted: a cog on a platform with an `id` (or `texture` naming a platform).
3. **The forcefield as an unseen barrier an event clears** (above): drawn as a lava door; its second face missing.
4. **Stairs open on their side** (145, 149: 98 and 97 %, the steps walled where the original's are open above the
   treads). Wanted: an opening along a stepped room's side whose sill is the higher floor.
5. Missing events: the crystal (57), the sarcophagi (61 to 63); the chest's level-7 roll; the lich's wand.
6. As before: a sideways door that moves less than its width (8), a step inside a doorway (76, 147, event 20), the
   turning stair, a sunken level inside a sunken level (144), floor mist, wall texture offsets and bands, the slope
   limits at 1's east rock wall.

### Tool defects

1. False "wall without thickness" warning for a full mouth when the wall has a per-wall `surface`:
   `oymap build output/studio_cal/mm6_cd2/repro/full_mouth_thin_warning --assets assets_dev --out <dir>` (drop the
   `walls:` entry and it goes). 12 of this project's warnings.
2. `chests[].random_levels` is read by `core/IndoorLowering.cpp` and written by `IndoorBuild.cpp` as the game's chest
   record, but `oymap validate output/studio_cal/mm6_cd2/repro/chest_random_levels --assets assets_dev` refuses it.
3. `oymap validate` accepts a mapping with a key given twice (a hand edit left `trap_level` and `notes` twice in a
   chest) and `oymap fmt` silently keeps the first.
4. The wall-pair warning is right to exist: two of its 23 openings had been on the wrong walls since round one.
5. Round three's defects 3 (a mover's `bottom` under a platform above it; `repro/mover_under_platform` still refused,
   now answered by `floor_height`) and 7 (headless pick of a moved cover) not looked at again.

### Unsure of

- Whether the original's Lich King keeps his place: in the rebuild he leaves it in some runs once the party is in
  the court (same monster, same table).
- The Deck of Fate (item 2067) at six places: the scene's own item numbers were taken as they are.

## Round six (2026-11-13): what the player sees at every interactive thing

Brief: the lead's task message of 2026-11-13 (after the user's walk through Gharik's Forge; REBUILD_PROCEDURE.md "What
the measure does not see"), and the lead's note of about 11:20 (the studio's fix of the Forge faults merged into
`openyamm-studio/build/oymap`: `kind: lever`, end-middle-end chests, the coplanar check, `oymap things`). The project as
round five left it is in `output/studio_cal/mm6_cd2/r6_backup/`. Every edit is a recorded one-off script in
`output/studio_cal/mm6_cd2/tools_r6/`, each run once and its diff read, every number the original's (export
`tools_r6/orig_r6.json`; door and event faces listed by `things.py` into `things_orig.txt`, and by `oymap things` into
`things_orig_oymap.txt`): `edit_things_r6.py` (doors, levers and their niches, covers, chest, forcefield, sarcophagi and
the study's walls, events), `edit_notches_r6.py`, `edit_door5_walls_r6.py`, `edit_crystal_r6.py`, `edit_alcove_r6.py`,
`edit_gallery_r6.py`, `edit_tower_r6.py`, `edit_chest_levels_r6.py` (with the Lich King's `carries`), `edit_playtest_r6.py`
(and two small hand edits of the playtest after it: the sarcophagus's item and the crystal come into the hand and are
stowed). Helpers: `look.py` (from the Hive's: same-camera pictures of both maps with console lines before a shot, floor
mist off in both), `floors.py`, `stack.py`, `things.py`, `coplanar.py`, `play4.sh`; quick checks `t_new.yml`.

### Scores

| | `oymap compare` | distances | textures | mean ceiling difference | rooms |
|---|---|---|---|---|---|
| start of round six (`compare_r6_start`) | 99.1 % | 99.3 % | 99.0 % | 4.6 | 261 |
| doors, levers, chest, forcefield, sarcophagi (`compare_r6_a`) | 99.1 % | 99.3 % | 99.0 % | | 266 |
| the gallery over the tall corridor, door 5's walls (`compare_r6_b`) | 99.2 % | 99.3 % | 99.0 % | | 266 |
| the gate tower's low bay; end (`compare_r6_c`, `compare_r6_end`) | **99.2 %** | **99.3 %** | **99.0 %** | 4.4 | **267** |

By sector, start to end: 193 (the study) 0.974 to 0.999 (textures 0.920 to 0.995), 164 (lever gallery) 0.920 to 0.976,
185 (gate tower) 0.951 to 0.999, 58 (north passage, door 5) 0.988 to 0.995, 144 (west ward) 0.991 to 0.994, 156 0.992 to
0.996, 150 0.994 to 0.997. Still worst by points lost: 1 (south cavern, 14.4), 56 (great hall, 7.5: the north-west rock's
foot, moved 111 for the slope limit, still refused at the original's place: `rises 3.63 ... At most 2`), 71, 143 and 142
(the tunnels, 5.7 and 4.8), 94, 149 and 145 (stairs open on their side, refused as in round five). `compare.py`: 19 in, 13
near, 3 out. Rooms reached on foot with every door out of the way: 254 of 267 (13 not: the arrow slit, the barred rooms,
the teleport chamber and the study, the raised ledges, as round five). `oymap solve`: **252 of 267** in five steps in the
original's order (`tools_r6/solve_r6.txt`): the keep; the doors, the east lever, the cube and the portcullis; the closet
block, door 9, the west sign; the west lever and the throne hall's cube, whose `passable` now clears the forcefield's
faces (`SetFacetBit(11, Untouchable)`, "face 4471 ... no longer blocks"); the crystal chamber's cube to the study.

No wrong shape that measures better: the new rooms are the original's sectors' parts (the niches' faces 4509 to 4513,
4544 to 4548, 4372 to 4397; the tower bay's 3971 to 3974 and 4054), the gallery's opening is the original's portal 3360
less two posts 16 wide the vocabulary needs (below), and the doorways of doors 6 and 7 grew by the 1 unit of their old
notches.

**Playtest** (`playtest.yml`, 211 steps, was 184): **passes four runs of four** on the final project (`output/studio_cal/mm6_cd2/playtest_r6_d_1.log` to `_4.log`; also four of four on the build before the chest's roll levels and the Lich King's wand, `playtest_r6_c_*`). The final build with `build/oymap` of 11:44 (the lead's correction of sideways leaves at the jamb) is byte for byte the one the runs played (`tools_r6/calib_darkmoor_1119bin.blv` against `build/calib_darkmoor.blv`): every door here folds, so the correction does not touch it; the stair door (door record 7 of the build, the original's door 5) is passed in every run. New: before the west lever the party walks into the forcefield from the ward's landing and stops at it (`movement_segment`, then its position), and after the cube and a save and reload it walks through into the court; the signs' message windows are closed and the covers waited for (the window holds the world); the crystal is taken once (a second click gives nothing); the west sarcophagus answered Yes gives an item and map variable 6; the Lich King is counted round the west court (`near`), not over the whole map. Two failures on the way, both the test's: the cover still `opening` when checked right after the window (`playtest_r6_a_*`), and the crystal's item in the hand, unseen by `item_count` (`playtest_r6_b_*`, tool defect 4). Packs emptied before the chest and `clear_hostiles` on every walk, as round five.

### What changed

1. **Doors fold as the original's.** Every door record of the original moves only the leaf's free edge (door 1: the
   vertices at x 8273 only; 4: y 4417; 5: y 9890; 6, 7: y 11201, 15729; 8: x 3214; 9: x -7431): every door is `fold:
   true` now, at the original's thickness (64 for doors 5 to 9; rounds one to five 32 everywhere), across the original's
   doorway (doors 1, 6, 7, 8 `width: full`; rounds one to five 226, 95, 95 and 222 wide, narrowed so that a sliding leaf
   had room in the wall). Door 8 moves 258 of its 384 and leaves 126 shut, as the original's 255 of 381; door 5 is one
   leaf again (rounds four and five: two halves). Door 1's leaf tiles D2skulBs at 64 (4 by 6 skulls; rounds one to five
   one skull stretched over it), the stone leaves of doors 6 to 9 tile their wall textures. Round five's leaves slid into
   the walls and, open, showed their picture on the wall beside the doorway (`ingame_r6/start/diff/05-door1-north-open`,
   `14-door5-east-open`); gone (`ingame_r6/end/diff/05`, `14`).
2. **The walls round door 5** are d2wctrA as the original's (faces 1107, 3295, 3296, 3919); rounds one to five gave them
   the door's picture (the generator read the leaf's face as the wall's), so three door pictures stood round the one
   doorway (`start/diff/10-door5-east-shut`).
3. **The notches of rooms s162, s187, s188** (1 unit, the generator's reading of the shut leaves of doors 4, 6, 7) are gone:
   with the leaves folding they put each leaf's free end in one plane with the notch's wall (the build's three "faces in
   one plane" warnings, one of them the lead's "door leaf" finding). `oymap audit`: no `geometry.coplanar` finding left.
4. **Levers in their niches, as the original's.** Each lever stands in a niche 32 square and 32 deep in the wall (T3LL5,
   faces 4509 to 4513 and 4544 to 4548; rooms `s016_niche`, `s164_niche`), a `kind: lever` with the BdkSH16c arm 26 long
   (`reach: 26`) on a BdkSV16c post, its arm sinking 16 and rising at the next pull (door records 14 and 12). The stone
   covers (doors 13 and 11) stand at the original's place, 3 thick on the wall's face (rounds one to five: 3 further out,
   in front of a t1swdd plate). Seen alike, shut, uncovered, pulled and pulled back (`end/diff/34` to `45`, `68`).
5. **The chest** is `kind: ch2`: ch2FRNTb with ch2frLE and ch2frRE ends on both long sides, ch2TOPb with ch2topLE and
   ch2topRE on the top, ch2side on the ends, 96 by 64 by 64 on the study's floor; its three rolls at the original's
   levels 6, 6, 7 (`random_levels`, which the schema accepts now). Rounds one to five: the plain plank chest on a block 64
   high (a `levels` entry under its footprint, the generator's reading of the chest's top as a floor), so it stood at 64
   to 128 (`start/diff/57-study-chest`).
6. **The forcefield is unseen, as the original's**: two invisible platforms (`visible: false`) where the original's two
   unseen faces stand (4522 across the ward's doorway at x -8206, -30 to 958; 4575 across the court's stair foot on the
   line between rooms s094 and s094_a, 30 to 630 over the court's floor), made `passable` by the throne hall's cube and
   on entering the map. Rounds one to five: a lava door that slid up (`start/diff/44-forcefield-east`: a wall of lava where
   the original shows an open doorway), and the second face missing.
7. **The sarcophagi** stand in niches 256 high (rooms `s193_n61` to `n63`, CTTRIM1 sides and roof) under a CTTRIM5 band
   with CTTRIM4 jambs and ctwl2RE corners (faces 4352 to 4396); rounds one to five ran the niches up to the ceiling, so
   each showed its picture twice (`start/diff/61` to `63`). Each niche's back is a wall panel with an id, clicked.
8. **The study's alcove** (the lava panel, event 44) has the original's frame: CTTRIM1 strips the whole height, CTTRIM3
   under its raised floor and over its lowered ceiling (faces 4343 to 4346; `end/diff/78-study-alcove`).
9. **The lever gallery** (s164) opens over the tall corridor across its south side as the original's portal 3360 (rounds
   one to five: only the ramp's 96 open, the corridor's 288 a wall).
10. **The gate tower's north bay** (s185 from y 11200, ceiling 856, faces 3971 to 3974 and 4054) is a room of its own,
    door 6 opening from it; rounds one to five had the whole tower at 1170.
11. **Events** (below): the cubes turn to lava and back, the signs show message windows, the crystal, the sarcophagi, the
    load handler's parts, the Lich King's wand.

### Events, the original's against the rebuild's

`oymap flow` of both (`tools_r6/flow_orig_r6.txt`, `flow_r6.txt`). Of the 54 numbers bound to a face or a sprite (59 and
64 to nothing in either; 65000 and 65001 are MMerge's): **50 the same, 4 differ, 0 missing** (round five: 41 the same, 6
the same but without a texture change or with a status line, 3 differ, 4 missing).

- Same since this round: 45 (the sign's message window; the crystal chamber's cube to lava, or silently to water again),
  53 and 55 (message windows; the covers move once the window is closed, as the original's continuation), 54 and 56 (the
  levers' arms sink and rise; the cubes' five faces to lava and back by `set_texture` on their platforms), 57 (the crystal,
  a decoration as the source: the Memory Crystal Delta, quest bit 1217, the sprite to crysdisc), 61 to 63 (the question,
  on Yes the original's `evt.GiveItem(6, n)` and `SubtractValue(655595, 10)`, silent once robbed), 8 (door 8 opens 255 of
  381), and the forcefield's part of 33, 35 to 37 (`passable` on its two faces).
- Differ: 20 (the doorway's plate, as before); 34 (the Book destroyed; the desk top's face turning to deskside is not
  said: `set_texture` changes every face of the podium's platform, and the top is no platform of its own); 56 (the
  original's slips not copied: its off branch moves the east lever's arm, door 14, and turns 4269 back twice and 4268
  never); 58 (on load: the cubes, the forcefield and the crystal's sprite as the original's, in four `trigger: load`
  events with their own conditions, the forcefield on the original's own test, the west lever pulled; not the desk top;
  and the original's click on the forcefield's face 4522, which runs 58 again, is not bound).
- The west lever's title is "Sign" as the original's (event 56's title; a slip, kept).

### What the player sees: differences per interactive thing

Pictures of both maps from the same camera before and after use, floor mist off in both (the studio has no mist; the
original's is OpenYAMM's `cd2_mist.scene.yml`): `output/studio_cal/mm6_cd2/ingame_r6/start/` (round five's build, 64
pairs, mean edge agreement 0.783), `a/` (the first fixes, 68 pairs, 0.820), `end/` (this round's, 78 pairs, 0.815; on the
64 pairs `start` has, 0.783 to 0.838); cameras and console lines in `tools_r6/things_spec.yml`, `things_spec2.yml`,
`things_spec3.yml`. Each sheet: original, rebuild, difference.

| Thing | Original | Rebuild now | State |
|---|---|---|---|
| Door 1 (event 1) | D2skulBs tiled, 256 by 384, folds west; its free edge BemSV32c, red-brown, a strip at the jamb when open | the same (`end/diff/01` to `05`: 0.96, 0.94, 0.94, 0.94, 0.94; start 0.81 to 0.91) | fixed; the edge's texture: gap a |
| Door 4 (event 4) | D2LgDor, folds north; edge BemV32c | the same (`06` to `09`: 1.0, 0.79, 0.87, 0.99) | fixed (fold); edge: gap a |
| Door 5 (event 5) | D2LgDor 64 thick, folds north; edge BemVdk; d2wctrA walls round it | the same (`10` to `14`: 0.90, 0.86, 0.85, 0.84, 0.90) | fixed (fold, walls); edge: gap a |
| Doors 6, 7 (events 6, 7) | wall-stone blocks 64 thick, fold north | the same (`15` to `22`: 0.68 to 1.0, the lowest from door 7's west side where a monster stood in round five's pictures; start 0.37 to 0.99) | fixed |
| Door 8 (event 8) | a stone block 381 wide, 255 open, 126 stays | the same (`23` to `26`: 0.77 to 0.82) | fixed |
| Door 9 (event 9) | D2WlActr panel 64 thick, folds east | the same (`27` to `30`: 0.74 to 0.87) | fixed |
| Portcullis (door 10, event 2 on its faces) | a block in the arch, sinks 180 | the same; the arch's ends square where the original's curve (`31` to `33`) | as round five |
| East and west levers (events 54, 56; doors 14, 12) | a BdkSH16c arm in a T3LL5 niche behind a stone cover | the same, the cover lowered by the sign, the arm sinking and rising (`34` to `45`, `68`: 0.54 to 0.64, the lowest of the round because the original's walls there draw red, below) | fixed with the studio's `kind: lever` |
| Signs (53, 55, 45) | message windows | message windows | fixed |
| The three cubes (28 to 33, 35 to 42) | water panels turning to lava with their lever or sign | the same (`37`, `39`, `43`, `52`, `55`: 0.70 to 0.95) | fixed |
| Forcefield (faces 4522, 4575) | unseen, solid until cleared | unseen, solid until cleared (`46` to `49`: 0.81 to 0.83; start 0.75 with a lava wall) | fixed |
| Crystal (event 57) | mcryst01 on its stand; taken, the stand is empty (crysdisc) | the same (`53`, `54`) | fixed (Lua with the decoration's number: gap c) |
| Teleport chamber's panels (43), study's panel (44) | orWtrTyl, LAVATYL panels | the same; the alcove's frame now CTTRIM1 and CTTRIM3 (`56` to `58`, `78`: 0.79 to 0.92) | fixed (frame) |
| Chest (event 10) | ch2, end-middle-end, on the floor | the same (`59` to `61`: 1.0) | fixed with the studio's `kind: ch2` (round five: plank chest on a block) |
| Podium (event 34) | DESKTOP showing its paper sheet (texture offset u 32), deskside once used | the desktop's other half (a key and coins), no change on use (`62`, `63`: 0.99) | gaps b and b2 |
| Sarcophagi (61 to 63) | niches 256 high under a band, the question | the same (`64` to `66`: 1.0; start 0.85 to 0.92) | fixed |
| Exit (60) | D2LgDor face | the same (`67`) | as round five |

The studio's five being fixed now, where this map has them:
- **Lever handles that move**: both levers (doors 12 and 14 of the original): built with `kind: lever` this round and
  looked at (above). The studio's post stands 8 out of the niche's back where the original's BdkSV16c strip lies flat on
  it; from where a player stands it reads the same (`end/diff/68-lever-east-close.png`).
- **A toggling switch's picture**: the two ember signs toggle their covers; their picture is the same on and off (sign7),
  and the build now keeps their state in `toggle.sign_embers_e` and `_w` (map variables 0 and 5). The levers' old Lua that
  set a plate's picture back is gone.
- **Chest faces laid end-middle-end**: the study's chest, built with `kind: ch2` this round (above).
- **Things over moving parts**: none in this map (nothing stands on the portcullis, the covers or the levers' arms).
- **Faces in one plane over each other**: in the rebuild, door 4's leaf (the lead's finding) and doors 6 and 7's leaves
  against their rooms' 1-unit notches, gone with the notches (3 above); `oymap audit` finds none now. The original has
  three of its own (`tools_r6/audit_orig_r6.json`): the great hall's east wall faces 787 with 1053 and 1054 (d2wctrA,
  x 16753, overlaps 124416 and 456192), and door 9's 4059 (d2wctrA) with 4076 (D2flor4) at its far end.

Seen in the original only, not the project's: in OpenYAMM the original's walls round each lever niche draw red-tinted
(faces of door records 11 and 13: 314, 4520, 4539, 4555 and the signs) while that lever is pulled, and once at the start
(`a/diff/36-lever-east-pulled.png`, `45-lever-west-again.png`); the rebuild's do not. A question for the game, not the
rebuild.

### Gaps (studio), most visible first, with the original's faces

a. **A leaf's free edge surface.** The original's open doors show their leaf's edge at the jamb in a trim texture:
   door 1 BemSV32c (face 3855, x 8273, y 5920 to 5952, z -288 to 96), door 4 BemV32c (3876, y 4417, x 7985 to 8017,
   z -636 to -396), door 5 BemVdk (3909, y 9890, x 12641 to 12705, z -180 to 75); the rebuild's edges take the leaf's
   picture or the wall's. Field: `doors[].edge_surface` (the Hive's gap f too).
b. **A texture change on one face of a platform**: the podium's top (face 4560 DESKTOP to deskside by event 34 and 58);
   `set_texture` names a platform and changes all its faces. Field: `set_texture: {of, to, face: top}`, or a top that is a
   platform of its own without sides. b2: **the texture offset of a platform's top**: the original lays DESKTOP from u 32
   (the paper sheet; `texture_delta_u` 32, `_v` -2912), the rebuild from the world's grid (the other half: a key).
c. **A decoration's picture**: the crystal's SetSprite (original 329 to crysdisc) is Lua naming the decoration by its
   entity number in the build (325), which moves when decorations before it change; ids.lock.yml keeps no decoration
   numbers. Field: `set_sprite: {of: deco:d329, to: crysdisc}` indoors (the outdoor sketch has it), the number kept in
   ids.lock.yml.
d. **Two openings in one wall need 16 units between them**: the lever gallery's south side (original portal 3360, one
   opening over x -4366 to -3982) is the ramp's mouth (96) and the corridor's (256 of 288), with two posts 16 wide the
   original has not (`end/diff/73-gallery-164-south.png`, the near post). Field: one opening into two rooms (`to: [a, b]`).
e. A click on an unseen face (the forcefield's 4522 runs event 58): an unseen platform could be a source; not bound, as
   it changes nothing the load handler has not.
f. Floor mist: the original's look in OpenYAMM includes `cd2_mist.scene.yml` (a mist layer over the sunken floors at
   -150); the studio has no mist word.
g. As before: tunnels 142 and 143 (bent tubes with leaning roofs), stairs open on their side (145, 149;
   `repro/stair_open_side` still refused), the step in a doorway (event 20), the slope limit at the great hall's
   north-west rock and the south cavern's east wall, the arch's curved ends at the portcullis.

Refused this round: nothing new. Round five's repros `chest_random_levels`, `question` and `decoration_source` validate
now (all three used); `unseen_barrier` is still refused as written (`opens` on a platform), the `passable` effect says it.

### Tool defects

1. `oymap things devdocs/map_studio/briefs/mm6_cd2/L4 --assets assets_dev`: the crystal is "decoration in sector 0" (it
   stands in room:s170_b).
2. A decoration's entity number (what `evt.SetSprite` takes indoors) is not in ids.lock.yml (gap c).
3. `ids.lock.yml` keeps `door:d05.leaf2: 29` after door 5 lost its second leaf ("ids.lock.yml forgets removed ids").
4. The scenario runner: an item given by an event (`evt.GiveItem`, the crystal's AddValue) comes into the hand, where
   `item_count` does not see it and the game's own HasItem does not either: a second click on the crystal gave a second
   one until the playtest stowed the first (the original's handler behaves the same: its `HasItem(2172)` test is the
   game's).
5. From round five, still: the false "wall without thickness" warning (now 1, open:s094_s170); `ids.lock.yml` written
   by `oymap build --out` and `oymap export <project>` into the project.

### Unsure of

- What the red tint on the original's lever walls is (above).
- Event 61 to 63's `SubtractValue(655595, 10)`: the exporter does not name variable 655595; taken over as the original's
  call.
