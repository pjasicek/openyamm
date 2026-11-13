# The Hive (MM6, `hive.blv`) rebuilt as a Map Studio project: where it stands

Rebuild agent run of 2026-11-12, by `devdocs/map_studio/REBUILD_PROCEDURE.md`. Project: this folder (`project.yml`,
`rooms.yml`, `objects.yml`, `wiring.yml`, `ids.lock.yml`, `playtest.yml`). Scratch data, pictures and the scripts that
write the project: `output/studio_cal/mm6_hive/`.

**Since round two (below) the project files are the source and are edited by hand; the generator paragraph that
follows describes round one only, and its scripts (kept in `gen/`) must not be run over the project again.**
**Where it stands now is the last section, "Round six": 97.7 % (distances 98.1, textures 97.6), 100 rooms, every
tunnel with the original's six-sided section and heights at its path points, junctions as side doorways.**

The project files were written by `output/studio_cal/mm6_hive/tools/gen.py` (with `lib.py`) from a measured
description: tunnel centre lines as a few stations `[x, y, z]` each, chamber outlines of 4 to 26 points, doors,
switches, chests, spawns and lights at the original's places. `tools/regen.py` runs it, `oymap fmt` and
`oymap validate`; `tools/round.sh` adds `oymap compare`; `tools/mkplay.py` writes `playtest.yml`; `tools/play.sh`
builds, installs into the scratch mount and plays a scenario. Change the description, not the YAML.

## Scores

| Round | What changed | `oymap compare` score | distances | textures | floor points missing |
|---|---|---|---|---|---|
| 1 | shell only: 282 rooms, no doors or objects | 83.1 % | 87.9 % | 78.4 % | 31 |
| 2 | pits reshaped, cells given door stubs, long ramps cut, wall textures taken from upright faces, bands | 86.3 % | 89.3 % | 87.3 % | 35 |
| 3 | doors, switches, chests, spawns, lights, wiring | 87.6 % | 90.6 % | 88.5 % | 35 |
| 4 | reactor's outer ring in three rooms, pits with one slanting open side, chest alcoves with their pier, vault band, water pads | 88.6 % | 90.6 % | 91.2 % | 31 |
| 5 (last) | ledge ceiling, antechamber textures, two sliver rooms removed | **88.8 %** | **90.7 %** | **91.4 %** | 31 |

- `compare.py` (structure, scale, play): first 13 in, 6 near, 16 out; last **16 in, 4 near, 15 out**. Every "out" but
  two is a count or a size per sector: the rebuild has 345 rooms where the original has 79 sectors, because a tunnel
  that climbs along a curve has to be cut into flat bends and straight ramps (gap 3). Floor area 106.3 against 98.1
  million, walkable 94.1 against 88.2, floor level spread 2304 against 2330, doorway median 224 against 256.
- Rooms reached: 1 of 345 at the start (the original: 1 of 79), **345 of 345** with every door out of the way.
  `oymap solve` opens it in the original's order: entry door; double door (250 rooms: the great chamber, its four
  pits and the four tunnel loops; the original 52 of 79); the click doors; the switches; the key door (item 2190);
  the reactor; the gates and the Queen's chamber with quest bit 1204.
- Playtest (`playtest.yml`, 218 steps): **passes**. It walks from the entry to the Queen's chamber through all four
  loops, drops into the four pits, uses all 21 doors (the one-sided and locked ones from both sides), the 6 switches
  and the 5 chests. 200 seconds of walking, no jumps, no replans, no stuck spots.
- In-game pictures (`output/studio_cal/mm6_hive/ingame/diff/`, 18 pairs from `shots.yml`): mean edge agreement 0.71,
  blurred difference 0.048. Most alike: the great chamber and the reactor (0.87 to 0.89). Least alike: the ring's
  north side (0.48), the guard room (0.55), the cave (0.56), the tunnels (0.58 to 0.62).

## The five worst remaining differences

1. **The reactor's ring wall and gates** (sector 79; the six worst points, 0.33 to 0.43, stand in the gate strip at
   y 25344; 13 floor points missing under the ring). The ring is a moving wall (door 53) inside one sector; the
   rebuild has it as the fixed gap between a hexagonal room and three outer rooms, and one gate where the original
   has three. Gaps 2 and 7. Part of the low score is the tool's (defect 1).
2. **The great chamber's dome and ledge** (sector 4: 0.88, mean ceiling difference 344; sector 2: 0.42). The dome
   rises in four rings from z 0 to 2134; the rebuild has one step (1100, and 1900 inside radius 900), because raised
   ceilings do not nest (gap 6). Ten of sector 2's twenty points stand exactly on the ledge's edge (defect 2).
3. **The four pits and the hatch** (sectors 5 to 8: 0.31 to 0.59). Holes in the chamber floor in the original; side
   rooms open along one edge in the rebuild, with one wrong wall each beside pits 6 and 8, corner triangles for pits
   5 and 7, and ceilings as high as the chamber's. The shaft under the hatch is not joined to the chamber at all.
   Gaps 1 and 2.
4. **The north halls** (sector 35: 0.86, textures 0.79; 37 and 38: 0.86 to 0.89). A barrel vault drawn as one raised
   band; lower walls that lean in the original and stand upright here; the dividing wall's two textures (gaps 5, 6,
   11).
5. **The tunnels** (sectors 10, 20, 24, 70: 0.80 to 0.83, distances 0.73 to 0.78). Hexagonal in section in the
   original (floor 140 wide, 302 at mid height, 260 high); rectangles 224 by 256 here, with a flat bend at every
   station, straight ramps between and a ceiling that steps (gaps 3, 4, 5).

Smaller: the reactor antechamber (sector 80, 0.76: a beam overhead and a second wall texture), the chest alcoves
(sector 12: a floor that climbs two ways).

## Gaps in the vocabulary, most harmful first

1. **An opening in a floor onto a room below.** The hatch (door 43, 480 by 400 at 536, 8960) from the great
   chamber's floor at -768 into the shaft with its floor at -2304, which is the way to the reactor; and pits 5 to 8
   (about 450 by 600 each, 40 units inside the chamber's walls, -768 down to -1536, a tunnel leaving at the bottom).
   Did instead: the shaft is a room stacked under the chamber, reached only from the deep tunnel, and the switch
   that opens the hatch (event 36) carries the party to its foot with `evt.MoveToMap`; the pits are rooms in notches
   of the chamber's outline. A sunken `level` cannot serve: its bottom cannot open into another room. Field:
   `rooms[].floor_openings: [{outline, to: room}]`.
2. **One opening per pair of rooms, and no way to name its walls.** Two openings between the same two rooms are
   refused, and when two rooms face each other on several pairs of walls the build picks one. Pits 6 and 8 keep a
   wrong wall on one side; the ring wall has one gate instead of three; cells 52, 54, 57 and 59 were opened along
   their 768-long side walls (128 behind the passage) instead of their 256-wide doorways, until each got a stub room
   of its own. Field: `openings[].from_wall` and `to_wall` (edge numbers), and several openings per pair.
3. **A tunnel that climbs along a curve.** A `path` room takes no `slope` (a sloped room must be convex), and two
   rooms join only on exactly parallel walls. The 24 tunnel sectors became 250 rooms: a flat bend (three-point path,
   `smooth: 2`) at every station and straight ramps between. Field: path points with heights, `path: [[x, y, z],
   ...]`, the floor following the centre line.
4. **A ceiling that follows a sloping floor.** A ramp's `ceiling` is one height, so a tunnel 256 high that drops
   250 is 506 high at its foot. Did instead: every ramp is cut into pieces of at most 80 units of drop (89 extra
   rooms and 175 build warnings, defect 6). Field: `slope.ceiling_to`, or `height` for constant headroom.
5. **A cross-section other than a rectangle.** The tunnels' hexagon (floor 140, 302 at mid height 130, ceiling 140
   at 260), and the lower walls of the halls and cells (sectors 35 to 38, 45, 46, 48, 50: leaning out about 80 over
   their first 256). Field: `section: {floor_width, mid_width, mid_height}` on a path, `batter` on a room's walls.
6. **Domes and vaults.** A second `ceiling_levels` region inside the first is refused ("the region cannot be cut
   out"), and no ceiling slopes. The great chamber's dome and the north hall's barrel vault (crown -436, springing
   -1024) are one step each. Field: nesting, or `vault: {kind: dome | barrel, apex, spring}`.
7. **Blocks that move but are not a leaf in a doorway.** The ring wall (door 53, sinks 1279), the gate blocks that
   rise from the floor and sink from above (51, 52), the floor panel over the lower passage of the guard room (38),
   the double door whose leaves part sideways (45, 46), the six buttons that move when pressed. Did instead: fixed
   wall, one `slide_down` gate, a placeholder, one `slide_up` leaf, plain switches. Field: `movers: [{outline,
   bottom, top, direction, travel}]`, and `kind: slide_left | slide_right | split` for doors.
8. **Events without an object the player uses.** 182 floor faces run a handler when walked on (the flush system:
   events 17, 19, 22, 27, 29, 54, 56, 57, 58, with the water pads that protect from it); event 100 runs on entering
   the map; event 23 belongs to a decoration (the keg). None is wired. Field: `source: {room, outline}` as a
   walked-on region, `on: load`, and decorations as sources.
9. **A door that opens from one side only** (doors 4, 5, 10, 11, 12, 36; "The Door Won't Budge" from the other).
   Did instead: doors 4 and 11 wait for a map variable set by the door on the only other way round (42 and 9), which
   keeps the order of opening; the others open from both sides. Field: `side: from | to` on a door event.
10. **Wall bands for one wall** (the hall's dividing wall is hvwl1a to 256 and hvwl6 above; the other walls hvwl5a
    and the vault's texture), and **a door leaf with a surface per side** (door 8 shows wall texture to the guard
    room). Field: `walls[].bands`, `doors[].back_surface`.
11. **Uneven floors.** The chest alcoves (sector 12: -1867 at the east mouth to -1772 at the west mouth and in the
    alcoves), the funnel sides of pit 5, the lumps of the north-west cave. Drawn flat. Field: floor height points.
12. **Fixed actors and items on the floor** (the reactor, the Queen, item 1817 in the flush lock): placeholders.
    A spawn cannot say a rank (spawn index 8: slot 2, rank B).
13. **`teleport` preset with a switch** is refused in a new project; the two teleport switches use `lua`.

`rough` was enough for the two caves; the tunnels' walls are smooth in the original. `rough` needs a level floor, so
a rough ramp could not be said, but this map does not need one.

## Tool defects

1. `oymap compare hive.blv --world mm6 --with <L4> --assets assets_dev`: its six worst points (y 25344, sector 79)
   stand inside the shut gate blocks (doors 51 and 52 start moved, state 2), where it reports "the original has
   nothing within 4096 to the south". `oymap probe hive.blv --world mm6 --assets assets_dev --from 4416,24800,-2256
   --to 4416,25800,-2256` shows the gate blocks the walk. Points on door faces should be left out.
2. Same command: points exactly on the edge of a drop (the ledge at y 7168, ten points of sector 2) count as
   "without a floor in the rebuild" although both maps have the same edge.
3. `oymap validate` on two straight rooms meeting 0.5 degrees off parallel says "rooms overlap: two rooms cannot
   share space"; it should say the walls are not parallel and by how much. There is no tolerance, so every joint
   needs points on one whole-number line (the generator takes steps of the segment's smallest whole-number vector).
4. `oymap validate` on two openings between the same two rooms that share three edges says "two openings in one
   wall overlap or stand closer than 16 units"; they were meant for different walls (gap 2).
5. `oymap validate`: "a teleport preset cannot have the switch as its source", while `oymap schema wiring` says a
   source is "a door, switch, chest or exit" and names no source a teleport may have.
6. `oymap build` warns "opening is in a wall without thickness and leaves wall round it ... move the rooms at least
   16 apart" 175 times, once for every joint of two pieces of one tunnel whose ceilings differ; the advice cannot
   be followed there.
7. `oymap audit --reach` counted a room 32 units long as "not reached" while every room beyond it was reached (it
   now says "niches too small to stand in" in `solve`, but `audit` lists them as unreached sectors).
8. `oymap install` reads only `<project>/build`; a build made with `--out` elsewhere cannot be installed, so the
   build folder has to be written into the brief.
9. `calibration/ingame_compare.py` uses fixed `--isolated` names (`studiocompareoriginal`, `studiocomparerebuilt`)
   for every caller, and stopped with `PermissionError` on `oymap` while the binary was being rebuilt.
10. `oymap audit --json` gives the count of unreached sectors but not their numbers; `solve --json` has them.

## Unsure in the original

- The keg room (sector 73) is "never reached" in the original's own solve: its floor is 60 above the tunnel's at its
  mouth. The rebuild has it 40 above, so it is reached.
- The doorway in the north hall's dividing wall: read as 256 high and 147 wide; the rebuild's is 250 by 128.
- Door states: read as 0 at the file's position and "close" as moved, which makes doors 51 and 52 shut at the start.
- Events 30 and 62 have faces but no handler. Sector 78 is one face. Chest contents were read only as two random
  items of level 6 each.
- The alcove with the switch panel (event 30) and the shelf along the reactor's north wall are simplified.

## Round two (2026-11-12, later the same day): the new vocabulary

The project files were edited directly. Helpers that read and measure, and the three one-off edits that touched
many rooms (each checked by its diff), are in `output/studio_cal/mm6_hive/tools_r2/` (`sec.py` lists an original
sector's faces, `poly.py` insets and checks outlines, `rank.py` ranks the comparison's sectors, `round.sh` runs fmt,
validate, build, compare, reach and solve, `play.sh` installs the build and plays a scenario; `edit_halls.py`,
`edit_ramps.py` and `edit_playtest.py` are records of edits already made). The round-one files are in
`output/studio_cal/mm6_hive/r2_backup/`.

### Scores

| | `oymap compare` | distances | textures | floor points missing | mean ceiling difference | rooms |
|---|---|---|---|---|---|---|
| start of round two | 89.1 % | 90.9 % | 91.8 % | 29 | 87.8 | 345 |
| pits and hatch as floor holes | 90.5 % | 92.5 % | 92.0 % | 25 | | 345 |
| great chamber: ledge as a platform, dome of four rings | 90.9 % | 93.0 % | 92.0 % | 25 | 36.9 | 344 |
| north halls: three ring domes | 91.6 % | 93.8 % | 92.4 % | 25 | 22.7 | 346 |
| ramps rejoined, ceilings parallel to their floors | 91.9 % | 94.2 % | 92.6 % | 25 | | 288 |
| reactor: north strip and bay, gate at its true width | 92.3 % | 94.7 % | 92.8 % | 25 | | 290 |
| hall mouths full width (two openings one above the other) | **92.7 %** | **95.2 %** | **93.0 %** | 25 | 20.3 | 290 |

- `compare.py`: 15 in, 6 near, 14 out (before: 16, 4, 15). Still out: counts and sizes per sector (290 rooms
  against 79 sectors).
- Rooms reached: 290 of 290 with the doors out of the way, 1 with the doors as they start (the original: 1 of 79).
  `oymap solve`: entry; the lock (the load event's doors need quest bit 1204, as in the original's solve); the
  double door (239 rooms, with the shaft and the deep tunnel, as the original's wave 2 has sectors 9 and 70); the
  click doors; the key door (item 2190); the rest. The original's waves are 1, 1, 52, 14, 10 sectors.
- Playtest (`playtest.yml`, 241 steps): **passes**, 219 seconds of walking, no replans, no jumps. New in it: the
  four pits as drops through holes in the chamber's floor, the walk back through the east tunnel and the drop of
  1536 through the hatch, the lock's two plates, the flush timers (warning, flush, complete), a water pad and the
  floor beside it, the switch that disarms, the load event opening both gates once quest bit 1204 is set.
- In-game pairs (`output/studio_cal/mm6_hive/ingame_r2/diff/`, 12 pairs from `shots_r2.yml` at the places changed):
  mean edge agreement 0.82, blurred difference 0.034. Great chamber 0.84 to 0.91, north halls 0.78 to 0.88, the
  stepped corridor 0.74, a tunnel ramp 0.62, the reactor's north strip 0.64.

### What changed

- **Pits 5 to 8** are rooms under the great chamber (floor -1536, walls to -1280, a whole-ceiling level whose
  sides lean in to the hole's shape at -768, as the original's undercut sides do), each joined to the chamber by an
  opening `in: floor` with an `outline`. The chamber's outline lost its four notches.
- **The hatch** is `open:s4_hall__s9_shaft`, `in: floor` with no outline (the shaft's whole top); the shaft has the
  original's seven-sided plan. The switch's teleport is gone. The trim strip east of the hole is a platform.
- **Great chamber**: one room with the ledge as a platform 768 high against the south wall (`platform:ledge`), so
  that one dome covers both: four nested `ceiling_levels` with `top_outline` at the original's ring heights (816,
  1509, 1972, apex 2134). The walls end at 256 (the gallery's doorway), not at 0, so the first ring leans from 256.
- **North halls**: each half of the great hall, the east hall and the west hall has its dome as whole-ceiling
  levels standing on the walls, rings at the original's heights (they were read as a barrel vault in round one;
  they are three domes, the middle one cut in two by the dividing wall). The ends toward the neighbouring hall
  stand upright, and the mouths rise into them. Two corners with doors became rooms of their own
  (`room:s37_recess`, `room:s38_recess`).
- **Ramps**: 31 ramps that had been cut every 80 units of drop are single rooms again (89 pieces, 58 openings
  between pieces removed), and all 82 ramps have `ceiling_slope` parallel to the floor, 256 above it.
- **Reactor**: the low strip under a sloping ceiling along the north wall and the bay with the switch panel are
  rooms; the gate between the ring wall's north side and the strip is 2272 wide and 1264 high (it was 2240 by 1100).
- **Events**: the lock's two walked-on faces as plates (events 17, 19), the three flush timers (57, 54, 51; 54 as
  two events), the water pads and the floors round them (56, 58; 9 of 30 pads), the Queen's floor (29), the load
  event (100: opens the two gates once the reactor is destroyed, shuts door 28), the flush switch as a `teleport`
  preset. The gates' click events are gone. The room under the south-west pit has its walls' texture and its pad.

### New features: which worked

Worked at the first try: a floor hole by `outline` into the flat top of a lower room's ceiling level; a floor hole
that is a lower room's whole ceiling (seven-sided); four `ceiling_levels` one on another with `top_outline`;
whole-ceiling levels with repeated top points (triangular sides) and upright ends; an opening that rises into an
upright end; `ceiling_slope` on outline and two-point path rooms with `slope`; a platform with an `id` against the
walls as a ledge; two openings one above the other between the same two rooms; `trigger: step` with a plate, a room
and platforms (`sources`), `trigger: timer`, `trigger: load` with `opens` and `closes`; `not` and `any` in a
condition; `else_effects`; the `damage` effect; a `teleport` preset with a switch. Not used: `from_wall`/`to_wall`
(nothing needed them once the pits were holes), raking beams, `cast`, `summon`.

Refused, or not as said (exact messages):

1. A plate exactly 16 from a wall: `objects.yml: plates[0]: the plate does not lie inside room:a with every corner at
   least 16 from its walls: move it or make it smaller (to make a whole floor run the event, give the event the room
   as its `source`)`; 17 is accepted. With it comes a second message that contradicts itself: `wiring.yml:
   events[0].source: plate:p is a plate, which is clicked: a step event's source is a room, a level or platform with
   an `id`, or a plate (put a plate in front of it)`. Repro: `output/studio_cal/mm6_hive/repro/plate_16/`
   (`oymap validate <folder> --assets assets_dev`).
2. A gabled mouth under two domes' upright ends: `rooms.yml: openings[0].apex: a gabled opening's `apex` is the
   height of its point above the sill: at least 16 above `height` (where its sides end) and at least 16 below the
   lower of the two ceilings`. Repro: `output/studio_cal/mm6_hive/repro/gable_mouth/`. A rectangle may rise there, a
   gable may not, and the original's mouths are arches from the walls' tops.
3. An opening wholly above the ceiling: `an opening that rises above the ceiling into the upright end of a ceiling
   level is a rectangle that begins at least 16 under the ceiling (-1248 here): drop `shape`, or lower `sill``. With
   the 16 units two stacked openings must keep, the lower one ends 48 under the walls' tops.
4. An opening through the upright end of a level standing on another: `the opening reaches -864 but the lower
   ceiling of its two rooms is at -1248, and the wall over it (the upright end of a ceiling level) takes an opening
   up to -1040, 16 under its top line at the opening's sides`. So a dome whose first ring stands on the walls cannot
   open higher than that ring; the great hall's walls therefore go up to -1024 and the ring at -1024 is left out.
5. Three openings side by side with no wall between: `two openings in one wall of room:s79_ring_n overlap or stand
   closer than 16 units ...` (as documented; the strip became one room).
6. Rooms stack by `floor` and `ceiling` alone: the guard room's lower ramp, rejoined as one room under a ceiling
   that slopes with it, was refused (`rooms room:s65_ramp2 and room:s65_upper overlap: two rooms cannot share space
   (move one, or change their floor and ceiling so they stack)`), though its ceiling passes 157 under the upper
   floor where the two overlap. It stays in two rooms.

Tool observations:

- `oymap solve hive.blv --world mm6 --assets assets_dev` reaches the shaft and the deep tunnel (sectors 9 and 70) in
  the same wave as the great chamber: it does not take the hatch's cover (door 43, a horizontal slab that starts
  over the hole) as a barrier. The in-game picture `ingame_r2/diff/02-chamber-hatch.png` shows the cover shut in the
  original at the start.
- The scenario runner's `status()` holds only lines shown during a `play_lua` step: a step event's text shown during
  a `walk_to` is not in it (the playtest runs that handler again by its number).
- The `damage` effect (`evt.DamagePlayer(Players.All, const.Damage.Physical, 20)`) ran in the playtest with the
  party mortal and off the pads, and the party's hit points stayed 2042 of 2042. Cause not found (the gallery's fire
  damage of 3 does show); the handler's variable changes as it should.
- Round one's defect 2 stands: ten points on the ledge's edge (y 7168, sector 2) count as without a floor in the
  rebuild; they are 10.6 of the 94 points still lost.

### Gaps still open, most harmful first

1. **A cover over a floor hole.** A floor opening takes no door, so the hatch is open from the start: a party can
   drop to the shaft and the reactor's side at once, where the original needs the switch in the east cell (event 36;
   event 27 shuts it again). The cover is `ph:hatch`. Field: a door (`slide`, with a direction) on an opening
   `in: floor`.
2. **Movers that are not doors or lifts** (as round one's gap 7): the ring wall (sector 79 loses 29 points, 13 of
   them floor points under the wall), the gate blocks, the floor panel of the guard room, the buttons.
3. **A mouth that follows a dome's end** (messages 2 to 4): the two mouths of the great hall are a full-width
   opening to 48 under the walls' tops and a rectangle over its middle, with a bar 16 high across between them that
   the original does not have. If the bar is thought worse than piers, each pair goes back to one rectangle
   (width 944 and 936, heights 672 and 632, `along` 0.4874 and 0.4704). Field: `shape: gable` or `arch` into an
   upright end, through nested levels.
4. **Tunnels**: hexagonal section and a path that climbs (round one's gaps 3 and 5; sectors 10, 19, 20, 24, 33, 70
   at 0.81 to 0.85). 203 of the 290 rooms are tunnel pieces.
5. **One surface for a wall**: the hall's dividing wall (hvwl1a for 256, hvwl6 above, and only on its east face),
   the halls' outer walls (hvwl5a, a trim, the dome's texture above); room bands paint every wall. Sector 35's
   textures agree on 0.82. Also walls that lean (the halls' and cells' lower walls). Field: `walls[].bands`.
6. **A whole-ceiling level needs a convex room**: two door corners are rooms of their own and the great hall's north
   wall is one straight line (up to 60 off). Field: an outlined level that may touch the walls, or upright ends
   on an outlined level.
7. **Effects under their own condition**: the flush's handler (text always, damage unless protected) is two timer
   events and a variable, and the damage may come 10 seconds after the text. **A decoration as an event's source**
   (the keg, event 23). 21 water pads are not built (work, not vocabulary: a platform with an `id` each).
8. Stacking under a sloping ceiling (message 6). One-sided doors (round one's gap 9). Uneven floors (gap 11).
9. Not attempted this round: the reactor antechamber (sector 80, 0.77: a beam overhead, a second wall texture), the
   outer ring's ceilings (several sloping planes over non-convex rooms), the stepped corridor's two pitches in
   sector 69 (one pitch here), the great chamber's porch columns at the north door.


## Round three (2026-11-12, night): climbing tunnels, moving parts, pads and surfaces

The project files were edited by hand, with four recorded one-off helpers whose every value is measured from the
original (`output/studio_cal/mm6_hive/tools_r3/`: `edit_tunnels.py` and its log, `edit_s33_box.py`, `edit_pads.py`,
`edit_playtest_r3.py`; each was run once and its diff checked). Read-only helpers there: `tun.py` and `stations.py`
(an original tunnel sector's floor cross-lines as stations x, y, z), `fit.py` (samples the original's walkable floor
every 32 along a centre line and cuts it into the fewest climbing rooms of one grade within a tolerance), `chains.py`,
`try.py`, `rank.py`, `round.sh` (fmt, validate, build, compare, reach, solve), `play.sh`. The project as round two
left it is in `output/studio_cal/mm6_hive/r3_backup/`. The round-one generator in `gen/` was not run.

### Scores

| | `oymap compare` | distances | textures | floor points missing | mean ceiling difference | rooms |
|---|---|---|---|---|---|---|
| start of round three | 92.7 % | 95.2 % | 93.0 % | 25 | 20.3 | 290 |
| tunnels rejoined as climbing paths | 93.3 % | 95.9 % | 93.1 % | 23 | | 151 |
| ring wall and north gate as movers in one reactor room | 94.6 % | 96.3 % | 93.2 % | 10 | 19.7 | 151 |
| hatch cover, stepped corridor in its four parts, floor panel, sideways doors | 94.8 % | 96.5 % | 93.4 % | 10 | | 154 |
| the pads (16 water pads, 4 plain protected patches, the closet's water floor) | 94.8 % | 96.5 % | 93.4 % | 10 | | 155 |
| north and side halls: bands, dividing-wall panels | 95.2 % | 96.5 % | 94.6 % | 10 | 19.0 | 155 |
| reactor antechamber and its steps at their true heights and textures | 95.7 % | 96.8 % | 95.5 % | 10 | 16.4 | 156 |
| thresholds, two-faced leaves, true doorway widths, door 14 moved, box and lock textures (end) | **95.8 %** | **96.8 %** | **96.1 %** | 10 | 16.4 | **156** |

- `compare.py`: 15 in, 13 near, 7 out (round two: 15, 6, 14). Still out: the sizes per sector (156 rooms against 79
  sectors: min, q1, median floor area), doorway count and the widest doorway (full-width mouths).
- Rooms reached: 156 of 156 with the doors out of the way, 1 at the start (the original: 1 of 79). `oymap solve`:
  entry; the lock (quest bit 1204 for the load event); the double door (101 rooms); the click doors; the key door
  (item 2190); the rest. Same order as round two and as the original's waves.
- Playtest (`playtest.yml`, 261 steps, was 241): **passes**, 185 walks, 235 seconds of walking, no replans, no
  jumps, no stuck spots. New in it: the hatch's cover shut at the start and bearing the party (z -730 over the
  hole), uncovered by the floor at the head of the stepped corridor (event 27), shut and opened again by the switch
  (it toggles), then the drop of 1536; both leaves of the double door; a gallery pad setting and the floor beside it
  clearing protection; the closet's water floor and its floor button sinking (door 38 = mover:button50); the guard
  room's floor panel bearing the party at -1536, sliding away under it (drop to -2080) and coming back; the ring
  wall and gate standing until the load event with quest bit 1204, then sunk, and a walk over the ring's place into
  the outer ring's west side. That the ring and gate stop a walk before the event is shown by `oymap probe` (a
  scenario cannot expect a walk to be blocked): `oymap probe <L4> --assets assets_dev --from 2300,22400,-2256 --to
  1500,22400,-2256` stops at (2028, 22400) and the north probe at (4416, 25185), the same points as on `hive.blv`.
- In-game pairs (`output/studio_cal/mm6_hive/ingame_r3/diff/`, 16 from `shots_r3.yml` at the places changed):
  see the line under "What the pictures show".

Per sector, round two's end against round three's (compare's points lost): reactor 79 29.1 to 9.9; antechamber 80
5.7 to 1.1 (ceiling difference 137 to 0); north hall 35 9.7 to 5.3 (textures 0.82 to 0.94); tunnels: sector 10
distance agreement 0.78 to 0.98, 13 0.76 to 0.89, 20 0.74 to 0.95, 24 0.78 to 0.94, 25 0.90 to 0.90 (score 0.46 to
0.92), 29 0.82 to 0.94, 33 0.83 to 0.97 (floor difference 33 to 5), 70 0.82 to 0.85 (floor 12 to 3); stepped
corridor 69 floor difference 73 to 0.

### What changed

1. **Tunnels.** The original's tunnels are straight planar ramps between sharp mitred bends (the floor strip, 127
   wide, is one face per straight); round one had put its stations elsewhere on those lines and smoothed the bends.
   Each of the 13 chains (197 rooms) is now drawn on the original's own bend stations (`smooth` 0, snapped to 16;
   the old end points and end directions kept, so the rooms they open into still fit) and cut into climbing `path`
   rooms: 56 rooms, plus the level box under the south-west pit as a room of its own. A climbing path has one grade
   from end to end, so a chain is cut wherever the original's grade changes; `fit.py` puts each cut on a straight,
   just past a bend, at the original's measured floor height there, with every 32-unit sample within 16 of the
   original's floor (24 at the 96-degree turn out of the box, before it became a room). Floor error against the
   original, mean / max, round two to round three: s10 8.9/66 to 2.6/15, s11 15.7/46 to 3.5/14, s13 31.4/68 to
   2.3/8, s14 29.6/137 to 6.8/16, s15 8.5/80 to 2.8/14, s19 3.9/19 to 4.4/12, s20 5.0/21 to 3.9/13, s23 1.2/4 to
   0.9/3 (one room for 11), s24 6.9/37 to 3.6/13, s30 7.3/28 to 4.5/14, s31 8.0/38 to 3.7/11, s33 23.2/106 to
   4.5/16, s70 13.3/43 to 3.9/12; the centre lines now lie over the original's floor strip at 94 to 100 % of
   their samples (82 to 100 before). Width 224 and headroom 256 are kept (the hexagon's width at eye height; the
   original's head is 255). Where a chain ends at a level junction room of round one whose floor is not the
   original's, a stretch at that end follows the junction instead of the original (s11 and s13 at the flat chest
   alcoves, 160; s14 at j73, 300: the original climbs 190 through there; s20 at j75, 96; s33 at j74, 96). Two
   nearly level pieces holding flush pads were made level (s15_t6 at -768, s24_t4 at -897; the original is -768
   to -777 and -888 to -897 there).
2. **Reactor (sector 79).** The reactor room is the ring's outer hexagon (notched at the steps), as the original's
   one sector; the outer ring's three rooms open onto it along the ring's outer faces (seven openings with
   `from_wall`/`to_wall`, two rooms on three walls each). The ring wall (door 53: 128 thick, 1279 high, sinking
   1279 when the map is entered after the reactor is destroyed) is six convex outline movers; the north gate
   (doors 51 and 52) is one mover. Event 100 (`evt:load`) opens all seven with door 30 and shuts door 28.
3. **Hatch cover (door 43).** Six slats 480 by 47, 32 thick, 6 above the floor, as stretching movers whose west ends
   fold to the east, drawn at their folded pose and starting at `state: end` (shut). The switch in the east cell
   (event 36) toggles them; the floor at the head of the stepped corridor (event 27, its own room `s69_top` now)
   folds them. So the party again needs the switch, or the way up the stepped corridor, to drop into the shaft.
   Round two read event 27 as shutting the cover; it is the same "close" action as a door click, which moves a part
   by its travel, i.e. uncovers the hole (normal doors open with it; the cover is shut at the start in the
   game's picture of the original).
4. **Guard room floor panel (door 38).** The lower passage under the guard room rises to the guard room's ceiling and
   opens onto the upper floor above its join with the lower ramp; the panel is a stretching mover at the upper
   floor's height, retracting east into a 12-wide stub (the original reaches 31 further west, over the wall between
   the passage and the west room). Its switch (event 34) is on the wall over the panel, where the original's is.
5. **Doors.** The double door is `slide_left` with `leaves: 2` (doors 45 and 46) in its true 512 by 256 doorway
   (one picture over both leaves, gap 8); door
   28 `slide_left` (south) in its 256 by 256 doorway. All doorways have the original's widths now (13 of 15 exactly;
   10 and 12 are 224 against 256, the tunnel's width) and height 256; door 14 stood 320 out of place and is moved.
   Doors 1, 4, 10 and 12 show the wall's texture to the side they do not open from (`back_surface`, as the
   original hides its one-sided doors), door 8 shows hvwl5a to the guard room. 18 door openings have the original's
   trim threshold (hvtrim1, hvtrim4 at doors 1, 7, 8, 13).
6. **Pads.** All 26 of the original's water-pad faces are built: raised pads as platforms 16 high (gallery two, the
   four cell passages, antechamber, north-west cave, north tunnel, the box), flush ones as plates (north cell block,
   west passage, keg room, before door 5, east tunnel), the flush switch closet's whole water floor as its theme with
   the shelf along its north wall; plus the four plain floor patches with the protecting event (sectors 42, 61, 68,
   75). Event 56 and 58's sources follow them. The floor button of the closet (door 50) is a mover that sinks into
   the shelf when used.
7. **Surfaces.** North hall (sector 35): bands hvwl5a to 256, hvtrim2 to 288, hvceilb above; the dividing wall's east
   face a panel of hvwl1a for 2172 of its length and hvwl6 above, its west face hvwl6 whole. East and west halls:
   bands at the original's heights. Lock: the band of hvwl3 over the double door and the edge strips beside it.
   Antechamber: 256 high (ceiling -1824), hvwl5a, pad orWtr32; its steps cut at the lintel, the lower eight under a
   ceiling rising from -1856 to -1488 (`ceiling_slope` on a stepped room). Stepped corridor (sector 69): level,
   ramp, level, ramp, as the original (one ramp before). Box under the south-west pit: hvflori walls, hvflora ceiling.
   The reactor's north wall: hvwl3 and hvdorf panels where the shelf's mouth is.

### New features: which worked, which were refused

Worked: climbing `path` rooms (56, every one at the first build; joints on whole-unit points of a straight);
movers with `outline` (six ring segments) and with `at`+`size`; `stretch: true` with `state: end` (hatch slats,
floor panel); a mover sinking into a platform (the floor button); movers in `opens` of a `trigger: load` event and in
`toggles`/`closes` of switch and step events; a mover as an event's `source` (clicked); doors `slide_left` with
`leaves: 2` on a full-width opening; `back_surface`; `threshold` (18); `walls[].panels` with `from: end`, `bottom`,
full length; room `bands` together with panels on one wall; `ceiling_slope` on a room with `steps`; several openings
between the same two rooms with `from_wall`/`to_wall`; plates with `rise` 0 and a surface; platforms in climbing paths
and rough caves. Not used: `ends` (the original has no corner strips; its edge strips beside doors are panels),
`kerbs`, `auto_return_seconds`, `tread`.

Refused (exact messages; repros under `output/studio_cal/mm6_hive/repro/`, check with
`openyamm-studio/build/oymap validate <folder> --assets assets_dev`):

1. A mover that rises into the ceiling (`repro/mover_into_ceiling/`): `objects.yml: movers[0]: the mover's top at its
   end (after `travel`) is at 384, above the ceiling of room:a there (256): shorten `travel` or `height`, or lower
   `bottom``. The gate's upper half (door 52) rises 639 into the ceiling; the gate is one block that sinks its full
   height here (same shut and open poses, other motion; the original's halves are combs of three teeth).
2. A mover pushed into its wall (`repro/button_into_wall/`): `objects.yml: movers[0]: the mover's corner [272, 520] at
   its end (after `travel`) is not inside room:a: a mover stays in its room. Shorten `travel`, move the block, or
   make the room one room over its whole way`. The five wall buttons (doors 16, 31, 35, 37, 41: boxes 10 deep that
   go 8 to 10 into the wall) stay flat switches.
3. A plate in a climbing path (`repro/plate_in_climbing_path/`): `objects.yml: plates[0]: a plate needs a level floor
   and room:tunnel slopes or has steps: give the event the room itself as its `source`, or put the plate in the room
   at the slope's foot or head` (as documented). Two tunnel pieces were made level instead.
4. A level at the room's own height, for a flush patch (`repro/flush_pad/`): `rooms.yml: rooms[0].levels[0]: a level
   is a simple counter-clockwise outline at a floor height other than the room's, in a room with a level floor`;
   plates say it in level rooms.

### What the pictures show

16 pairs at the places changed (`output/studio_cal/mm6_hive/ingame_r3/diff/`, cameras in
`output/studio_cal/mm6_hive/shots_r3.yml`): mean edge agreement 0.76, blurred difference 0.044. Ring wall from inside
0.96, the north hall's dividing wall 0.96, hatch cover 0.93, antechamber and steps 0.93, box under the south-west pit
0.87 (0.63 before its textures were set), gallery pads 0.85, guard-room panel 0.84, double door 0.74, north gate 0.73
(the same solid wall, its texture half a tile off), tunnels 0.64 to 0.67, stepped corridor 0.62 (the same shape; the
textures' offsets differ), flush closet 0.53 (the camera stands higher in the rebuild's picture; not found why).
Looked at: the tunnel bends now fall where the original's do, and what differs is the hexagonal section (the
original's narrow floor and leaning lower walls); the double door is the one picture over both leaves (gap 8).

### Gaps still open, most harmful first

1. **A tunnel's cross-section** (all 13 tunnels, 59 rooms; the in-game tunnel pairs are the least alike pictures):
   the original's hexagon (floor 127, 256 at mid height 127, ceiling 127 at 255) is a rectangle 224 by 256. Field:
   `section: {floor_width, mid_width, mid_height}` on a path.
2. **Heights per path point.** A climbing path has one grade, so a tunnel that is level, then ramps, then levels is
   cut into a room per grade (56 rooms where 13 to 17 would do, with joints that must lie on whole-unit points of a
   straight just past a bend). Field: path points `[x, y, z]`, or `heights` beside `path`.
3. **Side openings in a climbing path, and junctions that ramp.** Every junction is a level, axis-aligned room of
   round one: j73 at the keg room is level at -1400 where the original ramps from -1536 to -1352 past the keg
   room's mouth (the mouth 60 above the ramp, which is why the original never reaches the keg room); j47, j49,
   j74, j75 and the chest alcoves (flat at -1820 where the original runs -1867 to -1772) likewise. Field: an
   opening in a climbing path's side wall with a `sill` above the path's floor there.
4. **A mover that goes into the ceiling** (refusal 1): the north gate's upper half. Field: allow a mover's travel to
   end above the ceiling (hidden in it), as the floor already allows below.
5. **A mover pushed into a wall** (refusal 2): the five buttons. Field: allow travel into the wall it stands against,
   or a `button` kind of switch with a depth and a travel.
6. **A room nothing reaches.** The shelf over the reactor's north strip (x 3776 to 6080, y 26118 to 26374, floor -1424
   to -1360, ceiling -1232) opens onto the outer ring 832 above its floor; built, it is a room `solve` never
   reaches (it was built and measured: textures 95.9, distances 96.9), so it stays solid with its textures as
   panels. Field: a recess on a wall (`niches: [{wall, offset, length, bottom, height, depth}]`), or `unreached: true`
   on a room that should not count.
7. **Plates in climbing paths** (refusal 3): the flush pad in the east tunnel and the one before door 5.
8. **A picture on each leaf of a two-leaf door.** The double door's surface is stretched over both leaves together,
   so each half shows half of hvdord, where the original's two leaves (doors 45, 46) each carry the whole picture
   (`ingame_r3/diff/13-double-door.png`; `fit` or not makes no difference). Field: `leaf_surface`, or the surface
   applied per leaf when `leaves: 2`.
9. Still open from round two: effects under their own condition (the flush handler), a decoration as an event's
   source (the keg, event 23), uneven floors (the chest alcoves), the leaning lower walls of the halls and cells,
   the bar 16 high between the great hall's two mouths (the lead's decision), fixed actors (reactor, Queen).

Work left that the vocabulary can already say: the door-frame edge strips (HVWL1LE/RE, HVWL4LE/RE, hvwl6LE/RE beside
the cell doors 2, 3, 36) as panels; the lintel's recess over the antechamber steps (up to -1728); the junction rooms
redrawn on the original's tunnel lines.

### Tool defects

1. `oymap compare hive.blv --world mm6 --with <L4> --assets assets_dev`: a worst point at (5632, 19712) in sector 79
   stands inside the original's ring wall (the triangle at its south-east corner is the top of door 53, 128 thick):
   "the rebuild has a wall down to the west at 84 where the original has nothing within 4096". Round two's fix
   leaves out points inside thin blocks only.
2. `oymap validate output/studio_cal/mm6_hive/repro/mover_into_ceiling --assets assets_dev` (and `button_into_wall`):
   after a refused mover a second line says `wiring.yml: events[0].opens[0]: there is no door mover:gate_high in
   objects.yml`: it calls the mover a door and is a follow-on error of a refused object (those were to be suppressed).
3. `oymap validate output/studio_cal/mm6_hive/repro/plate_in_climbing_path --assets assets_dev`: after the refused
   plate, `plate:pad is a plate, which is clicked: a step event's source is a room, a level or platform with an id,
   or a plate (put a plate in front of it)` contradicts itself (round two's message 1, still there).
4. `ids.lock.yml` keeps `door:d51`, `door:d52`, `evt:door51`, `evt:door52` after the objects are gone; rooms that are
   gone are pruned.
5. `oymap probe` has no vertical ray (nothing checks a floor hole or a cover over one), and a scenario's `walk_to`
   cannot expect to be blocked (the ring's and gate's blocking had to be shown with `probe`).
6. Suspected: `oymap compare`'s points at y 26368 in front of the Queen's gate (sector 79, e.g. (3072, 26368)) say
   "the rebuild's wall to the east is 1289 nearer"; the original has face 3431 (HVWL1A, x 3776, y 26246 to 26374,
   z -2256 to -1680) facing west at 704 there, as the rebuild does. A ray slipping past the corner at (3776, 26374)?
7. For helper scripts: PyYAML reads the switches' `off:` key as a boolean (`objects.yml` must not be dumped with it).

### Unsure in the original

- Door poses: read here as "state 0 shows the file's pose; a click's close moves the part by its travel" (normal
  doors open that way; the game shows the hatch's cover shut, the ring wall standing and the north gate as a solid
  wall at the start). With that, event 27 uncovers the hatch, not shuts it as round two wrote.
- Doors 51 and 52 start in state 2 with attributes 3; in the game the gate is a solid wall at the start, and how the
  two three-toothed combs close it was not traced face by face.
- The keg room is never reached in the original (its mouth is 60 above the ramp); the rebuild still reaches it.

## Round four (2026-11-12, night): the tunnels' cross-section, one room per run

Brief: `devdocs/map_studio/rounds/ROUND_FOUR.md`. The project as round three left it is in
`output/studio_cal/mm6_hive/r4_backup/`. Every edit of this round is a recorded one-off script in
`output/studio_cal/mm6_hive/tools_r4/`, each number in it measured from the original's export (`orig_r4.json`) and
named where it comes from: `edit_tunnels_r4.py` (the tunnels, junctions, side rooms, pads; its log
`edit_tunnels_r4.log`), `edit_mouths_r4.py` (the great hall's two mouths), `edit_s66_r4.py` (the ramp and stair up
from the south-east cave), `edit_cells_r4.py` (the three cells' domes), `edit_playtest_r4.py` (walk targets);
`apply_r4.sh` ran them in order on the round-three files while they were being worked out. The project files are
the source from here on; those scripts are not to be run again. Read-only helpers there: `xsec.py` (the original's
section square to a stretch), `prof.py` (its width by height band), `near.py` (a sector's faces in a box),
`chain4.py` (the round-three chains with the original's floor at every point), `pts.py` (a compare's points.json by
sector), `tex.py` (texture area by section part), and round three's `tun.py`, `stations.py`, `sec.py`, `rank.py`,
`round.sh`, `play.sh`.

### Scores

| | `oymap compare` | distances | textures | without a floor in the rebuild | mean ceiling difference | rooms |
|---|---|---|---|---|---|---|
| start of round four | 96.7 % | 96.9 % | 96.3 % | 0 | 16.4 | 156 |
| every tunnel one room with the section, junction boxes gone | 96.6 % | 97.2 % | 96.4 % | 4 | 16.3 | 100 |
| great hall's mouths without the bar | 96.7 % | 97.3 % | 96.4 % | 4 | 16.3 | 100 |
| tunnel through the chest alcoves, alcoves as side rooms | 96.8 % | 97.3 % | 96.5 % | 4 | 16.3 | 100 |
| ramp and 15 steps up from the south-east cave (sector 66) | 96.8 % | 97.4 % | 96.5 % | 4 | 15.9 | 100 |
| domes of the three round cells (end) | **97.0 %** | **97.7 %** | **96.6 %** | 4 | 14.5 | **100** |

- Rooms 156 to 100: the 56 climbing path rooms, the nine level junction boxes and the chest room became 8 tunnels
  (`room:s10_tunnel` sectors 10 to 13, 19 points; `s14_tunnel` 14 to 18, 17; `s19_tunnel` and `s20_tunnel` 19 to
  23, 11 and 19, two rooms only because a path takes at most 24 points; `s24_tunnel` 24 to 27, 20; `s30_tunnel` 29
  and 30, 13; `s33_tunnel` 33, 31, 32, 12; `s70_tunnel` 70, 5) and two alcove rooms. Left as boxes: the junction
  before the west cell (`s13_j49`, below), the box under the south-west pit (`s33_box`: the original's own box) and
  the room under the south-west pit (`s6_low`).
- Rooms reached: 99 of 100 with every door out of the way (round three 156 of 156; the original by today's
  `oymap solve` 79 of 79). Not reached: the keg room, see "What changed" 3. `oymap solve`: entry; quest bit 1204;
  the double door (41 rooms); the click doors (17); the switches (3); door 6 (8); the key door, item 2190 (13); the
  rest (15). Same order as round three measured with today's tool (1, 1, 96, 17, 5, 8, 13, 15 of 156); the
  original's waves are 1, 1, 50, 9 with item 2190, 3, 7, 8 (today's solve puts the key door earlier there than in
  either rebuild, as it did at the start of the round).
- Playtest (`playtest.yml`, 266 steps, was 261): **passes**, 190 walks, 239 seconds of walking, no replans, no
  jumps. Walk targets in tunnels moved onto the path's line (41 of them, `tools_r4/edit_playtest_r4.log`); new: into
  both chest alcoves (chest 4 now stands in the east alcove), the flush closet's floor walked onto deeper (the room
  starts 16 further from the tunnel), the targets on the sector 66 ramp at its new heights.
- In-game pairs (`output/studio_cal/mm6_hive/ingame_r4/diff/`, 20 from `shots_r4.yml`): mean edge agreement 0.70,
  blurred difference 0.051. The tunnels 0.66 to 0.72 (round three 0.64 to 0.67): the section is the original's
  (narrow floor, leaning lower and upper sides, the mitres at the bends fall together); what still differs in them is
  the textures' offset along the sides. The great hall's mouths 0.88 and 0.91, the cell dome 0.76, the alcove 0.61
  (its doorway is 160 wide, the original's alcove opens over its whole width), the sector 66 ramp 0.56 (same shape,
  the wall texture's offset).

Per sector, start to end (compare's score): 12 chest alcoves 0.83 to 0.91, 66 0.81 to 0.98, the cells 46, 48, 50
0.88..0.89 to 0.95..0.97, 35 0.961 to 0.964 (4.7 to 4.4 points lost), 10 0.98 to 0.99, 19 0.90 to 0.92, 24 0.95 to
0.99, 29 0.95 to 0.99, 13 0.92 to 0.93, 70 0.89 to 0.90; 11 0.86 to 0.79, 18 0.93 to 0.75 and 33 0.97 to 0.82, each
losing one point that stands on the original's widened floor where the rebuild's tunnel is 128 wide (gap 3).

### What changed

1. **Every tunnel has the section** `[[-64, 0], [64, 0], [128, 128], [64, 256], [-64, 256], [-128, 128]]`. Checked
   against sectors 24 (level stretch x 5456..6144: floor -65..60, at 128 up -127..123, top -72..67 at 255) and 20
   (x 7360..8048: floor -65..61, 126 at 130 up, top 257 up), with `xsec.py` and `prof.py`. Heights at path points:
   the original's flat tunnel floor at each bend, and a point added on a straight where the original's floor
   leaves the straight ramp by more than 10 (five, all in the east tunnel: its level start, the pad, sector 26's
   level stretch and the kink in sector 27). Ends, from the original's portals: mouths `shape: section` into the
   great chamber (2077), the north-hall vestibule (3306), the south-east cave (2078), the north-west cave (3230, its
   last 64 drawn along x and the cave's wall there upright, because the portal is on a slant) and tunnel to tunnel
   (the north-east run's joint); square ends where the original fans to a rectangle: sector 10's north end (256 by
   256 over 136), doors 12 and 10 (256 wide, fanning over the whole first stretch, as the original's 835), door 5
   (128 wide over the whole last stretch), the shaft (256), the south-east pit (215, square to its wall), the box
   under the south-west pit (256, fanning over 312 where the original's fan is 594 long, see gaps), the north-west
   cave (256 over 256) and both sides of the junction box `s13_j49` (224 and 256).
2. **Junctions are side doorways** in the stretch the original has them in, its leaning sides running to the jambs:
   the south-west cell's passage (sector 47; the stretch is the whole straight (-1000, 4000) to (-1982, 3836) as in
   the original, so the floor fans out to the doorway from the bend), the chest room (sector 75; the bend moved to
   x 4781, 32 west of the original's jamb on its bend at 4813), both cell blocks of sector 22 (in one stretch, one
   each side, exactly at the original's lines y 11328 and 11584), the switch closet (74), the east cells' passages
   (51 and 45; that straight drawn on the line of sectors 26 and 27's widest points, y 5745), the keg room (73).
   Sills of 16 where the original has them (47, 51, 45). The side rooms' walls are 16 beyond the tunnel's widest
   line (passages 51, 45, cells 56, 61, closet 74, chest room 75; passage 47 16.8 beyond, parallel to the askew
   straight): in the side's own plane the build warns that the sill strip lies in two planes.
3. **The keg room's doorway** (sector 73) stands in the straight that climbs 0.28 from (-4128, 6816) at -1536 to
   (-3744, 7392) at -1342, where the original has it (jambs about -1456 and -1401), the keg room at the original's
   -1352. The original reaches it by a steep ramp face in the tunnel's side (face 3811) and lifts its ceiling to
   -1104 over the doorway; neither can be said, so the doorway is 154 wide from -1352 to -1228 and the room is not
   reached (`oymap solve`: "no floor at (-4037, 7184, -1392)"). Round three had a level junction at -1400 and the
   keg at -1360. Making it reachable would take the keg floor down to about -1420 or the doorway 280 up the ramp.
4. **The chest alcoves (sector 12)** are the tunnel's own stretch (its south side leans as in the original; round
   three's chest room had an upright wall there) with the two alcoves as rooms off its north side: east x -2810..-3210,
   west -3241..-3619, the pier 31 wide (the original's 32), back walls y 4230, floors ramping from the doorway's level
   up to -1772 at the back (`floor_points`), ceilings from -1590 / -1544 at the front to -1498 at the back. Doorways
   160 (east) and 320 (west) wide: the original's alcoves open over their whole width and above the tunnel's top.
5. **The great hall's mouths** (portals 2240 and 2241) are each a full-width opening to the walls' tops and a
   rectangle touching it above (no bar): east to -846 (the east hall's first ring, 16286..17272), west to -902 (16
   under the west hall's first ring; -886 would be on that ring's line but not on the great hall's sloping end line,
   which is -885.8 there). The original's upper parts are a flat-topped trapezoid to -787 (east) and an arch with
   shoulders at -886 to a point at -787 (west); a gable or arch cannot rise above a ring's flat top, which is the
   upright end's top line.
6. **Pads in tunnels**: the east tunnel's flush pad is a plate across the stretch (x 7540..7776; the original's
   7518..7774: a path point stands at 7520 and a plate keeps 16 from it); the pad before door 5 a plate across the
   square end's stretch (-1540..-1426, as round three); the north-west loop tunnel's pad (sector 29, x -547..-291) a
   plate across its stretch, -528..-308: the original's is a wedge whose west edge stands 16 above the floor beyond
   it, round three's a platform 16 high, and a tunnel takes no platform. The box's pad and the low room's pad stay
   platforms (plain rooms). Event 58's sources name the whole tunnels now where they named one piece of one: the
   original has it on the floor round each pad and at the junctions, and walking off a pad clears protection in both.
7. Outside the tunnels: **sector 66** (the way up from the south-east cave) ramps from -1569 to -1381 over x
   4511..5023, runs level to 5279 and climbs 15 steps of 15 (hvtrim1 treads) to -1156, the ceiling parallel (round
   three: level at -1569 and 11 steps). **The three round cells** (46, 48, 50) have their domes: walls to the foot
   ring, `ceiling_points` at the original's ring vertices and apex one for one (17, 17, 25 points), where the dome
   changes slope.

### New features: which worked, which were refused

Worked: `section` on 8 tunnels with path points `[x, y, z]` (up to 20 points), `start`/`end` square ends with
`length` and `width` (and a door in one: doors 5, 10, 12), `shape: section` into upright walls, through a wall into
a rough cave and tunnel to tunnel; side doorways in level and climbing tunnels with `sill`, `width: full`; plates
across a tunnel's stretch; `floor_points` with `ceiling_slope` (alcoves); `floor_points` with `ceiling_points` (sector
66 landing); `ceiling_points` for domes; `tread` on a stepped room; two openings touching one above the other. Not
used: `floor_lines`, `floor_plane`, `levels[].bank`, `top_slope`, gable or arch into an upright end (see 5).

Refused (exact messages; repros under `output/studio_cal/mm6_hive/repro/`, check with `openyamm-studio/build/oymap
validate <folder> --assets assets_dev`):

1. A platform in a tunnel (`repro/tunnel_platform/`): `rooms.yml: rooms[0].platforms: a tunnel (a path room with a
   section) takes no platforms: its sides run from point to point of the path as the section draws them, so it has
   no upright walls, floor or ceiling of the usual kind to carry one. Drop it, or make this stretch a room of its own
   without section` (as documented). The north-west tunnel's raised pad.
2. Two tunnels with different sections end to end (`repro/tunnel_two_sections/`): `the two tunnels do not end in one
   and the same section here ... give both the same section` (as documented). The deep tunnel's wide first 1900.
3. A path of more than 24 points: `rooms.yml: rooms[5].path: allows at most 24 items` (the north-east run, 28: two
   rooms joined by a section joint).
4. A side doorway the side room's whole width: `width: 256` gives `the opening is 256 wide but the two rooms share
   only 256 units of wall (it needs 16 on each side)`; `width: full` works for the passages and cell blocks, but not
   for the chest room (`repro/side_door_full_width/`, tool defect 1), whose doorway is 224 (the original's 256).
5. Still refused from round three, left as they are: the gate's upper half into the ceiling
   (`repro/mover_into_ceiling/`) and the five wall buttons into their wall (`repro/button_into_wall/`). Round three's
   `repro/plate_in_climbing_path/` now passes.

### Gaps still open, most harmful first

1. **A side doorway that rises above the tunnel's top, and a ramp up to it in the tunnel's side.** The keg room is
   not reached (3 above), the chest alcoves open through doorways 160 and 320 wide under the tunnel's top where the
   original opens them whole. Field: `side_bay: {from, to, ceiling}` (the tunnel's ceiling lifted over a stretch of
   its side) and a doorway `ramp` (a sloping floor piece from the tunnel's floor to the sill).
2. **A section that changes along the way.** The deep tunnel (sector 70) is wider for its first 1900 units (floor
   200 to 250, widest 300 to 320, top lopsided; then floor 150, widest 296 to x 11072, narrowing to the standard by
   12100); sectors 26, 27 and 31 are 266 to 293 high and lean (floor strip 26 north of the widest points in 26 and
   27, the floor tilting across in 27). One standard section is used throughout. Field: `section` per point or per
   stretch (`sections: [{from_point, outline}]`), the build lofting between them; or tunnels of different sections
   joined end to end.
3. **Fans: floors that widen toward a junction or an end.** The original's floor widens over a whole stretch toward
   a doorway (sector 18 toward door 5: 127 to 207; sector 33's fan from the box over 594 at a slant to its square
   end; the junction fans of 11 and 47): four of compare's points stand on such floor where the rebuild's is 128 wide
   ("without a floor in the rebuild"). A square end must be square to its stretch, so sector 33's fan is drawn along
   x over 312. Field: `start|end: {length, width, floor_width}` with the floor widening too, and a square end at an
   angle to its stretch.
4. **A junction at a bend** (sector 13 / 49): the passage continues the north leg while the east leg joins its side at
   the bend; still the level box `s13_j49` with square tunnel ends. Field: a side doorway at a path point (between
   the two stretches' sides), or a tunnel branching from another's side through a section mouth.
5. **The great hall's mouths' upper parts** (5 above). Field: `shape: trapezoid` (flat top), or a gable/arch whose
   top may stand on a ring's flat-top line.
6. Still from round three: movers into the ceiling and into a wall (gate's upper half, five buttons), a picture on
   each leaf of a two-leaf door, effects under their own condition, a decoration as an event's source, the reactor
   shelf no one reaches, fixed actors.

Points still named by `points.json`, not tunnels: the reactor (sector 79, 8.6 points of 507: the ring and the north
strip's sloping ceilings), the north hall (35, 4.4), the north-west cave (34, 2.7: a terraced roof of 135 faces at
-1281, -1161, -1073, -1041, more than a cave roof's point budget), the Queen's chamber (77), the antechamber (80).

### Tool defects

1. `oymap validate output/studio_cal/mm6_hive/repro/side_door_full_width --assets assets_dev`: a side doorway with
   `width: full` into a room whose wall lies inside the tunnel's side is placed `from 0 to 426 along a side 745 long`,
   from the side's start to the room's far corner, not over the 256 the two walls share.
2. `oymap validate output/studio_cal/mm6_hive/repro/side_door_ceiling --assets assets_dev`: a side doorway in a
   climbing tunnel may reach only `-1640` (the floor at the point before its stretch plus 256), not the tunnel's
   ceiling at its lower jamb (about -1602); drop the path's first point and the same doorway passes.
3. The build's warning for a side doorway whose room's wall lies on the tunnel's widest line (`opening ... is in a
   wall without thickness and leaves wall round it`) names no way out but moving the room; for a sill strip of 16 the
   message could say so.
4. `ingame_compare.py` skips a shot whose point has no floor in the original without saying which map's floor it
   looked for at which height (the first try of `keg-ramp`).
5. From round three, still: `ids.lock.yml` keeps door ids after their objects are gone; `probe` has no vertical ray.

## Round five (2026-11-13): contents, the kill flow, movers, the hall mouths

Brief: `devdocs/map_studio/rounds/ROUND_FIVE.md`. The project as round four left it is in
`output/studio_cal/mm6_hive/r5_backup/`. Edited by hand; two recorded one-off scripts whose every number is the
original's own vertex (`output/studio_cal/mm6_hive/tools_r5/edit_halls_r5.py`: the east and west halls' domes as
points and their mouths as one opening each; `edit_north_hall_r5.py`: the great north hall's dome as points), each run
once and its diff checked against the copy beside it (`rooms_before_halls.yml`, `rooms_before_north_hall.yml`); the
`ceiling_lines` after them by hand. Helpers: `tools_r5/round.sh` (fmt, validate, build, compare, reach, solve),
`play.sh`, `rank.py`, `final4.sh` (final measure and four playtests).

### Scores

| | `oymap compare` | distances | textures | rooms |
|---|---|---|---|---|
| start of round five | 97.0 % | 97.7 % | 96.6 % | 100 |
| monsters, item, kill flow, gate combs, buttons | 97.1 % | 97.7 % | 96.6 % | 100 |
| east and west halls' domes by points, one mouth each | 97.1 % | 97.7 % | 96.6 % | 99 |
| five openings pinned, chest room 256, alcoves 348 and 347 | 97.2 % | 97.8 % | 96.7 % | 99 |
| great north hall's dome by points | 97.2 % | 97.8 % | 96.7 % | 99 |
| three walls' panels round the buttons, chest 2's key and trap (end) | **97.2 %** | **97.8 %** | **96.8 %** | **99** |

Per sector, start to end: 35 (great north hall) 4.4 to 3.6 points lost (mean ceiling difference 14 to 10), 37 0.8 to
0.7 (6 to 2), 38 0.9 to 0.8 (18 to 4), 12 (chest alcoves) 0.91 to 0.94. `compare.py`: 22 in, 9 near, 4 out.

### Contents

- **Placed monsters: 2 of 2.** The original's scene has two actors and both are `monsters[]` now, at its places:
  the Reactor (monster_data 647, actor 0, on the dais at z -2128) and the Demon Queen (646, actor 1, in her
  chamber), group 85, hit points and hostility as their kinds (the records hold no facing). The three placeholders
  are gone.
- **Lying items: 1 of 1.** Item 1817 (Feather Fall scroll, the scene's one sprite object) on the lock's floor at
  (128, 5248); the playtest picks it up.
- **Chests: 5 of 5 with the original's contents.** Read from `initial_state.chests` (each record's items: -6 is a
  random item of level 6): records 1, 3, 4, 5 (events 41, 43, 44, 45) two random items of level 6 each, not trapped,
  as the rebuild had them; **record 2 (event 42, the chest room off the north-east tunnel) holds the key to door 6
  (item 2190) besides two random items, and is trapped**: the rebuild had it as two random items, and the playtest
  had granted the key from outside since round one. `chest:c2` now has `items: [reactor_way_key]`, `trap_level: 1`
  (the record holds only the trapped bit). Record 0 (two random items, trapped) is opened by no event and has no
  chest in either map.
- **The keg** (event 23, title Keg: " +20 Hit Points" and 20 hit points on each click) stays a decoration at its
  place without its event: no preset takes a decoration as its source (`wiring.yml: events[0].source: a script
  preset cannot have the decoration deco:keg as its source`, the same for text and switch; repro
  `output/studio_cal/mm6_hive/repro/keg_decoration_source/`), and its room is not reached (below).

### Events, the original's against the rebuild's

`oymap flow hive.blv --world mm6 --assets assets_dev` lists 48 handlers; 65000 and 65001 (Nicolai's kidnap and
state) are the world's and stand in every MM6 map's list, so 46 are the map's own. **35 the same, 7 differ, 4
missing.**

| Original | Rebuild | |
|---|---|---|
| 1, 2, 3, 7, 8, 9, 13, 14 doors; 6 the key door (item 2190 taken, "The door is locked") | evt:door* | same (9 also sets `north_way`, below) |
| 4, 11 doors that open from one side | `condition` on a variable set by the door on the only other way round (42, 9) | differ: no one-sided door word |
| 5, 10, 12 doors that open from one side | open from both sides | differ |
| 21 "The Door Won't Budge" (door 5 from the chamber) | — | missing (door 5 opens from both sides) |
| 16 flush button: carried to the entry, button in or out, map var 2 = 0, text | evt:switch16 on `mover:button16` | same (the button moves since this round) |
| 17, 19 the lock's floors (text; arm) | evt:flush_notice, evt:flush_arm on plates | same |
| 22 the closet's floor clears map var 5, which nothing reads | — | missing (does nothing) |
| 23 the keg | — | missing (decoration source) |
| 27 the corridor head uncovers the hatch | evt:hatch_top | same |
| 28 door 28; 38 door 42; 39 the double door (45, 46) | evt:door28, evt:door42, evt:door45 (two leaves) | same |
| 29 the Queen's floor disarms the flush | evt:queen_floor | same |
| 31 button 31 pushed, door 32 | evt:switch31 on `mover:button31` | same (button moves since this round) |
| 33 button 35 and door 36 toggle | evt:switch33 on `mover:button35` | same (button moves) |
| 34 button 37 and the floor panel (38) toggle | evt:switch34 on `mover:button37` | same (button moves) |
| 36 button 41 and the hatch cover (43) toggle | evt:switch36 on `mover:button41` | same (button moves) |
| 41 to 45 chests | evt:chest1 to 5 | same; chest 2's key and trap since this round |
| 48 the south exit | evt:exit_south | same |
| 50 floor button, flush off for good | evt:switch50 on `mover:button50` | same |
| 51 "Flush sequence complete" | evt:flush_complete | same |
| 54 "Flush sequence in progress", 20 damage unless on a pad | evt:flush_run, **one handler since this round** | same (text after the damage) |
| 56, 58 pads protect, floors round them unprotect | evt:pad_on, evt:pad_off | same |
| 57 the warning | evt:flush_warning | same |
| 60 the final exit (quest bit 1226) | evt:exit_final | same, with the good ending of 65012 (below) |
| 100 on entering: ring, gate, Queen's gate open, door 28 shut (quest bit 1204) | evt:load | same |
| 65010 (map supplement) a physical blow to the reactor does 2 to 40 | — | missing: no damage hook |
| 65011 (supplement) reactor killed with the Ritual of the Void: 16 summons at tier C, the doors of event 100, the party carried before the Queen's gate, restored; without it the bad ending; the Queen killed after it: quest bit 1226 | evt:reactor_dead, evt:reactor_dead_bad, evt:queen_dead (`trigger: timer`, `once`, `kills`) | differs: run at the next two-second tick, the item tested then, the original's random 120 left out of the carry |
| 65012 (supplement) on leaving after the reactor: the good ending (Queen dead, Ritual held) or the bad | the good ending as effects of evt:exit_final | differs: no leave trigger, so leaving by the south door after the reactor is not the bad ending |

The flush (target 4): the original's event 54 is one handler whose damage has its own test inside it. A condition
`lua` guards the whole handler (doors, sets, effects, text), so it cannot say "the text always, the damage unless
protected"; one event does say it with a Lua step in `effects`: `if not IsAtLeast(MapVar(8), 1) then
evt.DamagePlayer(Players.All, const.Damage.Physical, 20) end` (map variable 8 is `protected` in ids.lock.yml: a Lua
step cannot name a wiring variable). Round two's second timer event and its variable are gone.

### Playtest

`playtest.yml`, 275 steps (round four 266), 191 walks, about 234 seconds of walking: **passes four runs of four** (`output/studio_cal/mm6_hive/run/play_r5_1..4.log`), no replans, no jumps. New in it: the scroll picked up in the lock;
before each chest the packs emptied of what earlier chests rolled (all but the scroll and the key), so no loot
depends on the rolls; chest 2 gives the key and door 6 takes it (no `grant_item` for it any more; the locked side of
door 6 cannot be met on the walk, as the chest lies on the way); the five buttons in and out; the flush as one
handler; the ring and both gate halves standing while the reactor lives; the Ritual of the Void granted (it comes
from another map), the reactor struck down (`damage_actor`: it is not hostile to the party by its tables, so the
walks' sweep leaves it), the kill flow's doors open and the party carried to (3328, 25920) (`advance_runtime` with
`follow_map_move`: a timer handler's move within the map is not followed by a `play_lua` `wait()`), the final exit
locked while the Queen lives, the Queen struck down (quest bit 1226, map variable 13), out through the gate between
the lower half's teeth, and the final exit to New Sorpigal (`assert: {map: oute3.odm}`). The summoned monsters are
cleared by the walks' sweep.

### What changed

1. **Contents and the kill flow** (above). The reactor's death now does what the original's map supplement does;
   before, killing it did nothing in the rebuild and the playtest set quest bit 1204 by hand.
2. **The north gate (doors 51 and 52)** is two movers as in the original: `mover:gate_low`, a comb from the floor to
   -1616 with three teeth to -1488 (`parts`), sinking 638 so its teeth stay 128 above the floor (the original's body
   stops 1 above the floor, here 2); `mover:gate_high`, a comb from -976 down to -1616 with three teeth to -1744,
   rising 639 into the ceiling and leaving its teeth hanging, as the original's. Round three's single block that sank
   whole is gone.
3. **The five wall buttons** (doors 16, 31, 35, 37, 41) are movers 10 to 16 out of their walls, pushed 8 to 10 into
   them, the click sources of their events (the five flat switches are gone), with the original's front and side
   textures. Two walls round them got the original's panels: the closet's east wall (hvwl3spa panels, hvtrim1 strips
   over and under the button), the south cell's south wall (the carved hvwl4le/hvwl4re panel and an hvwl3 band; its
   outline loses a slanted corner that is a niche 96 above the floor in the original, so the wall stands at y 2188 as
   the original's), the east cell's north wall (hvwl2le/hvwl3le/hvwl2re and hvtrim2).
4. **The great hall's mouths** (target 3). The true outlines (portals 2240 and 2241): east, from y 16080..17515 at
   the floor, the sides leaning out to 15992 and 17553 at -1280, in to 16043 and 17482 at -1024, a flat top at -787
   from 16286 to 17272; west, 16296..17787 at the floor, 16296 and 17857 at -1280 and -1248, an arch through 16347
   and 17786 at -1070, 16515 and 17618 at -886, to its point at 17272, -787 (off the middle). The three domes on
   either side (sectors 35, 37, 38) are now `ceiling_points` taken from the original's ceiling vertices one for one
   (north hall 23 + 26, east hall 27, west hall 26 points, with `ceiling_lines` along the rings), so each dome's end
   on the mouth's wall is the original's own line, and each mouth is one opening, `width: full, height: full`,
   cut to the lower of the two domes point by point: the trapezoid and the arch, exactly. The two-part mouths, the
   rectangles and the round-two recess room of the east hall are gone (99 rooms). `trim_to_wall` was used first,
   with the halls' domes by points and the north hall still in levels; with all three domes by points the build says
   it does nothing and it was dropped. The lower sides stand upright (the original's lean) and the west mouth ends at
   17797, where the great hall's north wall is drawn straight.
5. **Openings pinned** (`from_wall`, `to_wall`): five, each the pair the original has (portals read from the export).
   One was wrong until now: the chest room's doorway (`open:s19_tunnel__s75_chest`) had been placed on the chest
   room's far wall, 256 behind the tunnel (the longest shared stretch), not on its 256-wide neck; pinned, it takes
   `width: full`, 256 like the original's (x 4816..5072, the original's 4813..5069). Round four's "tool defect 1"
   (`repro/side_door_full_width`) was this choice of wall pair.
6. **The chest alcoves** (target 6): doorways 348 (east) and 347 (west) wide, from 160 and 320, the widest a side
   doorway may be in its stretch (32 clear of the path points); the east alcove's front floor at -1820 (the tunnel's
   floor at its higher jamb), level.
7. `mover:button50` answers its warning with `floor_height: -1565` (it had been built standing 121 above the
   shelf's top since the rule changed); the migration warning went with the last whole-ceiling levels it named.

### New features: which worked, which were refused

Worked: `monsters[]` and `items[]`; `kills` with `monster`; a condition `item` with `kills`; `once` on timer events;
effects `summon`, `teleport` (followed by the game) and `lua` with an `if`; a mover passing into the ceiling (gate's
upper half) and into its wall (five buttons); `parts` (teeth, with their own `top_surface`); a mover as the click
source of switch and teleport presets; `from_wall`/`to_wall` on side doorways and plain openings; `height: full`
under `ceiling_points` on both sides of a mouth; `ceiling_lines`; a trapped chest with fixed items. `trim_to_wall`
worked while one side was levels, then had nothing to do. Not used: `lights_on`/`lights_off` (the map has no light
events), `solid`/`visible`, ladders, sounds, `secret`, `thickness`/`bottom_surface`, `floor_surfaces`.

Refused or not as wanted (repros under `output/studio_cal/mm6_hive/repro/`, `openyamm-studio/build/oymap validate
<folder> --assets assets_dev`):

1. A decoration as an event's source (`keg_decoration_source/`), message above.
2. A raking sill in a tunnel's side doorway: `rooms.yml: openings[0]: the uneven floor of room:s12_alcove_e is not
   level along this opening: it runs from -1841 to -1816 between the opening's sides ... An opening stands on a
   level sill` (west: -1816 to -1775). The original's alcove floors rise straight out of the tunnel's floor; the
   alcoves' fronts are level here (east -1820, west -1778).
3. A side doorway the alcove's whole width: `the doorway reaches from 2 to 404 along a side 412 long, between two
   points of the tunnel's path: keep it 32 clear of both` (as documented): 348 and 347 where the original's are 404
   and 384.
4. A ceiling by points rising more than 4 per unit: two ring points of the west hall's dome, 8 and 28 inside its north
   wall, left out (`the ceiling of room:s38_west_hall rises 94.23 for each unit of run ...`); the original's dome
   stands almost upright there.

### Compromises undone and left

Undone: the gate sinking whole (now two combs, the upper into the ceiling); the five buttons as flat switches; the
mouths' rectangles in two parts; the chest room's doorway 224 wide (and on the wrong wall); the alcoves' doorways 160
and 320; the flush as two events; the placeholders for the Reactor, the Queen and the scroll; the key granted from
outside; the east hall's recess as a room of its own. Left (each in "Gaps"): the keg room unreached, the north-west
loop pad's lip (a platform in a tunnel), sections that change along a tunnel, fans, the junction at a bend
(`s13_j49`), the north-east run as two tunnels (28 points), one picture over both leaves of the double door, the
alcoves' level fronts.

### Pictures

`output/studio_cal/mm6_hive/ingame_r5/diff/` (16 pairs, `shots_r5.yml`): mean edge agreement 0.77, blurred
difference 0.045. The Reactor on its dais 0.97 and the Queen 0.96 (the same creatures at the same places in both),
the lock with the scroll 0.84, the shut gate 0.72 (one hvwl6 wall in both, the texture half a tile off), the flush
button 0.63, the other buttons 0.57 to 0.58 before their walls got the original's panels. Pairs retaken after the
domes and panels: `ingame_r5b/diff/` (8 pairs, `shots_r5b.yml`): mean 0.84, blurred difference 0.032; the west
mouth 0.94 (0.93 before), the east mouth 0.90, the halls' domes 0.85 and 0.88, the closet button 0.97 (0.58), the
south cell's button 0.70 (0.58), the hatch button 0.77 (0.57), the chest room's doorway 0.70. A small spike shows at
the west mouth's left shoulder seen from the west hall (where the great hall's corner point at -1248 meets the
arch); not traced. Looked at: the reactor and Queen pairs are alike to the pixel;
before the north hall's dome went to points, the west mouth showed a band of wall between the arch and the great
hall's flat dome end that the original does not have (its dome droops along the arch), which is why that dome was
redone.

### Gaps still open, most harmful first

1. **The keg room** (sector 73): its doorway stands above the tunnel's top and the original reaches it by a ramp
   face in the tunnel's side; not reached, so its keg and its pad do nothing. Field: a side bay lifting the tunnel's
   ceiling over a stretch of its side with a doorway `ramp`; and `source: deco:...` for the keg's event.
2. **A section that changes along a tunnel** (the deep tunnel's wide first 1900, sectors 26, 27, 31 taller and
   leaning). Field: `sections` per stretch.
3. **Fans** (four of compare's points without a floor: 11, 18, 33, 70). Field: `start|end` with `floor_width`, at
   an angle.
4. **A raking sill in a tunnel's side doorway, and a doorway its room's whole width** (the alcoves). Field: let a side
   doorway's sill follow the side room's floor points, and let the jambs come within the 32 when the side room is as
   wide as the stretch.
5. **Leave and damage hooks** (the supplement's 65012 for other ways out, 65010). Field: `trigger: leave`; a
   monster's damage rule.
6. **One-sided doors** (4, 5, 10, 11, 12; event 21). Field: `side` on a door event.
7. A junction at a bend (`s13_j49`), a platform in a tunnel (the north-west pad's lip), a path of more than 24
   points (north-east run), a picture per leaf of a two-leaf door, a part's underside surface apart from its sides
   (the gate teeth's hvflord undersides), the lean of the halls' lower walls (the mouths' sides).

### Tool defects

1. `oymap solve` takes a `kills` condition as already met: a timer event with `kills` on a monster in a room nothing
   reaches still carries the party into a closed room at step 1
   (`openyamm-studio/build/oymap solve output/studio_cal/mm6_hive/repro/kills_teleport_solve --assets assets_dev`,
   from a copy). In the Hive this puts the reactor's kill flow before the double door: `solve` now reports
   1, 17 (with quest bit 1204 and item 2164), 43, 22 (item 2190), 14, 1 sectors; with the kill flow's carry taken out
   of a copy it is 1, 1 (quest bit 1204), 41 (the double door), 17, 3, 7, 13 (item 2190), 15, round four's order and
   the original's. `solve` also still lists item 2190 as needed at the key door's step though chest 2 now holds it
   (it names no outside source for it any more).
2. `oymap solve` and `audit` still count the keg room unreached (true in the original too).
3. The build warns "is in a wall without thickness and leaves wall round it ... move the rooms at least 16 apart"
   for three joints where the original's rooms meet on one plane (`open:s4_hall__s39_corridor`,
   `open:s80_steps__s79_reactor`, `open:s80_steps_top__s80_steps`); moving them apart would add a wall the original
   does not have, so they are left.
4. `ids.lock.yml` keeps `mover:gate`, `door:d51`, `door:d52`, `evt:flush_hit` and the variable `flush_hit` after
   their objects are gone (round three's defect 4).
5. Scenario runner: a `play_lua` `wait()` does not carry out a move of the party that a timer event asked for within
   the map; `advance_runtime: {follow_map_move: true}` does (the playtest says so where it matters). And
   `mapvar(name)` reads only named map variables (`evt.GetMapVar`), not a wiring variable by number; the checks use
   `assert: {state_dump_map_var: ...}`.
6. A Lua step in `effects` cannot name a wiring variable: the flush's damage test reads `MapVar(8)` by its number in
   `ids.lock.yml`.

### Unsure in the original

- The Reactor is not hostile to the party by its tables in either map (the walks' sweep leaves it); in the game the
  supplement's damage hook and its kill flow suppose the party attacks it.
- Chest record 0 (trapped, two random items) is opened by no event; read as unused.

## Round six (2026-11-13): what the player sees at every interactive thing

Brief: the lead's task message of 2026-11-13 (after the user's walk through Gharik's Forge; REBUILD_PROCEDURE.md "What
the measure does not see"). The project as round five left it is in `output/studio_cal/mm6_hive/r6_backup/`. Every
edit is a recorded one-off script in `output/studio_cal/mm6_hive/tools_r6/` with every number the original's (export
`orig_r6.json`, door and event faces listed by `things.py` into `things_orig.txt`): `edit_things_r6.py` (doors, chests,
exits, Queen's alcove, bay panel, entry and lock walls, chest 3's plinth, events), `edit_lock_r6.py` (the lock's corner
panels), `edit_playtest_r6.py`; small edits inline (copies before them: `rooms_before_ring.yml`, `rooms_before_porch.yml`,
`rooms_before_plinths.yml`). Helpers: `round.sh`, `play.sh`, `final4.sh`, `look.py` (same-camera pictures of both maps
with console lines before a shot, so a thing is seen before and after use), `stack.py`, `coplanar.py` (faces in one
plane over each other in an export), `things.py`.

### Scores

| | `oymap compare` | distances | textures | rooms |
|---|---|---|---|---|
| start of round six | 97.2 % | 97.8 % | 96.8 % | 99 |
| doors fold, chests, exits, alcove, bay panel, entry and lock walls, events | 97.3 % | 97.9 % | 97.0 % | 100 |
| the lock's corner panels; the outer ring's ceilings sloping by points | 97.4 % | 97.9 % | 97.4 % | 100 |
| the porch before the north doorway (two columns and two beams of d5colum/d5trimA) | 97.5 % | 97.9 % | 97.5 % | 100 |
| chest plinths, the lower passage's walls, the Queen's gate as thick as its wall (end) | **97.7 %** | **98.1 %** | **97.6 %** | **100** |

Per sector, start to end: 79 (reactor) 0.983 to 0.987 (8.6 to 6.6 points lost; mean ceiling difference 20.7 to 1.9),
4 (great chamber) 0.988 to 0.994, 1 (lock) 0.948 to 1.0 (textures 0.83 to 1.0), 77 (Queen) 0.937 to 0.996. Still worst:
79, 35 (north hall, 3.6), 34 (north-west cave, 2.7), 70, 11, 33, 18 (tunnel fans, as round five). `compare.py`: 22 in,
9 near, 4 out. Rooms reached: 99 of 100 (the keg room, as the original). `oymap solve`: 1, 1 (quest bit 1204), 41, 27,
10, 3 (item 2190), 16; the click doors now open from their own side only, so the crossing's north door and the
gallery door come with the doors behind them (see tool defect 1).

No wrong shape that measures better: the outer ring's ceilings are the original's planes (outer edge -976, ring line
-720, faces 3559 to 3586), the porch is faces 1562 to 1576, the alcove faces 3369 to 3380, the plinths faces 2940 to
2942, 2972 to 2974, 3098, 3157, 3158.

**Playtest** (`playtest.yml`, 296 steps, was 275): **passes four runs of four** (`output/studio_cal/mm6_hive/run/
play_r6_1..4.log`). New: door 5 used with the use key from the great chamber (event 21, the leaf stays shut) and, after a
walk up the north-west tunnel, from its tunnel side (opens); door 11 from the crossing by the use key (event 21); the
kill flow's doors waited for instead of a fixed four seconds (the one failure of the round: the ring wall still
"opening" at the check); after the final exit, quest bit 784 set and the Ritual taken (the leave event's good ending).
Packs emptied before every chest and `clear_hostiles` on the walks, as round five.

### What changed

1. **Doors take the original's form.** Every door record of the original moves only the leaf's free edge, 250 of its
   256 (door 1's moving vertices lie at z 1 only, door 45's at x 449 only): every door is `fold: true, travel: 250`
   (door 30: its default). Round five's leaves slid whole into the wall and, opened, lay in the plane of the wall
   face above or beside the doorway: the door picture showed over the wall over every open door
   (`ingame_r6/start/diff/04-entry-door-open.png`, `08-double-door-open.png`, `15-door5-open.png`); gone. The double door
   (45, 46) has `pictures` with the whole hvdord on each leaf. Leaves with a wall texture (doors 4, 8, 10, 12, 30) are
   `tile: true` (round five stretched hvwl1a over the leaf at twice its size: `46-crossing-door10-back.png`). Door 30
   (the Queen's gate) is 128 thick, the whole wall, as the original's block.
2. **One-sided doors by `side`** (the original's event faces, `things_orig.txt`): door 4 (corridor side, face 2176),
   5 (tunnel side; event 21 from the chamber, face 2184), 6 (east hall side; from the passage the face runs event 31,
   the south cell's switch: built as `evt:door6_passage`), 8 (ramp side, 2238), 10 (tunnel, 1645), 11 (north, 1584;
   event 21 from the crossing, 1593), 12 (tunnel, 1646), 28 (lower passage, 2215), 36 (event 21 from the passage,
   1728; event 33 from the cell, 1715: `evt:door36_cell` toggles door 36 and the closet button), 42 (cave, 3129). The
   variables `north_way` and `stair_way` that stood in for this are gone. Checked in the game: door 11 from the
   crossing runs event 21 and stays shut, door 12 from the tunnel opens, door 11 from the north opens
   (`run/t_sides.yml`).
3. **Chests** at the original's size and place (96 by 64 by 64, chest 2 a 64 cube; round five 72 by 48 by 44), sides
   ch1frntB, ends ch1side, tops Ch1topB (chest 4 Ch1tpBv, facing north), chest 2 ch2side/ch2frnt/ch2top. Chest 3 stands
   on its niche's plinth (32, hvtrim1), chest 2 on its dais (16, hvtrim4), chest 5 on its plinth in the cave (55, top
   hvtrim1): round five had all three on the floor.
4. **Exits**: the south exit is face 3000 (hvwl1spb 256 square; round five a door picture 192 by 256) on an hvtrim1 wall;
   the final exit is face 3378 (hvflorG 256 square) at the end of the Queen's low alcove (512 by 256, 256 high, hvwl6),
   now a room of its own (`room:s77_alcove`); round five had a door picture on the chamber's side wall and the alcove
   at the chamber's full height.
5. **Walls round the things**: door 1's hvtrim4 frame on the entry side; the lock's carved corner panels (HVWL2LE/RE,
   128 beside every corner) and its HVWL3 band; the reactor bay's panel (event 30's face, SWtrPnl in an SWhz2dk frame);
   the lower passage under the floor panel (HVWL1SPB below, HVWL2A to the panel, as faces 2214 to 2221).
6. **Events** (below): the keg (event 23 on `deco:keg`), event 22, chest 2's map variable 12, the leave event 65012, the
   flush and keg handlers in the original's order, titles as the original's (events 33, 38, 39 have none).
7. **Score work**: the outer ring's ceilings by points; the porch of two columns and two beams before the north doorway.

### Events, the original's against the rebuild's

`oymap flow` of both (`output/studio_cal/mm6_hive/flow_orig_r6.txt`, `flow_r6.txt`): of the original's 46 own handlers
**44 the same, 1 differs, 1 missing** (round five: 35, 7, 4).

- Same since this round: 4, 5, 10, 11, 12 and 21 (one-sided doors and "The Door Won't Budge"), 22 (the cell floor
  clears a variable nothing reads), 23 (the keg: the line, then 20 hit points; its room is not reached in either map),
  42 (sets map variable 12), 54 (text, then the damage unless protected, then the variables), 60 and 65012 (the exit
  opens with quest bit 1226; leaving after the reactor's death is the good ending with the Queen dead and the Ritual
  in the packs, else the bad ending: `evt:leave_ending`), titles of 33, 38, 39. Also built: the passage face of door 6
  (event 31) and the cell face of door 36 (event 33).
- Differs: 65011, the kill flow, runs at the next two-second tick, without the random 120 of the carry.
- Missing: 65010 (a physical blow to the reactor does 2 to 40): no damage hook.
- Not built, as data slips of the original: the undersides of door 36's leaf (event 6) and door 6's leaf (event 31).
  Events 30 and 62 have faces and no handler in either map.

### What the player sees: differences per interactive thing

Pictures of both maps from the same camera before and after use: `output/studio_cal/mm6_hive/ingame_r6/start/` (round
five's build, 85 pairs, mean edge agreement 0.687) and `ingame_r6/end/` (this round's, 92 pairs, 0.715); cameras and
console lines in `tools_r6/things_spec3.yml`. Each sheet: original, rebuild, difference.

| Thing | Original | Rebuild now | State |
|---|---|---|---|
| Entry door (door 1) | hvdord leaf folding up, hvtrim4 frame, HVWL3SPA back between HVWL2RE/LE | the same (`01`, `03`, `04`: 0.82, 0.96, 0.77) | fixed (frame, back panels, fold); jambs: studio gap a |
| South exit (event 48) | HVWL1SPB 256 on an hvtrim1 wall with hexagonal corners | the same face and wall; the corners square (`02`: 0.84) | fixed; corners: gap c |
| Double door (45, 46) | two leaves, a whole hvdord on each, folding to the jambs | the same (`06`, `07`, `08`: 0.97, 0.88, 0.86) | fixed; jambs gap a |
| Door 4 | HVDORC to the corridor, HVWL2A to the gallery, opens from the corridor | the same (`09` to `11`) | fixed (side) |
| Hatch cover (43) and its button (41) | slats, toggled | alike to the pixel, shut, open and shut again (`12`, `35`, `37`: 0.99) | as round five |
| Door 5 | HVDORF both faces; tunnel side opens, chamber side "Won't Budge" | the same (`13` to `16`) | fixed (side, fold) |
| Door 13, 2, 3, 7, 9, 14 | leaf folding up; trim frames (hvtrim4 round door 13, hvtrim1 round door 14) | leaves alike; frames and jambs of 13 and 14 missing (`18`, `57`) | frames by panels possible, not done; jambs gap a |
| Buttons 16, 31, 35, 37, 41 and floor button 50 | small blocks pushed 8 to 10 into the wall, toggling | the same blocks and travel; the press is too small to see from where a player stands in either map (`21`, `23`, `27` to `29`, `33`, `36`, `38`, `45` to `48`, `62`, `65`, `72`, `73`) | as round five |
| Door 32 (opened from the south cell, and from door 6's passage face) | | passage walls HVCeilB in the original, hvwl5a here (`24`) | texture of the passage, not of the door |
| Door 36 | Won't Budge from the passage, toggles from the cell | the same (`42`, `44`, `47`) | fixed (side) |
| Doors 10, 11, 12 at the crossing | back faces HVWL1A at 1:1, door 11 "Won't Budge" from the crossing | the same (`49` to `54`: 0.68 from 0.51) | fixed (tile, side); the crossing's hvtrim1 jamb strips: gap a |
| Door 6 (key) | HVDORG, opens with the key from the hall; its passage face is the south cell's switch | the same | fixed |
| Door 8, 28, 42 | one-sided | the same | fixed (side) |
| Floor panel (38) and button 37 | panel slides away showing the lower passage | slides; the lower passage's walls now HVWL1SPB/HVWL2A (`67`: 0.85; `ingame_r6/panel/`) | fixed (walls) |
| Chests 1, 3, 4, 5 | 96 by 64 by 64, a middle picture with end strips on front and top | right size and place, chest 3 and 5 on their plinths; front and top one tiled picture | **waits on the studio** (end-middle-end) |
| Chest 2 | 64 cube ch2frnt/ch2side/ch2top on a 16-high dais | the same box on the dais (`74`, `75`: 0.91, 0.75); the lid picture laid from the world's grid, half a picture off | lid: gap d |
| Keg (23) | smlbarel decoration, " +20 Hit Points" | the same, now wired (`80`); its room unreached in both | fixed (event) |
| Reactor and Queen | on the dais, in the chamber | alike (`81`: 0.99) | as round five |
| Ring wall (53), north gate (51, 52) | stand, sink and rise after the kill | the same (`82`, `83`, `89`); the gate's hvwl6 half a tile off (`83`: 0.40) | texture offset on a mover: gap e |
| Queen's gate (30) | 128-thick block of hvwl6, its top SWhz3, ends swhor1dk | 128 thick, hvwl6 at 1:1 (`85`: 0.42, the offset); top and ends hvwl6 | ends and top of a leaf: gap f |
| Bay panel (event 30, no handler) | SWtrPnl 32 deep in a bevelled SWhz2dk frame | flat panels on the back wall (`86`, `87`) | recess: gap b |
| Final exit (60) | hvflorG at the end of a low hvwl6 alcove | the same (`91`: 0.65 from 0.48) | fixed |

The studio's five being fixed now, where this map has them:
- **Lever handles that move**: none (no lever in the Hive; its switches are buttons, built as movers since round five).
- **A toggling switch's picture**: none (no event changes a texture).
- **Chest faces laid end-middle-end**: chests 1, 3, 4, 5. Faces: chest 1 (event 41) ch1frntB 2927 and Ch1topB 2928 in
  the middle (x 4576..4640), ends ch1frLE 2983/2984 and ch1bkRE 2985/2986 (16 each, x 4560..4576 and 4640..4656, front
  +y at 10176, top -1466), ch1side 2930/2931 at x 4560 and 4656; chest 3 (43) Ch1topB 2957, ch1frntB 2958, ch1topLE
  2968, ch1frLE 2969, Ch1topRE 2970, ch1frRE 2971 (x 8471..8567, front -y at 7561), ch1side 2977/2978; chest 4 (44)
  turned: front -x at x -2875, y 4134..4230, Ch1tpBv 2960, ch1frntB 2961, ch1tpLEv 2979, ch1frLE 2980, Ch1tpREv 2981,
  ch1frRE 2982, ch1side 2959; chest 5 (45) Ch1topB 3148, ch1frntB 3149, ch1frLE 3150/3151, ch1frRE 3152/3153, ch1side
  3154/3155 (x -6936..-6840, front -y at 14428). Only the middle faces carry the event in chests 1, 3 and 5; all seven
  faces in chest 4. Chest 2 has no end strips.
- **Things over moving parts**: none (nothing stands on the hatch, the floor panel or the ring).
- **Faces in one plane over each other**: two water pads in cell passages lie over the side tunnel's sill strip
  (`tools_r6/coplanar.py` on the round's start build: faces 3209/3271 near (5824, 5881, -1489) and 3210/3280 near
  (7792, 5881, -1319), overlaps 1920 and 2048); in the game no flicker shows from where a player stands
  (`end/diff/31-pad-sill-cell51.png`, `43-pad-sill-cell45.png`), but the strip in front of each pad differs from the
  original's sill. The north gate's teeth lie inside the other half at the shut pose, as in the original's own records
  (doors 51, 52: upper teeth down to -1744, lower body up to -1616); no flicker in the pictures.

### Gaps (studio), most visible first

a. **A doorway's reveal surface.** The original lines the jambs and the head of its doorways with trim: door 1
   hvtrim1 (faces 3010, 3011), door 13 hvtrim1 (2449, 2451), door 11's crossing hvtrim1 (1585, 1586, 1591, 1592),
   doors 5, 7, 14 likewise; the rebuild's reveals take the wall's texture. Field: `openings[].jamb_surface`
   (and `head_surface`).
b. **A recess in a wall** (the bay's panel: SWtrPnl 3433 128 by 256 at y 26438, SWhz2dk bevel 3434 to 3437 32 deep,
   HVWL1A slopes 3438 to 3441, 3604 to 3607 round it): flat panels here. Field: `walls[].niches` with a bevel.
c. **A box room with a cross-section** (the entry, sector 76: the end walls hexagonal, corners at (160, y, 160) and (736,
   y, 160), faces 2998 to 3007): square here. Field: `section` on an outline room.
d. **A chest's lid laid from the chest's corner** (chest 2's ch2top shows half a picture; part of the end-middle-end work).
e. **Texture offset on movers and fold leaves**: the north gate's and the Queen's gate's hvwl6 half a tile off the
   original's (faces 3458, 3473 to 3480 carry u from the world x); a mover's or leaf's texture origin is not said.
f. **A leaf's top, ends and underside**: door 30's top SWhz3 (3376) and ends swhor1dk (3368, 3374); the folded stubs'
   undersides OFlrL32 (doors 3, 14: 1794, 2457), hvtrim4 (door 13: 2433), hvtrim1 (the rest). Field:
   `doors[].edge_surface`.
g. Still from round five: the keg room unreached (a side bay over a tunnel with a ramp), sections that change along a
   tunnel, fans, a raking sill, the damage hook (65010), a junction at a bend, the north-west pad's lip.

Refused this round: nothing (every new word validated at its first try: `fold`, `pictures`, `tile`, `side`, a
decoration as a source, `trigger: leave`, `else_effects` with Lua, `ceiling_points` on a C-shaped room, hanging
platforms with `base` and `bottom_surface`, chests with `end_surface`, `top_surface`, `facing`).

### Tool defects

1. `oymap solve devdocs/map_studio/briefs/mm6_hive/L4 --assets assets_dev`: a door event with `side` is listed as used
   from the sector its leaf is filed in, not from its side: "event 9 (Door) in sector 25: door 4 open" (event 9 is
   `side: room:s19_tunnel`; sector 25 is the crossing, where the game's use key finds no target on that face), "event 8
   (Door) in sector 25: door 3 open" (side `room:s40_a`). The order `solve` reports may open a door from its dead side.
2. Scenario runner: `press_interact` cannot expect "no target" (it fails with "did not pick a target"), so a one-sided
   door's dead face cannot be asserted directly; the playtest checks the leaf stays shut after the other side's text.
3. `calibration/ingame_compare.py` takes no console lines per shot, so nothing is seen after use; and a shot without a
   floor on one side is skipped there only, so every later `NN-` name differs between `original/` and `rebuilt/` (the
   keg in `ingame_r6/start/`: renumbered by hand). `tools_r6/look.py` does the first; the second stands.
4. From round five, still: `ids.lock.yml` writes from `oymap build --out` and `oymap export <project>` into the project.

### Pictures

Best: `ingame_r6/end/diff/06-double-door-shut.png` (0.97), `03-entry-door-back.png` (0.96), `12-hatch-shut.png` (0.99),
`67-lower-passage.png` (0.85). Worst: `83-gate-shut.png` (0.40, texture offset), `85-queen-gate.png` (0.42, offset),
`79-chest5-above.png` (the cave's terraced roof cuts the original's view), `87-bay-panel-near.png` (flat panel).
