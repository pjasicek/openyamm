# Abandoned Temple (MM8 `d05.blv`) rebuilt as a Map Studio project: notes

Project: this folder (`project.yml`, `rooms.yml`, `objects.yml`, `wiring.yml`, `ids.lock.yml`, `playtest.yml`).
Map id `calib_mm8_d05`, map table row 9711, `reference: d05.blv`. Drawn in the original's frame.
The four project files are written by a generator, `output/studio_cal/mm8_d05/gen.py` (rooms and objects as measured
numbers, the maze derived from the original's door records), then `oymap fmt`; `mkplay.py` beside it writes
`playtest.yml`, `play.sh` builds, installs and plays. That held for round one only: since round two (last section)
the files are edited by hand and the generator must not be run.
Scratch data, the comparison reports of every round and the in-game pictures are in `output/studio_cal/mm8_d05/`.

## Where it stands (2026-11-12, six rounds)

| Round | What changed | `oymap compare` score | distances | textures |
|---|---|---|---|---|
| 1 | first complete shell, objects and wiring | 70.3 % | 69.1 % | 79.0 % |
| 2 | hall 8 as one tall room, walkway as a solid level; wall bands; cave dome | 68.7 % | 66.6 % | 79.7 % |
| 3 | lake drawn shallow (so the party can leave it) | 68.2 % | 65.9 % | 79.7 % |
| 4 | lake at its depth with flights out; causeway; door leaves; panels dark | 69.0 % | 66.6 % | 80.7 % |
| 5 | walkway as a hanging slab; piers at the doors; lake edges | 70.6 % | 68.5 % | 81.5 % |
| 6 (last) | maze doors as deep as their doorways (seen in the in-game pairs) | **71.7 %** | 69.9 % | 81.8 % |

841 points of the original, 21 without a floor in the rebuild, 6 of the rebuild's 817 without one in the original.
Round 2 lowered the score on purpose: round 1 had a solid floor right across hall 8, which looks like the original
and plays wrongly (see gap 3).

- `compare.py`: first round `counted (structure, scale, play): 18 in, 2 near, 15 out`, last `17 in, 3 near, 15 out`.
  Nearly all "out" lines are counts (93 rooms against 31 sectors, 94 openings against 30 portals): every maze
  closet, doorway passage and stair flight is a room here.
- Rooms reached: 93 of 93 with every door out of the way, 16 as the doors start (`oymap audit --reach`); `oymap solve`
  opens it in 13 steps with nothing unreached. The original: 30 of 31 (sector 21, the killing pit, never), 6 steps.
  The order is the same (hall of stones, closets and stair, hall of the false floor, retracting floor, great hall,
  maze from its entry door to the cave); the rebuild has more steps because the four alcove slabs and the stair
  buttons are clicked here and run by the floor in the original.
- Playtest: **passes**, 193 steps (`playtest.yml`): down the tower, stairwell, tunnel; a stone sinks; the four
  buttons refuse out of order and raise the steps in order; both closets and chests; the long stair; a fall off the
  walkway and the way back by the return stair and door 6; the walkway end to end; the eight panels and the far
  door (refused before, open after); the great hall's chest; the back stair to the back-door chamber; the maze by
  the six right buttons, one wrong button (closet opens, the right door shuts); the causeway and the niche door.
  Not played: the two exits (the walk ends in the cave), the four corner chests of hall 8 (no way to them on foot
  in the original either).
- In-game pairs (`ingame_compare.py`, 20 pairs, rounds 3 and 5; sheets in `output/studio_cal/mm8_d05/ingame_final/diff`):
  mean edge agreement 0.53, then 0.54. Alike: retracting-floor room 0.99, pyramid floor 0.98 (dark), great hall
  0.97, maze hall 0.89, trap hall 0.85. Unlike: hall 8 from its door 0.66 (the false floor is missing: a pit with
  a slab across it), the cave 0.71, views from inside door passages (the original's camera stands inside the door),
  the pyramid from the tower's top. The pairs found what round 6 fixed: the original's maze doors are plugs as deep
  as their doorways with the leaf flush in the hall's wall; the rebuild's stood 64 thick in the middle of the wall.

## What the map is (the original, as read)

33 sectors (one empty, one a single stray face). The 112 door records are: 49 real doors (1, 3 to 6, 52 to 93,
108, 109, 114: all but door 6 are slabs whose bottom edge rises into the lintel; 6 is a block that sinks into the
floor), 46 buttons (10 to 51 in the maze, 100/102/104/106 in the trap hall: a 32-unit block that moves 16 or 48 into
the wall), 10 moving floors (94 to 99 the sinking stones, 101/103/105/107 the four pairs of rising steps), one
record of four slabs (2, the alcoves of the trap hall), four floor plates that draw back into the walls (110 to
113), and one secret panel (115). Door records 7, 8 and 9 are named by handlers and do not exist.

1. Sectors 14, 15: a hall 4608 square under a pyramid roof, with a free-standing stair tower; the party arrives on
   its top (2464) and the front exit is there. A stairwell in the floor leads into
2. sectors 2, 3: a rock tunnel under the hall, falling 560 to 160, to
3. sector 1: the hall of the sinking stones (six stones from a dais to the north landing; fall, and four buttons in
   four alcoves raise a stair), then sector 5 (two chest closets), 6 (long stair), 7,
4. sector 8: the hall of the false floor (a winding solid walkway hidden in a floor that is not there), with
   sector 9 the way back up from below; 10 (slanting stair),
5. sectors 11, 21: the room whose floor draws back over a killing pit until eight panels are put out,
6. sectors 12, 13 (corridors), 16, 17 (great hall: four poison-spraying heads, a fire-bolt stand with a quest
   book, a secret chest niche), 19, 20 (back stair and back exit, above the great hall),
7. sectors 22 to 32: the button maze (18 halls, 42 buttons, 42 doors, 23 of them closets that summon a serpent man),
8. sector 18: the lake cave with a causeway, a quest book and a niche behind a slab.

## Gaps of the vocabulary, most harmful first

1. **A sloped ceiling (a pyramid roof).** Sectors 14 and 15 (289 of the comparison's 841 points; they score 0.53
   and 0.54, distances 0.37) and sector 20: the roof rises from the floor line at all four walls to a flat top 1488
   higher. Did: a flat ceiling at the top's height (the flat height makes no difference to the score: 2000, 2200 and
   2432 give 0.37 to 0.39). `ceiling_levels` cannot stand in: they may not touch a wall, each other or nest. Would
   have said it: `ceiling: {slope: [{toward: <wall>, from: 944, to: 2432, run: 1664}, ...]}`, or a room-level
   `roof: pyramid` with a rise and a flat top. The same word would give the ceilings that follow a stair (sectors
   6, 9, 19: `mean_ceiling_difference` 128 to 179) and the cave's dome (sector 18).
2. **A floor opening onto a room below.** The stairwell of the pyramid hall (768 by 256, twelve steps down from 944
   to 560 into the tunnel that runs back under the hall's floor). Did: the hall is three rooms (west, north-east,
   south-east) with the stair a walled room between the two east ones and a strip of floor (`room:pyr_mid`) east of
   it; the stairwell has walls up to the roof on both long sides where the original has none. Would have said it:
   a `levels` entry lower than the floor that an opening can leave (`openings.from: room:x, level: n`), or a room
   flag `open_above: room:pyramid`. (A sunken level with a flight builds the well itself correctly; nothing can then
   leave it.)
3. **A floor that is seen and is not solid.** Hall 8: a floor of t65b03 at the doors' height covers the whole hall;
   only a winding walkway and four corner squares are solid. Did: one tall room, the walkway as a hanging slab
   (`platforms` with `base`), the false floor left out, so the trap is plain to see and the picture from the door
   is wrong. Would have said it: `levels`/`platforms` with `solid: false` (and `visible`), or a `false_floors` list.
4. **Events run by the floor, by entering or leaving the map, or by a timer.** 86 faces of the original run events
   when stepped on: the six stones sink (506 to 511) and reset (512), the alcove slabs open (12), the heads spray
   poison (111 to 114), the stand throws fire bolts (115), the secret panel opens (453), the falls are counted (451,
   452), the pit kills (101). Events 1 and 2 run on entering (an NPC speaks; the floor room resets), 6 and 10 on
   leaving (quest bits), 110 on a timer. Did: stones and slabs are clicked; everything else is a placeholder. Would
   have said it: wiring `trigger: {step_on: <level, lift, platform or a rectangle of a room>}`, `trigger: enter`,
   `trigger: leave`, `trigger: {every_minutes: 2.5}`, and an effect `cast: {spell, skill, mastery, from, to}`.
5. **A floor that draws back / a mover that is neither a door in a doorway nor a lift.** Door records 110 to 113
   (sector 11): four plates sliding 639 sideways into the walls at 10 units a second, stopped in mid-travel by
   `StopDoor`. Did: a solid floor at the plates' height, the funnel and pit not built, the eight panels as
   once-only switches that unlock the far door. Would have said it: a `movers` list (an outline or block of a room,
   a direction, a travel, two speeds, a start state) and wiring `stops: [...]`.
6. **A platform above a platform, and a stair slab one can stand under.** The tower's upper turn (three ramps from
   the platform at 1920 round to a platform at 2432 directly above it; the arrival and the front exit are up
   there). Did: the tower ends at 1920, the party arrives 544 lower, the exit is on the hall's south wall. `levels`
   are solid to the floor, so the comparison also finds no floor under the landings (4 points). Would have said it:
   `platforms` that may overlap in plan at different `base` heights and be named as a flight's `from`/`to`
   (`from: {platform: id}`), and flights with `open_below: true`.
7. **Two openings one above the other in one wall.** Hall 8's west wall: the door at -352 and, straight below it,
   the corridor at -1056. Refused as "overlap". Did: an invented jog room (`room:corr9_jog`) that moves the lower
   opening 272 north. Would have said it: nothing new; the check should compare heights.
8. **Which wall an opening is in.** A stair room standing in a slot of another room faces it on three sides; the
   build takes a long side ("the opening is in a wall the floor rises along") and there is no way to name the wall
   (tried: both orders of `from`/`to`, a different first corner). This, with gap 2, forced the hall into three
   rooms. Would have said it: `openings.wall` (an edge number of the `from` room).
9. **One panel on a wall; a door leaf of two textures.** Every maze doorway has a marker panel 128 wide beside it
   (t65a06 left doors, t65a07 right doors), every button pair a t65a12 plate, the walls alternate t65a01, t65a01a,
   t65a01b; door leaves are t65a05bl and t65a05br side by side. These are the largest texture misses (t65a06 621
   rays, t65a07 553, t65a05br 371, t65a12 228 of the last report); maze sectors agree on textures 0.51 to 0.67. Did:
   t65a01 everywhere, t65a05bl twice on a leaf. Would have said it: `walls: [{wall, from, length, surface}]` or a
   `sequence` of surfaces along a wall; `door.surface` as a list left to right.
10. **A sloped room that bends, a path that slopes, rough walls on a slope.** The tunnel (sectors 2, 3) is nine
    straight ramps cut by parallel lines and one level bend, because a sloped room must be convex with its two ends
    parallel and a `path` cannot slope. Would have said it: `path` with `floor_along: [560, 528, ...]`.
11. **Levels that touch each other, banks that slope.** The lake (sector 18): its bed slopes up to the shore all
    round and the causeway's sides drop into it. Did: upright sides, one flight of eight steps out of each half, a
    kerb 16 wide between causeway and water, the causeway 16 below the shore instead of 64 with a ramp at each
    end. Would have said it: `levels[].bank: <run>` (a sloped edge), levels sharing an edge.
12. **A platform or pedestal against a wall, more than 20 corners on a platform.** Hall 8's walkway must reach both
    doors: platforms must stand 32 clear of walls, so it stops 48 short and an invented solid pier (a level) joins
    it to each door; its outline is two platforms and thinned from 40 points to 23. The cave's book stand and the
    closets' pedestals (moved 16 off their walls) are the same case.
13. **Objects with no word:** an item lying in the map (three quest books), a fixed light that starts switched off
    (the eight panel lights: left out, 52 lights of 60), a lift with a base height or a turn (the stones sink to
    32, two are turned 27 degrees), a switch that goes back (`once` or nothing), a counter in a condition
    (`map_var >= n`; done with one variable per stage), an exit that is not on a room's wall (the front exit stands
    free on the tower), a secret door flush in a wall with a niche 20 deep behind it (door record 115).
14. **A step higher than 40.** Sector 10's six steps of 48 are eight of 36.

## Tool defects

- `oymap validate <L4>`: two openings at different heights in one wall are refused: "two openings in one wall of
  room:hall8 overlap or stand closer than 16 units" (replace `room:corr9_jog` by an opening `corr9` to `hall8`).
- `oymap validate`: an opening between a stair room and a room that faces it on three sides picks a side wall:
  "the opening is in a wall the floor rises along; put it in the wall at the low or the high end of the slope",
  though the high end is one of the facing pairs. No field names the wall.
- `oymap validate`: `levels` and `lifts` that touch the room's walls are accepted and build (trap hall, hall 8),
  `platforms` and `ceiling_levels` are refused; the schema's text says all must keep clear. One rule is wanted.
- `oymap validate`: a platform outline of 23 points passes the schema (at most 24) and is then refused with "a face
  of PLATFORM_hall8_4 has 23 corners (at most 20): the room has too many openings in its walls": wrong reason.
- `oymap validate`: a flight whose `from`/`to` lies exactly on a level's edge is judged to be on the other floor
  ("here 944 to 944"); it needs a point one unit inside and the message does not say so.
- `oymap validate`: an exit that does not fit its wall also reports "events[61]: the exit leads to , which is not in
  project.yml neighbours" (an empty name; the neighbour exists).
- `oymap audit <L4> --reach` and `oymap solve`: a gap of 33 units between a doorway and a hanging platform is not
  crossed (32 of 93 rooms reached) though the party walks over it in the game (the playtest passed in that state).
- `oymap compare d05.blv --world mm8 --with <L4>`: (a) faces that belong to door records are left out of the
  original, and in this map the side walls of every doorway passage are door faces, so points inside passages
  report "the original has nothing within 4096" (worst points (9472, -3328), (8960, 512), sectors 27, 29, 30);
  (b) the original is read in the pose stored in the BLV, not as the map starts: all doors open, the floor plates
  of sector 11 drawn back (the six points of sector 21 stand in the pit, score 0.03), while the game closes them on
  entering; (c) the false floor of sector 8 counts as geometry for the rays and not as floor for the points, so
  neither a solid floor nor none agrees.
- `oymap export d05.blv`: `counts.doors` says 200 (the map has 112) and the export holds no door records; they had
  to be read from `d05.scene.yml`.
- `oymap assets wtrtyl --assets assets_dev --kind texture`: no match, though `wtrtyl` is the lake's texture in this
  map and builds and draws when named.
- `calibration/compare.py`: counts rooms against sectors (93 against 31) and so marks 12 lines "out" for a rebuild
  that draws closets and doorways as rooms; `play.reached_at_start` likewise.
- `calibration/ingame_compare.py`: its default scratch root `output/studio_slice_root` and its run names
  (`studiocompareoriginal`, `studiocomparerebuilt`) are shared by every agent running at once (I gave `--root`);
  it leaves an `assets_editor_dev` folder beside the scratch root. In its pictures the original's doors that
  start shut are tinted red (corridor 5, hall 8's ceiling): not understood.
- `oymap build <L4>` writes `build/` into the brief folder, where git does not ignore it (removed at the end).

## Unsure of in the original

- Which pose is "closed". Taken from `game/indoor/IndoorGeometryUtils.cpp`: state 0 (Open) is the stored offsets,
  state 2 (Closed) is offsets plus direction times length. On that reading the stones start up, the steps start
  flat, the maze doors start shut. The static BLV vertices hold the open pose.
- Hall 8: how the four corner chests are reached (the corner squares touch no solid floor: jump or flight?), and
  what the third fall's `SetFacetBit(15, 2, 1)` shows the player.
- Sector 21: a floor at -1023 over the pit's real floor at -1152 with 36 small posts; read as an unseen killing
  floor. Whether the funnel (normal z 0.69) can be climbed was not tried.
- The retracting-floor room's sequence (events 62, 63, 64, 2, 110): which side of which door starts it.
- The secret niche of the great hall (door record 115 moves 127 of its 128) and the two copies of item 626.
- Sector 4 (one ceiling face) and the empty sector 0 were ignored.

## Round two (2026-11-12): the new vocabulary

From this round on the project files are edited by hand. The generator (`gen/gen.py`, `gen/mkplay.py`, and
`output/studio_cal/mm8_d05/play.sh`, which calls them) no longer describes the project: do not run it. The loop is
`output/studio_cal/mm8_d05/loop.sh` (fmt, validate, build, compare, reach, solve) and `play2.sh` (install, playtest).
Reports: `output/studio_cal/mm8_d05/compare_r2` (start), `compare_r2_end` (end); pictures `ingame_r2/diff`.

### Scores

`oymap compare` as it measures today (753 points; round one's 71.7 % was measured by the tool of that day over 841):

| | score | distances | textures | points without a floor in the rebuild |
|---|---|---|---|---|
| start of round two | 73.2 % | 69.5 % | 84.5 % | 8 |
| pyramid roof, the hall as one room, the stairwell as a hole in its floor | 86.1 % | 87.8 % | 85.3 % | 8 |
| stairwell one tread east and at its full width (384) | 86.3 % | 88.1 % | 85.3 % | 8 |
| ceilings that follow the four stair flights | 86.4 % | 88.2 % | 85.3 % | 8 |
| hall 8: corridor straight under the door (jog room gone), walkway to the walls (piers gone) | 86.8 % | 88.6 % | 85.7 % | 8 |
| hall 8: walkway 64 thick as measured | 86.9 % | 88.7 % | 85.8 % | 8 |
| back door chamber under a ridge roof (three rooms) | 87.1 % | 89.0 % | 85.8 % | 8 |
| cave dome, lake edge and tower textures, the tower's hanging box as beams | 87.5 % | 89.3 % | 86.3 % | 8 |
| the tower's top platform as a hanging slab | 88.2 % | 90.0 % | 86.5 % | 6 |
| the great hall's middle stand at its height (**end**) | **88.4 %** | 90.2 % | 86.7 % | 6 |

Sectors 14 and 15 (the pyramid hall, 289 points) went from 0.54 and 0.53 to 0.94 and 0.88; sector 8 from 0.82 to 0.86;
sector 20 from 0.71 to 0.96; sector 18 (cave) from 0.70 to 0.74. Mean ceiling difference 300.8 to 25.

- `compare.py`: `counted (structure, scale, play): 16 in, 3 near, 16 out` (round one ended 17 in, 3 near, 15 out; one
  exit fewer).
- Rooms reached: 91 of 91 with every door out of the way, 13 as the doors start (the hall is one room now instead of
  four); `oymap solve` opens it in the same 13 steps with nothing unreached.
- Playtest: **passes**, 192 steps (one waypoint fewer: the way back from under hall 8 no longer turns through the jog).
  No floor the walk uses moved; the start still stands at 1920 on the tower's top platform (now a hanging slab).
- In-game pairs (`shots_r2.yml`, 11 pairs, `ingame_r2/diff`): mean edge agreement 0.76. Pyramid from the floor 0.84 and
  0.84 (round one: "unlike"), tower top 0.83, hall 8 from below looking at the west wall with its two openings 0.89,
  hall 8 from the door 0.74 (the false floor is still missing), back door chamber 0.66 (roof right; monsters differ),
  stairwell 0.66 and 0.68, cave 0.70. Seen in them: the texture on every leaning ceiling side is stretched along the
  slope (see defects), and the cave's niche slab was a lit t65b02 panel in a rock wall (the original's is t6502b; fixed).

### What changed

- `room:pyramid` is one room 4608 square (`pyr_e_n`, `pyr_e_s`, `pyr_mid` gone) under
  `ceiling: 960, ceiling_levels: [{ceiling: 2432, top_outline: [...]}]`: the roof from the floor line to the flat top
  (x -3584 to -2432, y -1920 to -768; measured from ceiling faces 853 to 856, 904 to 907).
- `room:well` is a stair room under the hall's floor (`floor: 560, slope: {to: 944, toward: west, steps: 12},
  ceiling: 944`) opened by `open:pyr_well` (`in: floor`, with an outline). The walls up to the roof are gone. The room
  is drawn one tread east of the original's hole so that the treads stand where the original's do.
- `ceiling_slope` on `stair6`, `stair9a`, `stair9b`, `stair19a`, `stair19b` (measured from ceiling faces 351, 579, 660,
  1608, 1526).
- `room:corr9_jog` removed: `open:corr9_hall8` stands straight under `open:room7_hall8` in hall 8's west wall.
- Hall 8's walkway reaches both walls (platforms may stand against walls) and is 64 thick (underside -416, measured);
  the two invented piers are gone.
- `room:s20` is three rooms: the middle strip at 896 and `s20_s`, `s20_n` under `ceiling_slope` (the ridge roof).
- `room:cave`: one leaning roof from -384 at the walls to 200 (`top_scale: 0.4`) instead of two flat heights; lake
  sides t6502b; niche slab t6502b.
- The tower: the top platform west of the flight's head is a hanging slab (`platforms` with `base`), and the box that
  hangs from the roof round it (four walls, the upper platform's slab, three ramps and two landings) is drawn with ten
  `beams`, three of them raking. They are masonry to be seen, not a way up: see gap 1 below.
- The front exit (`exit:top`, `evt:exit_top`) is **gone**: `ph:front_exit` holds its place. Under the true roof the
  hall has no wall (16 high) to carry it; round one had it on the south wall under a flat ceiling, which was wrong too.
- The great hall's middle stand: a block 128 high with the turned block on it (256 in all, t65a13), as measured.

### The new features

Worked as described, first try:

- `ceiling_levels` without `outline`, with `top_outline` (pyramid) and with `top_scale` (cave, over a 16-point convex
  outline with two sunken levels and flights in the room).
- `ceiling_slope` on five stair rooms, parallel to the stairs or not; `height: full` openings at both ends followed.
- Two openings one above the other in one wall (hall 8, west): accepted with no `sill`, the higher room's floor lifts
  the upper one.
- Platforms against a room's walls, also hanging ones (`base`).
- Raking `beams` (`bottom_end`).
- `oymap export ... --world mm8 --assets assets_dev`: 112 door records at the top level (`doors`).
- The party start on a hanging platform is placed on its top (1920).
- `from_wall`/`to_wall`, `teleport` and `script` with a switch as source: not needed, not tried.

Did not work, or not as described (repros under `output/studio_cal/mm8_d05/repro/`, each `oymap validate <folder>
--assets assets_dev`):

1. **A stairwell of more than eight steps cannot be the "whole ceiling" hole** (`repro/stairwell_12_steps`):
   "openings: the hole of open:well cannot be cut out of the floor of room:hall: keep it clear of that room's walls,
   pillars, levels and other holes (it has 26 points, one for each corner and doorway side of the room below; at most
   20)" and "a face of PORTAL_well has 26 corners (at most 20): the room has too many openings in its walls". The hole
   takes a point from every step. The schema's own example (`open:well`) works only because the gallery's stair has 8
   steps. Worked round with an explicit `outline`.
2. **A hole's corner exactly 16 from the lower room's wall is refused** though the text says "at least 16": "the hole
   must lie inside room:well with every corner at least 16 units from its walls". 17 passes (the project's
   `open:pyr_well`; change its outline to 16 inside to see it).
3. **A stair room's top tread is one rise under the floor above**, so a stairwell whose first tread is level with the
   hall's floor (this one) has to be drawn one tread along; nothing says so except the schema's aside. A
   `slope.first_tread: level` or a note in the message would do.
4. **A room over a whole-room ceiling level** (`repro/lantern`): "openings[0]: the floor of room:lantern lies 1472
   above the ceiling of room:pyramid: a hole goes through at most 512 units (raise the lower room's ceiling, or put a
   shaft room between the two)". The hole is measured against the room's `ceiling` (960), not the level's flat top
   (2432) that the lantern stands on. And a whole-room level excludes every other ceiling level, so the lantern cannot
   be a second level either.
5. **A flight cannot end on a hanging platform** (`repro/flight_to_hanging_platform`): "rooms[1].flights[0]: a flight
   runs from a point on the lower floor (`from`) to a point on the higher one (`to`: here 1920 to 944), in steps of at
   most 40": the `to` point is read as the room's floor under the platform.
6. **A chest stands on the room's floor whatever is at its place** (`repro/chest_on_level`, build it): a chest inside
   a level 704 high and one on a hanging platform are both built at z 0 to 44, with "oymap validate: no issues". Hall
   8's four corner chests and the two closet chests are buried in their blocks (so they were in round one). The rooms
   schema says of levels "what stands inside the outline stands on the level".
7. **`ceiling_slope` may rise 1.9 times its run at most**; the back door chamber's roof rises 2 times (512 over 256).
   Drawn to 410 instead of 384. A whole-room level with `top_outline` has no such limit but needs a wall high enough
   for the room's doorways, which a roof from the floor line does not leave.
8. **A room under a roof that starts at the floor line has no wall**: nothing can be put on it ("exits[1]: the object
   does not fit on that wall of room:pyramid"), and `ceiling` must still be above the floor (960 here for 944).
9. **The texture of leaning ceiling sides is stretched along the slope** (in-game, `ingame_r2/rebuilt/04-well-head.png`,
   `01-pyr-floor-roof.png`, `11-cave.png`): t65c02's blocks come out as long streaks in bands; the original's roof has
   square blocks. No field sets it.
10. `oymap export`: `counts.doors` still says 200 beside 112 records.
11. `oymap compare`: a beam's top counts as a floor for the points (the two points on the original's upper platform
    at 2432 now "stand" on the slab beam, eye above the roof: "the rebuild has nothing within 4096").
12. `oymap probe` from inside the stairwell reports "blocked by a face ... (-2048, -1436, 1090)", a wall face of the
    stair room that ends at 944: its walls block above their tops.

### Gaps still open, most harmful first (numbers of the list above where they continue)

1. **Stairs and platforms one can stand under; a way up onto a hanging platform** (was 6). The tower's three flights
   are slabs with open space under them and its top is a box hanging from the roof with ramps inside; here the flights
   are solid to the floor and the box is beams. Most of sector 15's remaining loss (21 points of the 753). Wanted:
   `flights[].open_below`, a flight's `to` on a platform with a `base`, platforms as floors of a second storey.
2. **The lake** (11): banks that slope, and the causeway, which is a slab 64 thick over the water with a ramp at each
   end (underside -768, bed -896 under it). Sector 18 loses 10.7.
3. **The false floor of hall 8** (3) and its corner squares: the squares are hanging slabs like the walkway and stay
   levels only because of defect 6 (as slabs the score is 87.6 % at that step instead of 86.9 %). Sector 8 loses 10.
4. **The lantern, the arrival and the front exit** (defects 4, 5, 8): the party arrives 544 too low and the map has
   one exit.
5. **Floor, enter, leave and timer events; the retracting floor** (4, 5): unchanged. Sector 21's six points (5.8) are
   also the comparison's pose (tool defect b of round one), and sector 27's (5.0) its missing door faces (a).
6. **One panel on a wall, two textures on a leaf** (9): still the largest texture misses (t65a06 482 rays, t65a05br
   471, t65a07 460, t65a12 207).
7. **A platform's underside surface**: the walkway's underside is t65b04 in the original and takes `top_surface`
   here (167 rays).
8. Tunnel as nine ramps (10), a step higher than 40 (14), objects with no word (13): unchanged.

Closed this round: 1 (sloped ceilings), 2 (floor opening), 7 (stacked openings), 12 (platforms against walls; the
20-corner limit remains).

## Round three (2026-11-12): moving parts, events, panels

Edited by hand (the `gen/` scripts were not run). Two one-off helpers wrote mechanical parts and were checked by their
diffs; they are kept in `output/studio_cal/mm8_d05/r3/`: `movers.py` (the 46 buttons, six stones and four floor plates
of the original's door records as movers, their wiring, the door leaves' back faces) and `maze_panels.py` (the maze
halls' wall panels, from `maze_walls.py`'s measurement of the original's faces). The loop is `r3/loop.sh`, the
playtest `r3/play.sh`; backup of round two's end in `output/studio_cal/mm8_d05/r3_backup/`. Reports: `compare_r3`
(start), `compare_r3_end` (end); pictures `ingame_r3b` (mid-round) and `ingame_r3_end`, shots `r3/shots_r3.yml`.

### Scores

| | score | distances | textures |
|---|---|---|---|
| start of round three | 88.4 % | 90.2 % | 86.6 % |
| the tower's upper turn, the lantern, the recess and the front exit | 90.3 % | 92.3 % | 87.2 % |
| movers (buttons, stones, plates), the trap room's ledge and pit, the niche, plates and step events | 91.0 % | 92.9 % | 88.3 % |
| maze wall panels (`t65a06`/`t65a07` strips, `t65a01a`/`t65a01b`, button plates), door back faces | 92.1 % | 92.9 % | 92.0 % |
| the lake as one level, the causeway, stairwell walls, the tower's treads | 92.8 % | 93.4 % | 93.0 % |
| hall 8's corner squares as hanging slabs, chests at the original's size | 93.5 % | 94.1 % | 93.9 % |
| the tunnel as one climbing path (ten rooms gone), lantern panel, spikes (**end**) | **93.5 %** | 94.1 % | 93.9 % |

753 points; 4 without a floor in the rebuild (two at the edge of the alcoves, one at hall 8's east door, one at the
trap room's west door). Sector losses at the end: 15 (pyramid hall) 10.1, 18 (cave) 6.9 (was 10.7), 21 (pit) 4.5
(was 5.8), 8 (hall 8) 4.3 (was 10.1), 27 (the long maze passage, the tool's door faces) 3.8 (was 5.0), 1 (stones)
3.2 (was 6.2). Maze sectors 22 to 32 went from 0.88 to 0.97 and better.

- `compare.py`: `counted (structure, scale, play): 16 in, 4 near, 15 out`.
- Rooms: 85 (93 before: the tunnel is one room; lantern, recess and niche are new). Reached on foot with every door
  out of the way: 83 of 85; the two others are the lantern's own floor (a rim 16 wide round the hole over the box: the
  walkable floor up there is the box's top platform, in the pyramid's sector) and the niche 128 above the great hall's
  floor (reached into, not walked). `oymap solve`: nothing unreached, 12 waves against the original's 7, in the
  original's order (hall of stones; closets, stair, hall 8, return stair; the trap room; the great hall with the niche
  and the maze's entry; the maze hall by hall; the cave). It has more waves because each maze hall's buttons are one.
- Playtest: **passes, 217 of 217 steps** (192 in round two). New: the arrival in the recess (Simon Templar's
  dialogue on entering is presented and closed), down the box's three upper flights to its floor at 1920; all six
  stones start up and stone 94 sinks when used; touching the hall's floor opens the four alcove slabs (event 12);
  stepping back onto the dais raises the stone again (event 512); alcove button 1 goes into the wall; maze buttons 10
  and 11 trade places; the trap room: the four plates start out, using the far door shuts both doors and draws the
  plates back, the far door stays shut with one panel lit, the eighth panel lets the timer stop the plates and open
  both doors, and the party is still standing on the plate at -656; crossing the floor south of the stand opens the
  niche, whose chest is then taken. Not checked by the playtest: the casts of the spitting heads and the fire stand
  (the party crosses their plates; only that the walk is not stopped), the pit's kill (the party is immortal), the
  falls' count in hall 8.

- In-game pairs at the places changed (`r3/shots_r3.yml`, 12 pairs, `ingame_r3_end/diff`): mean edge agreement
  0.81 (tower-from-floor 0.97, under-north-flight 0.46, arrival-recess 0.99, box-floor 0.78, crusher-door 0.97, crusher-pit 0.66, maze-h22-south 0.93, maze-h30-north 0.53, sanctum-niche 0.92, cave-causeway 0.83, hall8-corner 0.95, tunnel-bend 0.72). Looked at: the arrival recess and lantern panel match; the trap room from its door matches; the box's
  flights match in place; under the north flight the rebuild shows the flight's solid side where the original is open
  (gap 1); the pit's walls rise to the ledge where the original's funnel slopes (gap 2). The mid-round set
  (`ingame_r3b`) showed the pit's spikes standing through the plates (defect 5) and the missing lantern panel; both
  fixed. In the maze pair a monster stands in front of the original's `t65a01a` panel.

### The 112 door records: all built

| kind | records | built as |
|---|---|---|
| doors in doorways | 52: the maze's plugs 52 to 93 (42), slabs 1, 3, 4, 5, 108, 109, 114 (7), the four alcove slabs of record 2, the secret panel 115, the block 6 that sinks | 56 `doors` (`slide_up`; 6 `slide_down`); record 2 is four doors |
| buttons that move in and out | 46: 10 to 51 (16 in and out of the maze halls' south walls), 100, 102, 104, 106 (48 out of the alcove walls) | 46 `movers` with `stretch: true` (only the front moves) |
| blocks that rise and sink | 6: stones 94 to 99 (top 160 on entry, sink to 32) | 6 `movers` (`bottom: -128`, `travel: [0, 0, 128]`), the two turned stones by `outline` |
| blocks that rise out of the floor | 4: 101, 103, 105, 107 (two blocks each) | 8 `lifts`, as in round two |
| floor plates that draw back | 4: 110 to 113 (two at -656 over two at -704, 639 from their walls) | 4 `movers` with `stretch: true` from a stub 16 wide at the wall, `travel` 624 |

Sideways doors, doors of two leaves, kerbs, lifts with `thickness` and `auto_return_seconds`: the original has none.
The game carries the party only on movers that rise or sink: the plates are level movers and drop the party, which is
what the original's trap does.

### Events now wired (`oymap flow` read for each)

12 (step on the trap hall's floor, once: the alcove slabs), 512 (step on `level:dais`: the stones rise), 1 (load:
Simon Templar speaks unless quest bit 403), 2 (load, two events for its two paths: the trap room reset or, once
solved, open), 63 (the far door: shuts both doors, draws the plates back, lights the panels), 102 to 109 (a panel
goes out), 110 (timer every 5: when all eight are out, the plates stop and both doors open), 101 (step on the trap
room's floor or the pit: the party is eradicated), 111 to 114 (13 plates round the four pedestals: four Poison Sprays
each, from the original's points), 115 (five plates: four Fire Bolts from the stand's corners), 453 (a plate south of
the stand: the niche opens), 451 and 452 (falls into hall 8 counted, armed again on the walkway). Still not wired:
506 to 511 (the stones sink when clicked, not when stepped on), 6 and 10 (on leaving), the effects SetFacetBit (451)
and SetLight (63, 102 to 109: the eight panel lights are not built), the texture change of door 1 on opening (11).

### What changed

- The tower: landings and flights hang as in the original (landings 32 thick as hanging platforms; flights from
  landing to landing with side walls 32 thick and 96 high, measured; treads `t65c02`); the box that hangs from the roof
  holds its floor at 1920 (one hanging platform, was a slab and a level), two landings, three flights (4, 8 and 4 steps
  of 32 where the original has ramps) and the top platform at 2432; its walls are nine beams following the ramps'
  undersides as measured. Above the roof `room:lantern` (640 square, roof 2816 to 2688, the `t65c12` panel on its north
  wall) opens onto the box by a hole in its floor; `room:recess` (32 higher, 0 wall between) holds the arrival and the
  **front exit** (`exit:front`, event 501). `ph:front_exit` and `ph:tower_top` are gone.
- The trap room: floor at -736 (the funnel's top), the pit sunk in it (`level:pit`, -1152) with 36 posts; four plates
  as stretching movers; the eight panels dark until the trap lights them; `ph:pit` gone.
- The great hall: the niche behind the north wall (`room:niche`, door 115 `slide_up`, the chest in it); 19 floor
  plates for events 111 to 115 and 453; the spitter placeholders gone (`ph:fire_stand` keeps only the book).
- The maze: 46 buttons are movers; every hall wall has its corner strips, `t65a01a`/`t65a01b` panels and the button
  plate (`t65o02c` under `t65a12`) as measured (`walls[].panels`); every maze door's back is `t6502`, door 1's front
  `t65a05al`, door 5's back `t65a05bl` (`back_surface`).
- The cave: one lake level midway down the banks (the banks run from the walls' foot to the bed: there is no shore),
  the causeway as a block on the lake bed to -704 with a step block at each end, sides `t65b02`, top `t65b03`.
- Hall 8: the corner squares hang like the walkway (they were levels to the floor); the chests are boxes 128 by 128 by
  96 of `t65b13`/`t65b04` on them, as the original's (the pedestals were the chests); the closets' chests likewise.
- The tunnel is one `path` room climbing from 560 to 160 (ten rooms and nine openings gone).
- The stairwell's long walls are `t65o02c`.

### New features: worked

`movers` (stretching buttons and plates, rising stones, turned stones by outline), `trigger: step|timer|load`,
floor `plates`, `id` on levels and platforms, effects `cast` and `set`, `walls[].panels` with `offset`, `from: end`,
`bottom`, `height`, `at: centre`, `back_surface`, `tread` on flights, a climbing `path`, flights ending on hanging
platforms with `to_height`, a room standing on a whole-ceiling level's flat top with a floor hole (the lantern), objects
on the highest floor (chests on the hanging corner slabs), a platform standing in a sunken level (the causeway).
Switches have cog numbers in ids.lock.yml, so a script can light them (`evt.SetTexture`); movers have door numbers, so
a script can stop them (`evt.StopDoor`).

### Refused or misread (each: `oymap validate <folder> --assets assets_dev`, under `output/studio_cal/mm8_d05/repro/`)

1. `step_on_mover`: "events[0].source: mover:stone is a mover, which is clicked: a step event's source is a room, a
   level or platform with an `id`, or a plate (put a plate in front of it)". The stones of 506 to 511 stay clicked.
2. `flight_from_under_platform`: "a flight runs from a point on the lower floor (`from`) to a point on the higher one
   (`to`: here 928 to 544)": `from` takes the highest floor, so a flight cannot start on a platform with another above
   it (the box's floor at 1920 under its top at 2432). The top platform stops 16 short of the original's (y -1424).
3. `platform_hanging_in_sunken_level`: "platforms[0].base: must be at least 0": `base` counts from the room's floor,
   so a slab cannot hang over a sunken level lower than the room's floor (the causeway: top -704, underside -768, the
   cave's floor -640). Built standing on the lake bed.
4. `flight_from_platform_in_sunken_level`: "(`to`: here 192 to 0)": the build stands the platform on the sunken level
   (top -64) but the flight check reads it on the room's floor (192). The causeway's end steps are step blocks instead.
5. `tapered_platform_in_sunken_level` (validate passes; build it and read the faces): a platform with `top_size` in a
   sunken level is built on the room's floor (z 0 to 128), the same block without `top_size` on the level (-256 to
   -128). The pit's spikes stood 48 through the plates; they are posts 8 square without taper now.
6. `plate_16_from_wall`: "plates[0]: the plate does not lie inside room:a with every corner at least 16 from its
   walls" for a plate exactly 16 from the wall, then the false follow-on "events[0].source: plate:p is a plate, which is
   clicked". Two plates of the great hall are drawn 17 from the wall.
7. `exit_full_width`: "exits[0]: the object does not fit on that wall of room:recess" for a doorway as wide as its wall
   (the original's), then the round-one follow-on "the exit leads to , which is not in project.yml neighbours". Drawn
   240 wide.
8. `switch_from_door`: "a switch preset cannot have the door door:d as its source". The trap (event 63) is a script
   that moves the doors and plates by their numbers in ids.lock.yml.

### Gaps still open, most harmful first

1. **A flight standing on the floor is solid beneath** (the tower's north flight, 944 to 1328 over 1472: open beneath
   in the original, a slab with a sloped underside 32 under the treads). Most of sector 15's remaining 10.1 (worst
   points (-4096, -512) and (-4096, -768), 0.24 and 0.30). Wanted: `flights[].underside: {thickness}` (or
   `open_below: true`).
2. **Floors that slope down on all sides** (the cave's bowl: banks from the walls to the lake bed; the trap room's
   funnel round the pit). Sector 18 loses 6.9, sector 21 4.5 (with the unseen floor at -1023). Wanted:
   `levels[].bank: <run>` (sloped sides from the room's floor to the level's).
3. **A floor that is seen and not solid** (hall 8's false floor at -352; the pit's killing floor at -1023, unseen):
   `levels`/`platforms` with `solid: false` and `visible: false`. Hall 8 is now 0.94 without it.
4. **A door leaf of two textures side by side**: every maze plug, doors 1, 5, 108 and 109 show `t65a05bl|t65a05br`
   (`t65a05al|ar`, `t65b05l|r`) as one picture 256 wide; the rebuild tiles the left half twice. The largest texture miss
   (481 rays). Wanted: `surface: [left, right]` on a door, or `panels` on a leaf.
   Also a leaf's surface is stretched over the leaf whatever its `size`: the plugs' `t6502` backs (rock 128 wide in
   the original) come out twice as wide (pair maze-h30-north, 0.53). Wanted: a leaf surface that tiles at its size.
5. **A platform's underside** (hall 8's walkway and corner slabs: `t65b04` under, here the top surface: 187 rays).
   Wanted: `platforms[].under_surface`.
6. **Step events on a mover** (repro 1) and **a hanging slab in a sunken level** (repro 3).
7. **Events with no word**: on leaving the map (6, 10: `trigger: leave`); stopping a mover (`stops:` beside `opens`,
   done with `evt.StopDoor` and numbers); a door's two sides running different events (63 inside, 62 and 64 outside:
   one event per door here); a face's attributes changed by an event (SetFacetBit in 451); a light that starts off and
   an event that switches it (the eight panel lights, SetLight); textures changed by an object's name rather than its
   cog number (`texture:` takes cog numbers from ids.lock.yml).
8. **A flight from under a platform** (repro 2): `flights[].from_height`.
9. Unchanged: a step higher than 40 (sector 10's six steps of 48 are eight of 36), items lying in the map (three
   books), the tunnel's irregular rock (a climbing path cannot be `rough`; its ceiling keeps 256 where the original's
   is 250 to 450).

### Tool defects

- `oymap validate`: repros 4 to 7 above (a flight's reading of a platform in a sunken level; a tapering block in a
  sunken level built on the room's floor; a plate exactly 16 from a wall and the false "which is clicked" after it; an
  exit as wide as its wall and the empty "leads to ," after it).
- `oymap compare d05.blv --world mm8 --with <L4>`: still leaves the original's door faces out (sector 27's long
  passage, 3.8 lost: its side walls belong to door 56) and reads the original's trap room in its stored pose (sector
  21's points stand in the pit).
- `oymap fmt`: writes the `outline` of a mover as a block list (one point a line) and turns a one-line list back into
  it, while rooms' and plates' outlines stay on one line.
- `oymap assets <texture>` gives no width or height (`null`), so a panel's texture size is guessed (`t65c12` drawn as
  one picture 256 square).
- `oymap audit --reach` counts a room whose whole walkable floor is a hole's rim (the lantern) as not reached.
- `ids.lock.yml` keeps the numbers of removed objects (`lift:stone_94: 9`, the tunnel rooms); harmless, but a
  playtest written against the old numbers silently means other objects only if numbers were reused.

### Unsure of in the original

- The panels' look before the trap: dark (`t65b11b`) in the file; the trap lights them. Built so.
- Whether the original's funnel kills on touch only by event 101 being on its faces (it is), and why the unseen floor
  at -1023 lies 15 under the pit's mouth.
- The size of `t65c12` (one picture or two across the 256 panel).
- Event 64's hint ("Leave the Abandoned Temple") on door 109's outer side, which only opens the door.

### A rule slip

In this round one `rm -rf output/studio_cal/mm8_d05/r3/tmp_cause/build` (a scratch build of my own) ran chained after
other commands instead of as its own command after an `ls`. Nothing else was removed.

## Round four (2026-11-12, night)

Edited by hand; no generator run. No helper wrote project files (the bank runs were measured by
`output/studio_cal/mm8_d05/r4/banks.py`, read only; the one-off renumbering of hand-written map variables is
described below). Backup of round three's end: `output/studio_cal/mm8_d05/r4_backup/`. Loop `r4/loop.sh`, playtest
`r4/play.sh`; reports `compare_r4_start`, `compare_r4_end`; game pairs `ingame_r4/diff` (shots `r4/shots_r4.yml`).

### Scores (merged measure, 744 points)

| | score | shape | textures |
|---|---|---|---|
| start of round four | 94.4 % | 94.5 % | 94.3 % |
| north flight open below, its side walls as raking beams, its solid foot; box top at full size (`from_height`) | 95.2 % | 95.6 % | 94.2 % |
| cave: lake bed with banks to every wall (`bank`), causeway as a hanging slab, ramps, end fills | 96.0 % | 96.5 % | 94.7 % |
| trap room: one banked pit level (funnel), tapered spikes | 96.2 % | 96.9 % | 94.7 % |
| great hall corner panels (t65a06/t65a07, t65b06t/t65b07t) | 96.3 % | 96.9 % | 95.0 % |
| exits at 256, chest c19, texture sizes from `oymap assets`, trap as a preset (**end**) | **96.3 %** | 96.9 % | 95.0 % |

Sector losses: 15 (pyramid hall) 8.5 to 3.6, 18 (cave) 6.9 to 0.9, 21 (pit) 4.5 to 2.6, 17 (great hall) 2.2 to
0.4, 16 1.6 to 0.1. Left: 15 3.6, 8 (hall 8, the false floor) 3.4, 21 2.6, 3 (tunnel) 1.1, 14 1.1.

- `compare.py`: unchanged in kind (counts rooms against sectors); doors 119 against 112, bound events 88 against 89.
- Rooms: 85. `oymap audit --reach`: 84 of 85 on foot with every door out of the way (the lantern is now reached;
  the niche, 128 above the hall's floor, is reached into). `oymap solve`: nothing unreached, 12 waves, in the
  original's order as in round three.
- Playtest: **passes, 237 of 237** (217 in round three). New: the party jumps from the dais onto stone 94
  (`movement_segment` with `jump`) and rides it down to 32 (stepping, not an event call, sinks it; the stone's
  faces carry the pressure-plate attribute and not the clickable one); again after the dais raises it; the cave is
  crossed with no flights (down the bank from the causeway's end, up the north bank to the niche: banks of 1.0 to
  1.06 are walked in the game); the fire stand's plate and a spitting head's plate run their events
  (`pressure_plate_triggered` 90 and 94); the first fall into hall 8 is counted (`state_dump_map_var` 56 = 1,
  57 = 1); the pit kills (`pressure_plate_triggered` 92 and the condition `eradicated`, the party set into the pit at
  the end of the walk). Not asserted: that the casts hit (see tool defects).
- Game pairs (11, `ingame_r4/diff`): mean edge agreement 0.86. Looked at: under the north flight the rebuild now
  shows the open underside and the solid foot's rock face where the original has them (0.74; the original's foot is
  darker); the cave from the bed and along the causeway match (0.91, 0.89: banks, slab, ramp, fill); the pit with its
  tapered spikes matches below the mouth (0.75: above it the original draws black where the rebuild shows its
  banks); the niche's panel matches (0.92).

### What changed

- **The tower.** The north flight (944 to 1328) is `open_below: 16` with `to` moved one tread on so its treads are
  the original's 64 deep (they were 61). Its side walls are two raking `beams` (32 wide, 96 deep, undersides 944 to
  1328 and 944 to 1277, as the original's) in place of `sides`, which stay solid to the floor. The original's flight
  is closed underneath from its foot to y -895: a wedge platform (`top_slope`, t6502). The box's top platform is the
  original's 640 by 256 (was 16 short on every side) and the first upper flight starts under it (`from_height`).
- **The cave.** The lake level's outline is the original's lake floor face (16 of its 17 corners); each side banks
  up to the wall it faces (`bank`, one run per side, 242 to 255: the distance to the wall less 1), `steep_floor` on
  the room. The two invented flights out of the lake are gone. The causeway is a slab 64 thick hanging 128 over the
  bed (`base` in the sunken level); its ramps (from -640 at the end walls to -704 over 256) are wedge platforms over
  the banks, and the fill under each end of the slab faces the lake (a block 32 deep, 128 high). The room's points
  for this were taken one for one from the original's lake face (16 points).
- **The trap room.** The pit is a sunken level at -1152 whose banks rise from its floor to the walls' foot (254 run,
  steep): the funnel's top edge is the original's; a funnel ending in an upright shaft cannot be said (gap 2). The 36
  spikes taper 16 to 2 over 128 (`top_size`), as the original's (built identical to the original's faces). The
  plates' stubs are 2 wide on the 2 units of level floor at the walls (travel 638) because a mover's height counts
  from the floor at its place (on a bank, lower).
- **Events.** The six stones sink when stepped on (`trigger: step` with the mover as source). The trap (event 63) is
  a `switch` preset with the far door as its source and the doors and plates in `closes`; only lighting the panels is
  Lua (cog numbers). The casts of the heads and the stand were already `cast` effects and write exactly the
  original's calls (`CastSpell(24, 10, 1, x, y, z, 0, 0, 0)`, `CastSpell(2, 10, 1, ...)`): checked with `oymap flow`
  against the installed Lua.
- **Map variables.** The hand-written Lua used MapVar(61) to (85) (the maze closets' summons) and (90), (91) (the
  falls); the game keeps 75 map variables (0 to 74) and reads 75 and above as decoration variables. Renumbered by
  hand-checked replacement in `wiring.yml` to 31 to 55 and 56, 57 (the build's named variables take 0 to 26).
- **Objects.** Both exits are 256 wide (the original's doorways fill their walls). Chest c19 is the size of the
  original's chest picture (128 by 128, `cr_w128b` on its front, 48 deep) with its front where the picture is (y
  3604) and its width across the niche (`facing: e`). Texture sizes from `oymap assets`: t6502 on door backs 128 by
  128 (was 128 by 256), t65a11 on the plates' edges 64 by 32, the spikes' t65b13a 16 by 64, solid01 16 by 16.
- **The great hall.** Each wall begins with a t65a06 panel under t65b06t and ends with t65a07 under t65b07t, 128
  wide (`walls[].panels`), as measured from faces 2305 to 2363.

### New features: worked

`flights[].open_below` (a number), `flights[].from_height`, `levels[].bank` with a run per side, `steep_floor`,
`top_size` in a sunken level, `base` in a sunken level (the causeway), `top_slope` blocks over a bank (with the
defect below), step events on movers, a switch preset with a door as source moving doors and movers by its lists,
exits as wide as their wall, `oymap assets` sizes.

### Refused or misread (each under `output/studio_cal/mm8_d05/repro/`; `oymap validate <folder> --assets assets_dev`,
or build with `--out` into a scratch folder and read the faces)

1. `hole_under_sloped_floor`: "an opening with `in: floor` leads from the upper room (`from`: room:a, floor -736,
   sloped) down to the room under it ...: the upper room needs a level floor at or above the lower room's level
   ceiling (... put a level landing room over the hole if the upper floor slopes)". The funnel over the pit: the
   funnel's floor is level where the hole is (its mouth), and no landing room can stand there.
2. `level_in_level`: "rooms[0].levels[1]: the region cannot be cut out of room:a: keep it inside the room and clear
   of its walls and of the room's other regions": a pit level inside a banked level (the other way to say a funnel
   over a shaft).
3. `bank_to_wall`: the same message for a bank whose top edge reaches the wall exactly (the original's cave banks
   start at the walls' foot): the run must stop 1 short, which leaves strips of level floor 1 to 26 wide along the
   walls.
4. `block_over_bank` (validate passes; build it): a `top_slope` block standing over a bank takes its foot from the
   bank's height under its middle and has no underside, so its top lies below the room's floor at the wall and the
   space where the bank falls away under its foot is open into the block. The causeway's ramps use `base: 1` to get
   an underside drawn (the nearest honest thing; the original's ramps sit on a fill).
5. `mover_on_bank` (validate passes; build it): a mover's `bottom` counts from the floor at its `at`, here the bank
   (plate top 70 where 80 is meant); movers have no `floor_height`.

### Gaps still open, most harmful first

1. **A floor seen but not solid, or solid but not seen** (hall 8's false floor at -352: sector 8 loses 3.4; the
   pit's killing floor at -1023, which is where the comparison stands its six points: part of sector 21's 2.6):
   `levels`/`platforms` with `solid: false` / `visible: false`.
2. **A funnel over a shaft** (the trap room: banks falling to a mouth at -1008 and upright walls from there to
   -1152): a hole under a level part of an uneven floor, or a level inside a banked level (repros 1, 2). The bank is
   drawn straight to the pit's floor, up to 144 under the original's funnel at the mouth.
3. **A door leaf of two textures side by side** (t65a05bl|br on every maze plug and doors 1, 5, 108, 109: the
   largest texture miss, 479 rays): `surface: [left, right]` on a door.
4. **A platform's underside** (hall 8's walkway and corner slabs, t65b04 under: 188 rays): `under_surface`.
5. **Events on leaving the map** (6, 10), **a different event per door side** (63 inside, 62/64 outside), a face
   attribute set by an event (SetFacetBit in 451), lights that start off and are switched (SetLight), textures
   changed by an object's name rather than its cog number, stopping a mover (`stops:`; StopDoor in Lua).
6. A bank that reaches the wall (repro 3), a block that stands on a bank with its foot at the bank's foot and its
   underside closed (repro 4), a mover's height over a bank (repro 5).
7. Unchanged: a step higher than 40 (sector 10), items lying in the map (three books), the tunnel's irregular rock
   and ceiling (sector 3 loses 1.1; not tried with `section` this round).

Where score and shape pulled apart: nowhere taken the score's way. The funnel could have been drawn as a banked
level at -1008 with no pit (its floor near the comparison's unseen -1023 floor), which would score sector 21 better
and hide the visible pit with its spikes: not done.

### Tool defects

- `oymap validate`: repros 3 to 5 above.
- `rooms` schema (`steep_floor`, `bank`): "the party walks up at most 0.9 for each unit of run ... the party does not
  walk up them" — the game walks up to normal z 0.6866 (a rise of 1.058 per unit, `game/indoor/IndoorGeometryUtils.cpp`
  `WalkableSlopeNormalZ`); the playtest climbs the cave's north bank (rise 1.0) built under `steep_floor`.
- `oymap validate` / build: hand-written Lua may name `MapVar(n)` for n of 75 and above; the game keeps 75 map
  variables and reads those as decoration variables (`game/events/EvtEnums.h`), silently. A warning is wanted.
- Headless runs cannot assert that an event's cast hits: `assert: {projectiles}` takes `source: actor|party` only
  (event projectiles are a third kind), and in both the original (`d05.blv`) and the rebuild a stationary party on
  the plates, with immortality off, keeps full hit points after the events and after `console: projectile spell 2
  <from> party 10 1` ("Spell cast.") — scenario `output/studio_cal/mm8_d05/r4/cast2.yml`. Not understood whether the
  bolts miss or are not moved headless.
- `play_lua`'s `click(n)` runs event n directly, so it cannot show that a face is not clickable.
- `state_dump_map_var` refuses an index of 75 and above ("map variable index out of range") although Lua can write
  them (see above).
- `oymap export <project folder>` writes `ids.lock.yml` into the folder it reads (it did so in two repro folders;
  removed). It should build privately as `audit` and `solve` do.
- In this round the game binary was absent for some minutes (being rebuilt by another session); runs waited for it.

### Unsure of in the original

- Why the original's funnel and pit draw black above the mouth from inside the pit (pair `crusher-pit`): probably the
  unseen floor at -1023 with its portal at -1008.
- Whether the original's event casts hit the party in this engine at all (see tool defects).

## Round five (2026-11-13): contents, floors seen and not solid, lights

Edited by hand; no generator run. Two one-off helpers wrote measured numbers and were checked by their whole diffs:
`output/studio_cal/mm8_d05/r5/objects_edit.py` (items, panel lights, plate stubs, chest contents, placeholders
removed) and `r5/rooms_edit.py` (hall 8's false floor and undersides, the pit's unseen floor, the cave's east stand
and recess, openings `height: full`, the L of the back stair's foot). Backup of round four's end:
`output/studio_cal/mm8_d05/r5_backup/`. Loop `r5/loop.sh`, playtest `r5/play.sh`; reports `compare_r5_start`,
`compare_r5_end`; game pairs `ingame_r5/diff` (shots `r5/shots_r5.yml`).

### Scores (744 points)

| | score | shape | textures |
|---|---|---|---|
| start of round five | 96.3 % | 96.9 % | 95.0 % |
| end | **96.5 %** | 97.0 % | 95.3 % |

Sector 21 (the pit) 0.565 to 0.864 (the unseen floor at -1023 is where the measure stands its points); sector 19
0.897 to 0.923 (the foot of the back stair as an L); sector 10 0.912 to 0.925; sector 17 0.959 to 0.962. **Sector 8
(hall 8) fell 0.955 to 0.938, and that is the measure's**: from the hall's floor its rays see the rebuild's false
floor as a ceiling 704 above (`the ceiling is 321 lower`, `ceiling up to the north is 560 nearer`) and see through
the original's single upward face. The game draws indoor faces from both sides (no culling state in
`game/indoor/IndoorRenderer.cpp`), and the pair `ingame_r5/diff/01-hall8-floor-east.png` shows both maps from the
floor with the same t65b03 sheet overhead (edge agreement 0.93). Kept.

- `compare.py`: `15 in, 3 near, 17 out` (round four 16 in): the recess over the east stand is a room 64 high, so the
  smallest sector height and doorway height now count against the original's (whose recess is part of sector 18).
- Rooms: 86. `oymap audit --reach` and `oymap solve`: nothing unreached; two niches too small to stand in (the great
  hall's chest niche and the new recess, both reached into); `solve` in the original's order as in round four.

### Contents: placed of the original's

- **Fixed monsters: 0 of 0.** `d05.scene.yml` `initial_state.actors` is empty: every monster of this map comes from
  its 52 spawn points (kept as spawn points) or from the maze closets' summons (events 23 to 61).
- **Lying items: 3 of 3** (`initial_state.sprite_objects`), objects.yml `items`: the Prophecies of the Sun (626) on
  the middle stand's top in the great hall (z -384), a second one on the floor of the cave's niche (z -640), and item
  186, a **Diamond**, on the stand at the causeway's east end (z -496). Rounds one to four took that last one for the
  Prophecies of the Snake; the Snake (652) is in chest 0, which is what event 10 asks after.
- **Chest contents: 7 of 7 chests that the map opens** (events 81 to 86, 100), from the scene's chest records: chest 0
  the Prophecies of the Snake (652) and five random items, chest 1 an Old Scroll (750) and seven, chest 19 the Idol of
  the Snake (630) alone, chests 2 to 5 four to thirteen random items. The original gives each roll its own level (1
  to 4); a chest here has one `treasure_level` (the mean, rounded). The original's chest 6 (eleven random items) has
  no face and no handler opens it (events 87 to 99 name chests 6 to 18, of which only 6 has a record): not built.
- Placeholders: `ph:fire_stand`, `ph:niche_book`, `ph:snake_book` and `ph:false_floor` became the real things (the
  snake book's stand is now built: a rock block 64 by 160 against the east wall up to -512 with a t6502c cap to -496,
  and the recess in the wall above it, 32 deep and 64 high, as the original's faces 3602 to 3618). `ph:simon` stays:
  it stands for events 6 and 10, which run on leaving the map (no word).
- Lights: 60 of 60. The eight panel lights (the original's light records 1 to 8, attributes 8: dark at the start)
  are lights with `on: false`, at the original's places (z -480: `height` 357.5 over the bank at -837.5); the build
  writes them as the original's records with ids 1 to 8, which `evt.SetLight` names.

### Events (`oymap flow`, each against the original's)

| original | rebuild | |
|---|---|---|
| 1 (load: Simon speaks unless qbit 403) | evt:simon | same |
| 2 (load: trap room reset, or open when solved) | evt:crusher_reset, evt:crusher_solved_load | same (two events for its two paths) |
| 6, 10 (on leaving: qbits by items 626, 652) | ph:simon | missing: no event on leaving the map |
| 11 (door 1 opens, its two leaf textures change) | evt:door_1 | differs: the texture change is missing (a door leaf has no cog and one surface) |
| 12 (step on the trap hall's floor: the alcove slabs) | evt:alcoves_open | same |
| 13 to 16 (doors 3 to 6) | evt:door_3 to evt:door_6 | same |
| 17 to 19 (doors 7 to 9, which do not exist) | none | not built (no door) |
| 20 to 61 (maze buttons, summons on the first press of a wrong one) | evt:button_10 to evt:button_51 | same (summons as the original's own Lua call, guarded per button) |
| 62 (door 108 from the corridor) | evt:door_108 | same |
| 63 (inside of both trap doors: doors, plates, panel textures, panel lights) | evt:crusher_trap | differs: on the far door from either side (one event per door); lights now `lights_on`, textures still Lua by cog |
| 64 (door 109 from outside) | (in evt:crusher_trap) | differs as 63 |
| 81 to 86, 100 (chests) | evt:chest_0 to 5, evt:chest_19 | same, with the original's contents |
| 87 to 99 (chests 6 to 18, no faces) | none | not built |
| 101 (funnel, pit floor, unseen floor: eradicated) | evt:pit_kill | same: now also on the unseen floor (`platform:pit_floor`) |
| 102 to 109 (a panel: toggles its light, texture and count) | evt:panel_1 to 8 | differs: each panel goes out once per run (no second press relighting it); its light goes out (`lights_off`), its texture by its `on` surface |
| 110 (timer: all out, the plates stop, doors open) | evt:crusher_timer | same (StopDoor in Lua) |
| 111 to 115 (casts from the heads and the stand) | evt:spit_1 to 4, evt:fire_stand | same calls (`CastSpell(24, 10, 1, ...)`, `CastSpell(2, 10, 1, ...)`); not assertable headless |
| 451 (a fall counted; the third marks the walkway) | evt:fall | differs: counted; SetFacetBit has no word |
| 452 (the walkway arms the count) | evt:walkway | same |
| 453 (floor south of the stand opens the niche) | evt:niche_open | same |
| 501, 502 (exits) | evt:exit_front, evt:exit_back | same |
| 506 to 511 (step on a stone: it sinks), 512 (the dais raises them) | evt:stone_94 to 99, evt:dais | same |
| 513 to 516 (the four step buttons in order) | evt:step_1 to 4 | same (the original's SetFacetBit that moves the clickable mark is said by `once` and the conditions) |
| 517 (door 114) | evt:door_114 | same |

Of the 94 handlers that do something and stand for something in the map (leaving out 3 to 5, 7 to 9, 17 to 19 and
87 to 99, which name nothing): 80 same, 12 differ (11, 63, 64, 102 to 109, 451), 2 missing (6, 10).

### Playtest

**Passes, 252 of 252 steps** (237 in round four), four runs of four (`run/play_r5_c.log`, `play_r5_run2.log` to
`play_r5_run4.log`). New: chests 0, 1 and 19 give up the Prophecies of the Snake, the Old Scroll and the Idol of the
Snake (`has_item`); the trap lights the panel lights (asserted on lights 52, 55, 59: the map's list places the
original's ids 1 to 8 at 52 to 59), seven panels put out darken theirs (52 and 58 dark, 59 still lit), the eighth
darkens 59; the book on the middle stand is taken from the floor with the use key (`pick_up`, 244 away), the Diamond
on the east stand (229), the second book in the niche (137), counted (`item_count(626)` 1, then 2); the party
dropped into the pit lands on the unseen floor at -1023 (asserted 6656, 2432, -1023) and event 101 eradicates it.
The fall into hall 8 now passes through the false floor (the walk from the west door's walkway into the hall lands at
-1056 and is counted, map variables 56 and 57 as before).

### What changed

1. **Hall 8's false floor**: two sheets at the walkway's height, `solid: false`, whose outlines are the complement of
   the walkway (as thinned in round two) and the four corner slabs: the original's faces 521 to 546 at -352. They are
   1 thick with t65b03 under them (the original's single face shows its t65b03 from below in the game). The walkway
   and the corner slabs take `bottom_surface: t65b04` (faces 460 to 481, 547 to 550). The pair from the west door
   (0.92) shows the hall as the original's: one floor with the walkway hidden in it.
2. **The pit's unseen floor**: a slab 1 thick over the pit's 768 square at -1023, `visible: false`, with an `id` that
   runs event 101 (the original's face 2190, invisible, event 101).
3. **Contents**: three items lying, chest contents with the two quest books' and the idol's places corrected, the
   eight panel lights and `lights_on`/`lights_off` in the trap.
4. Also: the plates' stubs (`floor_height: -736`; west and south 1 wide, 639 travel, as the original; east and north
   2 and 638, see refused); the foot of the back stair (`room:s19a`) as the original's L (a passage 128 deep from the
   great hall's portal, faces 1516 to 1523, 1666), so the portal is the passage's whole end (`width: full`) and the
   hall's wall no longer has a phantom strip of the stair room behind it; six openings between rooms that meet in one
   plane say `height: full` (they were the lower room's height in numbers; no change in faces);
   `migrated: [platform_in_sunken_level]` (the 36 spikes, the causeway and its ramps stand as built in round four:
   the build's new rule measures them as they were meant).

### New features: worked

`items` (three, taken in play), chest `items`/`random_items`/`treasure_level`, `lights[].on: false` with effects
`lights_on` and `lights_off` (the build writes the original's light records, attributes and ids), `platforms[].solid:
false` (fallen through in play), `platforms[].visible: false` with an `id` as a step source (landed on, kills),
`bottom_surface`, `movers[].floor_height` and a half-unit `at`, platforms against walls (the stand), a platform with
`base` on another (the cap), `from_wall`/`to_wall`, `migrated`. Not used: `monsters` (the original places none),
condition `lua` (the trap's tests are map variables), `kills`, ladders, sounds.

### Refused or misread (under `output/studio_cal/mm8_d05/repro/`)

1. `mover_half_unit_at_wall` (`oymap validate`): a mover 1 wide against the east wall (`at: [1279.5, 640]`, `size:
   [1, 1280]`) is refused, "movers[0]: the position [1280, 640] is not inside room room:a"; the same against the west
   wall (`at: [0.5, 640]`) passes. The middle is rounded before the inside test. The east and north plates are 2 wide.
2. `block_over_bank` (round four's repro, built again in `r5/repro_bob`): unchanged, a `top_slope` block over a bank
   still takes its foot from the bank under its middle (-128 where the wall's foot is 0) and is open below; platforms
   have no `floor_height`. The cave ramps keep `base: 1`.
3. `thin_wall_full_mouth` (`oymap build ... --out <scratch>`): "opening open:corr_hall is in a wall without thickness
   and leaves wall round it ... one will show through the other" for a corridor whose whole end wall is the opening:
   only the hall has a wall in that plane, so nothing shows through (checked on this map's build: at corr9/hall8,
   tunnel/trap hall, the stair foot, the back-door chamber, only one room has faces in the plane). The warning fires
   when the walls' looks differ and the opening is lower than the higher ceiling (`core/IndoorLowering.cpp` 6770),
   whether or not the lower room leaves wall there. Eight of this map's openings get it; moving the rooms 16 apart
   would put a wall the original does not have. Left.

### Compromises

- Undone: the false floor missing (round two's gap 3), the unseen killing floor missing, the walkway's underside in
  the top's texture, the plates' 2-wide stubs (west and south), the snake stand missing, items as placeholders.
- Left: the funnel drawn straight to the pit's floor (no word for a funnel over an upright shaft:
  `level_in_level`, `hole_under_sloped_floor`, `bank_to_wall` unchanged); the cave ramps' `base: 1`
  (`block_over_bank`); the east and north plates 2 wide; the walkway's outline thinned to 23 points (the false floor
  follows it, so the two meet; the original's walkway has 41); one event per door (63 on the far door from both
  sides); each panel goes out once per run.

### Gaps still open, most harmful first

1. **A door leaf of two textures side by side** (t65a05bl|br on every maze plug and doors 1, 5, 108, 109; 479 rays,
   the largest texture miss; pair `crusher-door` shows half the face twice): `surface: [left, right]` on a door.
2. **A funnel over an upright shaft** (the trap room, sector 21 0.864): a level inside a banked level, or a hole
   under the level part of an uneven floor.
3. **Events on leaving the map** (6, 10: the quest bits for the two books): `trigger: leave`.
4. **A different event per door side** (63 inside both trap doors, 62 and 64 outside): `doors[].events: {front,
   back}`.
5. **A texture changed by an event on a door leaf** (11) and by an object's name rather than its cog (63, 102 to
   109); **a face attribute changed by an event** (SetFacetBit in 451).
6. A block that stands on a bank with its foot at the bank's foot (`platforms[].floor_height`, repro
   `block_over_bank`); a mover's half-unit middle against a high wall (repro `mover_half_unit_at_wall`).
7. A raking beam whose top stays level (the box's walls under the pyramid's flat top: three beams rise 128 to 256
   above it, hidden behind the lantern's walls; the build warns): `beams[].top`.
8. Unchanged: a step higher than 40 (sector 10), the tunnel's irregular rock and ceiling, a chest of mixed levels.

### Tool defects

- `oymap validate`: repro 1 (a half-unit mover middle rounded before the inside test).
- `oymap build`: repro 3 (the thin-wall warning where the lower room leaves no wall).
- `oymap compare`: counts the original's one-sided false floor as absent when seen from below while the game draws
  it (sector 8 loses 1.7 for the rebuild's sheet that the game shows in both); `oymap compare d05.blv --world mm8
  --with <L4>`, worst points of sector 8 at -1056.
- `assert: {light: {key}}` takes the light's place in the map's list (52 to 59 here), while `evt.SetLight` and
  ids.lock.yml `lights` use the light's id (1 to 8); before any switch a light reads "unset", not its starting state.
  Worth a word in the scenario docs.
- `calibration/compare.py`: still counts rooms against sectors; a recess drawn as a room moves two more lines out.

### Where score and the original pulled apart

Hall 8: the false floor lowers sector 8 by 1.7 and is kept (the game shows it from below in both maps). Nothing was
done for the score.

## Round six (2026-11-13): what the player sees

Edited by hand, plus one one-off helper checked by its whole diff (`output/studio_cal/mm8_d05/r6/edits_r6.py`: door
leaves, chests, door 1's corridor ceiling, the per-side and leave events) and two small scripted edits of many alike
blocks (`fold`/`travel` on 55 doors, the 24 closets' theme), each diffed. Backup of round five's end:
`output/studio_cal/mm8_d05/r6_backup/`. Loop `r6/loop.sh`, playtests `r6/play.sh` and `r6/play4.sh`; reports
`compare_r6_start`, `compare_r6_end`; pictures `output/studio_cal/mm8_d05/ingame_r6/` (below). From 11:20 the
studio binary was the merged one with the Forge fixes; everything after that point is built with it.

### Scores (744 points)

| | score | shape (distances) | textures |
|---|---|---|---|
| start of round six | 96.5 % | 97.0 % | 95.3 % |
| door leaves of two pictures, tiled rock leaves | 96.8 % | 97.0 % | 96.5 % |
| the dais's doorway frame, the stairwell's t65c02 treads | 96.9 % | 97.0 % | 96.7 % |
| end (folding leaves, closets, new binary: leaves 2 back from the wall) | **96.9 %** | 97.0 % | 96.6 % |

Sector 27 (the long maze passage) 0.959 to 0.980, sector 1 0.967 to 0.972; nothing else moved by more than 0.003.
The closets' new surfaces are not measured (the measure leaves out what is shut at the start). Rooms reached and
`solve`: as in round five (84 of 86 sectors on foot, the two niches reached into; the original's order).
`compare.py`: unchanged in kind.

### Playtest, and the failure one run in four

**Passes, 252 of 252 steps, sixteen runs of sixteen on this round's builds** (`run/play_r6_a1..4` at the start,
`_b1..4` and `_c1..4` after the door, chest and event changes, `_d1..4` on the end build with the new binary).

The lead's check this morning failed once in four at step 175 ("the Idol of the Snake from chest 19 was not taken"),
with the walk of round five (yaml line 335, no discards). Cause, found by running that walk 26 times with the
gameplay trace (`r6/diag_pack.yml`, `r6/diag_lane.sh`, `r6/diagt_lane.sh`; logs `r6/diag_L*`, `r6/diagt_T*`):
**the scenario's new game has a party of one** (`party()` lists only Ariel), so every item of chests 0 and 1 goes
into one pack of 14 by 9 cells, and the idol needs a free block of 2 by 4 (item298, 72 by 127 pixels). In 2 runs of
26 (L3 run 3, T2 run 5) the random items left no such block: the trace shows chest 2 (the rebuild's number of chest
19) opened with the idol and no `item_received` for it, 37 items in the pack. A party of one holds 12 idols at most
(`r6/idol_fit2.yml`). The chest itself is not random (its record holds the idol alone, no trap until this round, no
random roll). The lead's discards before each chest (07:28, kept) remove the dependence without weakening a check:
every item the walk asserts is kept, and after the discards the pack holds the 18 starting items and at most three
quest items. Monsters (serpent men, couatls) neither steal nor destroy items; clear_hostiles on the walks was not the
cause.

### What changed

1. **Door leaves as the original's** (`door_pics.py` read each leaf of the original and which side faces the opening's
   `from` room): the 42 maze plugs show `t65a05bl | t65a05br` toward their hall and tiled `t6502` rock behind
   (`pictures`, `tile`); door 1 `t65a05al | t65a05ar`; door 5 `t65b05l | t65b05r` west and `t65a05bl | t65a05br` east
   (`back_pictures`); doors 108 and 109 `t65a05bl | t65a05br` on both sides; the rock leaves (the four alcove slabs,
   doors 3, 4, 6, 114) tile at their size instead of one picture stretched over the leaf.
2. **Folding leaves**: every door but 6 is `fold: true` with `travel` the opening's height less 1 (the original's
   leaves shrink against their lintel; door 115 folds 127 of 128). The niche panel no longer slides up into a wall
   that has no room for it (it stood visible over the band above the niche when open), and the alcove slabs no longer
   leave their underside in the alcoves' ceiling plane. Door 6 sinks 254 of 255 (its top was in the floor's plane).
3. **Secret doors**: doors 3, 4, 6 and 114 carry the secret bit, as the original's faces do (attribute 0x2: they
   pulse red for a party with Perception).
4. **Chests**: every chest is trapped (`trap_level: 1`; the original's records all have flags 1); chests 0 to 5 roll
   each item at the original's own level (`random_levels`, e.g. chest 0 [4, 3, 2, 1, 1]); the six stone chests have
   the original's `t6502b` lid (`top_surface`).
5. **Surfaces**: door 1's corridor (`room:c22n`, `c22s`) under the maze's `t65a04c` ceiling (theme `maze_entry`);
   the 24 maze closets as the original's (theme `closet`: `t65b02a1` sides, `t65c02` back wall, `t65a04a` ceiling,
   `t65a03` floor; they had the halls' carved `t65a01`); the tunnel's doorway behind the dais framed by `t65o10` jambs
   and a `t65o12r | t65o11a | t65o12l` lintel band (`walls[].panels`); the stairwell's treads `t65c02` (theme `well`).
6. **Events**: 6 and 10 run on leaving the map (`trigger: leave`; `ph:simon` gone, the map has no placeholder left);
   62, 63 and 64 by side (`side`): door 108's outer face opens it, the inner faces of both doors run the trap
   (`evt:crusher_trap`, `evt:crusher_trap_w`), door 109's outer face opens it with the hint "Leave the Abandoned
   Temple". The built faces carry the events exactly as the original's do (checked on the export).

### Events against the original's (`oymap flow` of both)

Same as round five's table except: **6 and 10 now the same** (leaving with the books sets quest bits 218 and 136 and
clears 135 in both maps: `r6/leave_orig.yml`, `r6/leave_rebuilt.yml`, both pass with the same bits before and after);
**62, 63 and 64 now the same** (per side). Still differ: 11 (door 1's leaves change to `t65a05bl`/`t65a05br` when it
opens: a door's pictures have no cog), 102 to 109 (a panel goes out once a run; the original's second press relights
it), 451 (SetFacetBit(15, 2, 1): after the third fall the walkway's faces become secret and pulse: no word). Of the
94 handlers that stand for something: 84 same, 10 differ (11, 102 to 109, 451), none missing (round five: 80, 12, 2).

### What the player sees: differences per interactive thing

Pictures: `output/studio_cal/mm8_d05/ingame_r6/sheets/` (56 places, each original left and rebuild right, before
above and after every thing was used once below; the after state is a save written by `r6/after_*.yml` and loaded
under the same tour), `ingame_r6/arrival/sheets/` (the arrival and the box's top; doors half open),
`ingame_r6/end/sheets/` and `ingame_r6/fold/`, `fold_half/` (this round's changes, shut, open and half open),
`ingame_r6/things_original/` and `things_rebuilt/` (the lead's `things_shots.py` on both maps on the end build:
244 and 249 pictures, each thing before, used and used again), paired thing by thing in
`ingame_r6/things_pairs/page_01.jpg` to `page_11.jpg` (`r6/things_pairs.py`; original left, rebuild right). In the
things pictures the doors open and stay open alike in both maps; monsters and their spells crowd many frames (the
tool runs the game live), and where the rebuild splits one original event over two doors (63) the camera stands at
the other door. `oymap things`: 89 events in the original, 90 here (43 buttons, 7 chests, 19 panels, 3 switches,
2 exits in both; doors 15 against 16, event 63 being two). The tool `r6/pics.py` takes the sheets.

Fixed this round (seen before and after in the game):
- door 5 (both sides), door 1, the maze plugs, doors 108 and 109: the whole carved picture instead of its left half
  stretched (`sheets/12`, `13`, `20`, `30`; `end/03`, `06`; `arrival/07` to `09` half open);
- rock leaves (alcove slabs, closets, door 6, door 1's back, door 114): grain at the original's size;
- the niche panel (door 115) folds away instead of standing over the band above the niche (`sheets/25`, `end/08`);
- door 6's sunk top no longer lies in the floor's plane; the alcove slabs no longer leave a band in the alcove's
  ceiling plane (`fold/`);
- doors 3, 4, 6, 114 pulse red as the original's (`end/01`, `04`);
- door 1's corridor ceiling, the 24 closets' walls, the dais's doorway frame, the stairwell treads;
- chests trapped, rolled at the original's levels, stone chests with their lid.

Alike already (looked at, both states): the six stones (up, and sunk after use), the alcoves and their step buttons,
the trap room (plates out; drawn back, panels lit, four put out dark), the 46 maze buttons (crops
`ingame_r6/view/buttons_crop.jpg`: the original's form, 32 by 16 by 32, `t65a13a` face, `t65b04` sides, pushed 16),
the fire stand, the great hall's heads, hall 8 from its door and from below, the arrival view from the recess, the
back exit, the cave's stand.

Waiting on the studio's five (not worked round):
- lever handles: this map has none (its 46 maze buttons and 4 step buttons are blocks, built as movers of that
  form; its 8 panels are flat plates, `kind: plate`, as the original's `t65b11b` faces are. The new `kind: button` was not used for the 46 maze buttons: they are movers of the measured form already, 32 by 16 by 32, `t65a13a` face, `t65b04` sides, pushed 16, each moving its partner and its doors as the original's door records do);
- a toggling switch's picture: the 8 trap panels (events 102 to 109) toggle in the original (a second press relights
  a panel and lowers the count, map variable 12). The new binary turns a plate back when its event toggles, but the
  panels' toggle holds only while the trap runs (`map_var trap`); with `else_effects` the "back" branch would also run
  before the trap (and light the panel). Wanted: a toggle under a guard (`condition` for the event, `toggle` for the
  picture). Not changed;
- chest faces end-middle-end: the original's chests here are not of a kit: chests 0 and 1 are stone blocks 112 by
  128 and 96 high whose carved `T65b13` front leans back 16 and shows the texture's rows 32 to 128, with a top of an
  8-wide `T65B04` rim round a `T6502B` lid (faces 1745, 1781 to 1784, 1790; 1794 to 1798, 1804); the four corner
  chests of hall 8 are tapered blocks 128 square with `T65b13` on the two sides facing into the hall and `T65B04` on
  the two wall sides (faces 1877 to 1890, 1891 to 1904, 1863 to 1876, 1905 to 1918); chest 19 is a `cr_W128b`
  picture with `gt002d` on the niche's back wall (faces 3864 to 3867, 3872). The rebuild's chests carry `t65b13` low
  in their front (no vertical offset for a chest's surface), on two opposite sides only (one `surface`, one
  `end_surface`), with upright sides (`sheets/10`, `18`, `19`; `end/02`, `05`);
- things over moving parts: nothing stands on this map's movers but the party (the stones), which rides them;
- faces in one plane: `oymap audit` lists 14 `geometry.coplanar` (15 before door 6's travel), all in the tower: the
  box's beams against the lantern's walls (faces 1351, 1375, 1389 of sector 64 against 2614 to 2618 of 82), the box's
  top platform under the lantern's floor rim at 2432 (1916 against 2619, 2621, 2622), the north flight's side beams
  against its foot (1536, 1538, 1539, 1541 against 1881, 1882, 1884, 1886) and two beams of the box (1651/1773,
  1876/1916).

Other studio gaps (most harmful first):
1. **The box's top in the tower shows black** (`arrival/sheets/03-box-top-north.png`, `04`, `05`): standing on the
   box's top platform at 2432, where the walk goes right after the arrival, the view is black in every horizontal
   direction but for the floor and a raking beam. The platform (face 1916) is in the pyramid hall's sector (64) and
   the party's eye is above that room's flat top (2432), inside the lantern (sector 82), so the game draws from a
   sector the eye is not in. The original has box and lantern in one sector (15). From the recess (2464, the lantern's
   own floor) and from the box floor looking up the views match (`arrival/01`, `06`). Wanted: a room whose floor hole
   lets the party stand with its eye above the hole's plane must put that floor into the upper room's sector (or the
   build must refuse a walkable floor within eye height below a floor hole).
2. **Secret faces that are not doors**: the original marks the floor plates of the four heads and the fire stand
   (faces 1296, 1301, 1305, 1309, 1312, 1314, 1316 to 1323, 1325, 1326, 1342, 1343, and 1315 of event 453; 1324,
   3629, 3630 without an event) and 22 faces of hall 8's ceiling at -32 (`T65A04`, faces 1811 to 1814, 1817, 1819,
   1825 to 1829, 1831, 1838, 1839, 1841 to 1843, 1852 to 1856: the walkway's path traced on the ceiling, a clue that
   pulses for a perceptive party) with attribute 0x2. `secret` exists for doors only. Wanted: `secret` on plates,
   floor and ceiling regions (`floor_surfaces`/`ceiling_surfaces` entries) and panels.
3. **`secret` on one face of a leaf**: the original flags only door 6's north face, doors 3's and 4's corridor faces
   (1756, 1759) and door 114's south face; `secret: true` flags the whole leaf, so the sunk top of door 6 pulses at the
   floor and the closets' doors pulse from inside.
4. **A face changed by an event on a door or a platform**: door 1's leaves to `t65a05bl`/`t65a05br` on opening
   (event 11, cogs 10 and 11); the walkway's faces made secret by event 451 (cog 15). Doors and platforms get no cog.
5. **The wall's carving under the niche restarts out of line** (`sheets/25-niche-wall.png`, `end/08`): the hall's
   `t65a01` under the niche opening (10304 to 10432, -640 to -512) is a face of its own whose texture does not continue
   the wall's; the original's band runs through.
6. **A door's place in a deep doorway**: door 108's leaf is flush with the corridor's end in the original (5936 to
   6000 in a doorway 5936 to 6016); here centred (5944 to 6008), so its reveal shows as a frame from the corridor
   (`arrival/09`). No field places a leaf in its doorway.
7. Unchanged from round five: a funnel over an upright shaft (sector 21), a block on a bank's foot, a mover's
   half-unit middle at a high wall, a raking beam with a level top, a step higher than 40, the tunnel's rough rock.

### Refused or misread

Nothing new was refused this round. `pictures` with `fold` on slide_up leaves, `tile`, `back_pictures`, `secret`,
`side`, `trigger: leave`, `random_levels`, `trap_level` and `top_surface` on chests worked as described.

### Tool defects

- `oymap compare`: still counts the false floor seen from below against the rebuild (sector 8) and the original's door
  faces in the maze passages (sector 27: `t65a05bl` against `t65a01`, 52 rays).
- `ingame_compare.py`/screenshot tours freeze the game, so a thing cannot be pictured after use within a tour; done
  here with a scenario that uses everything and `save_game: {path}`, loaded by `run_game.sh --save` under the same
  tour (`r6/pics.py`, `PICS_SAVE_TAG`). A save of a rebuilt map loses its state when the map is rebuilt (the saves
  were written again after each build).
- The scenario's `new_game_flow` party is one character; a walk that loots chests depends on one pack's room. Worth a
  line in the scenario docs, or a party of four.
- `oymap audit` (this binary): door 6's coplanar warning named the door by its lock number (34), not its id.
