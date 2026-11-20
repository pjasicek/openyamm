# Gharik's Forge (MM6 `6d18.blv`) rebuilt as a Map Studio project: notes

Rebuild by [REBUILD_PROCEDURE.md](../../../REBUILD_PROCEDURE.md), 2026-11-12. The map was chosen for lava and
mechanisms. Project id `cal6d18`, map row 9716 (`reference: 6d18.blv`). Scratch data, pictures and the tools that wrote
the files are in `output/studio_cal/mm6_6d18/` (`gen.py` writes the four project files from measured tables,
`play.py` writes `playtest.yml`, `run_play.sh` builds, installs and plays).

## Where it stands

| Round | What changed | `oymap compare` score | distances | textures | points without a floor |
|---|---|---|---|---|---|
| 1 | first complete build (60 rooms) | 76.1 % | 90.9 % | 88.7 % | 90 of 577 |
| 2 | free blocks and flights widened to the original's edge lines; lift tops made flush | 90.3 % | 93.0 % | 90.4 % | 12 |
| 3 | entrance landing split in two, tower corridor moved 8 (wrong pair of walls, see defects) | 90.5 % | 93.2 % | 90.6 % | 12 |
| 4 | lava cavern narrowed to its real walls, channel hall edges, tile block | 91.5 % | 94.6 % | 90.7 % | 12 |
| 5 | lava as a level inside a stone ledge so that steps are not lava: **thrown away** (91.4 %, textures 90.3 %) | | | | |
| final | bookcase as a chest, fire-resistance wall | **91.5 %** | **94.6 %** | **90.7 %** | 12 |

- With `--step 200` (points off the original's 256 grid) the final build scores 93.0 % (distances 95.1 %, textures
  90.2 %). The 12 points still "without a floor" all lie exactly on a wall or door line of the original.
- `compare.py`: round 1 `18 in, 13 near, 4 out`; final `18 in, 12 near, 5 out`. The five: smallest sector floor (my
  gate lobbies), median sector height (the original's sector boxes include its door slots), doorway width minimum
  (the original's closed doors have portals 1 unit high), doorway width maximum (the original splits the machine
  room in two sectors with a 2,304 portal), sectors reached with doors clear (45 against 22, see the solver below).
- Rooms: 61 (47 sectors in the original). `oymap solve`: 6 sectors at the start (the original 5; the entrance
  landing is two rooms here), then 7, 9, 10, 30, 37, 39, 41, 45 of 61 in nine steps, in the original's order (split
  door, bridge lever, gallery, machine room, north-east ring). It stops at the lift, which it cannot ride; the
  original's own solve stops earlier, at the sliding bridge (22 of 47).
- **The playtest passes**: `playtest.yml`, 237 steps in one run from a new game, walks the whole critical path in the
  game and uses every mechanism on it: the bridge and both turns of the tower ramp, the split door, the lever and
  the lava-hall bridge, the gallery walkway, three lever doors, the machine room (west bridge, four levers on both
  storeys, gates 51, 49, 52, the bridge swap, east bridge, gate 48), the ring's four lever doors, the lift (ten
  seconds, 2,024 down, position asserted), the laboratory door refused without the key and opened with it, the
  channel hall's bridge, three turns of the stair tower, the cavern walkway, the last door and the hourglass chest
  (qbit 1029 and item 2053 asserted). Monsters within 2,500 are killed on the way.
- In-game pictures, 12 same-camera pairs (`output/studio_cal/mm6_6d18/ingame_final/diff`): edge agreement 0.78,
  blurred difference 0.061. The lava river, the channel hall and the laboratory are close to indistinguishable;
  the machine room (no posts or rails, lower balconies moved) and the tower (steps for ramps, lava-red treads) are
  the least alike.

## The lava: how the original does it

- **Faces.** Eight sectors have floor faces textured `OrFyrLgA` (3, 5, 9, 16, 17, 34, 36, 39; 31 faces, about 21
  million square units). Their attributes are `0x84000110`: `0x10` (fluid: the texture flows), `0x04000000`
  (triggered by stepping on it) and event 51.
- **Events.** Event 51 sets map variable 2 to 1. The dry floors beside the lava (65 faces: islands, the river's
  banks, the channel hall's floors) carry the same step flag with event 53, which sets it to 0, as do event 52 (on
  load) and every escape teleport. Event 54 is a timer, every two half-minutes: if map variable 2 is at least 1,
  `DamagePlayer(all, magic, 25)`. So the lava does nothing by itself; it burns the whole party for 25 once a minute
  for as long as the last step trigger crossed was lava. OpenYAMM overrides this with `6d18_1.scene.yml`: the lava
  faces get the engine's Lava flag (`0x40000000`) and lose the step trigger, so they burn every second and Levitate
  protects.
- **Crossing and avoiding.** The party never has to touch it. Every lava room is crossed above the lava: a ramp round
  the walls (tower), a bridge the party must extend (first hall) or move (machine room), a fixed walkway (gallery,
  cavern), a fixed bridge and banks 20 above the lava (channel hall, river). A party that falls finds a dry island
  or recess with a tile `OrFyr64B` (events 31, 32, 41, 42, 43, clicked) that puts it back on the way; the cavern's
  sends it to the lower floor instead.
- **Fountains.** Timers 56 to 61, every half-minute, each throw one of four to six things at random from fixed
  points just above the lava of one room: fireballs (object 1050) or gold (object 1000).
- **In the rebuild** the lava is only the floor texture: the room's floor is the lava and everything walked on is a
  level or a free block (a platform with a `base`). No flag, no damage, no fountains. See gaps 1 and 3.

## The mechanisms, case by case (the original's 53 door records and 63 handlers)

| Original | What it is | Can the vocabulary say it? | Said with / field that would say it |
|---|---|---|---|
| Events 4-7, 9-12, 14, 17-21: doors 5/6 ... 39/40 (14 pairs) | A lever (the odd record: a 16-unit plate that sinks) lifts a door 128 by 256 in a wall 32 thick, for good | **Yes** | `doors` `kind: slide_up` in an opening, `switches`, wiring `preset: switch`, `opens` |
| Event 55 on those doors | "The Door won't budge." | **Yes** | `preset: text`, `source` the door |
| Event 16, doors 29/30 | The same, locked: key 2107 or qbit 1400, or qbit 1035 without 1223; takes the key, sets 1400, clears 1223 | **Yes** | `condition: {any: [...]}` with `item`, `qbit`, `not`; `effects` `take_item`, `qbit`, `clear_qbit`; `locked_text` |
| Events 2 and 13, doors 1/2 and 23/24 | A doorway 256 square closed by two halves one above the other; the lower slides 255 north into the wall, the upper south, when clicked | **No** (one lifting leaf, 224 wide) | a door `kind` that slides sideways, and `leaves` |
| Event 3, doors 3/4 | Lever; the end face of a bridge stub moves 959 north: the bridge (256 wide, top -16) stretches across the first lava hall | **No** (a lift of the same plan rising 744 out of the lava) | a moving block with a `travel` vector (x, y, z), or `kind: extend` |
| Event 8, doors 13/14 (+ opens 49) | Lever on the lower south-east balcony; the bridge of the machine room (992 long, with kerbs and posts, 73 vertices) slides 1,280 east from the west pair of balconies to the east pair, for good | **No** (two lifts, west up and east down, swapped by `closes` and `opens`: the same connections) | the same horizontal `travel`; a mover that carries the party |
| Event 15, doors 27/28 | Lever at the top and at the foot; the lift floor (256 by 240) travels 2,032 at 200 a second | **Yes**, nearly | `lifts` with `state: up`, `travel`, `speed`; `preset: switch` `toggles`. The lift is a solid block from the shaft floor, not a floor 16 thick |
| Events 33, 34, 36, 38, 39, 40; doors 48-52 | Levers on six balconies toggle five gates 256 by 240 (48 and 50 hang open in the lintel, 49, 51, 52 start shut) | **Yes**, with two losses | `doors` `slide_up` with `state`, `toggles`. A door needs 16 of wall each side (224, not the lobby's whole 256); the lower gates stand 288 from under the upper ones (gap 4) |
| Event 35, door 53 and face 2255 | Lever makes the "lava wall" of the chest alcove vanish (the door record has no vertices; OpenYAMM sets the face invisible and untouchable) | **Nearly** (a lifting door in the alcove's neck) | a door `kind: vanish` |
| Events 31, 41, 42, 43 | Clicked tiles that teleport within the map | **Only through Lua** | `preset: teleport` exists but takes no source in a new map (defect 4); `preset: switch` with `lua: evt.MoveToMap(...)`. Three of the four are floor tiles; here wall plates above the islands |
| Event 32 | The same on the tower's island, in the middle of the room | **No** (placeholder) | a switch that lies on a floor or a block (`at`), not on a wall |
| Events 51-54 | The lava (above) | **No** | gaps 1 and 3 |
| Timers 56-61 | The fountains (above) | **No** | an event with `every: <seconds>` and no source; an effect that throws an object |
| Events 44-47, 49, 50 | Chests | **Yes** | `chests`, `preset: chest` |
| Event 48 | Chest 5 (the Hourglass of Time, sets qbits 1029 and 1207) the first time, chest 8 for a party that already has the bit | **Half** (one chest with the item and the two qbits as `effects`) | a chest preset with alternatives by `condition` |
| Event 62 | Bookcase: up to four searches, each one scroll of six at random | **Half** (a chest in the bookcase's shape holding four of them) | an effect that gives one of a list, a `times` limit |
| Event 91 | A wall face gives +25 fire resistance once | **Only through Lua** | `preset: switch` with `lua` |
| Events 1, 22-26, 29, 30 | Bound to nothing in the original | not built | |

## Gaps, most harmful first

1. **A floor that is a liquid or a hazard.** All eight lava rooms. Nothing marks a floor as lava (the engine's Lava
   face flag), nothing gives a surface a flow, and nothing says what standing on it does. Done instead: the texture.
   Field: `floor_kind: lava` (or `liquid: lava`) on a room and on a level, lowered to the face flags.
2. **A part that moves sideways and carries the party.** The first lava hall's bridge (stretches 959) and the
   machine room's bridge (slides 1,280 with its kerbs). Done instead: lifts that rise out of the lava (three). They
   look wrong moving and stand as solid blocks from the lava up. Field: `travel: [x, y, z]` on a mover, and a
   mover's own shape (kerbs, posts).
3. **An event without a clicked source.** Stepping on a floor (events 51 and 53, 96 faces), a timer (54, 56 to 61),
   on load (52). Every preset demands a `source` that is a door, switch, lift, chest or exit. Field: `trigger:
   step` with a room or level as source, `every: seconds`, `on: load`.
4. **Two openings one above the other in one wall.** The machine room's north and south walls, four places: a
   balcony at 0 and one at -512 straight below it each have a doorway. The build refuses ("two openings in one wall
   overlap or stand closer than 16 units") whatever their heights. Done instead: the four lower balconies, their
   levers, gates and passages stand 288 nearer the middle. Field: none needed; the check should compare heights.
5. **A flight cannot say which block it ends on, and there is no sloping free block.** The tower (16 ramps in two
   turns) and the stair tower (12 ramps in three turns) are ramps that hang free, one above another. A flight's end
   is a point, and the build takes the level, block or step listed last there. Done instead: steps for ramps;
   landings of different sizes per turn so that each end finds its own; on the tower's east wall, where three ramps
   overlap, flights 74 and 54 wide side by side; the stair tower's top landing cut to a strip 36 deep. Fields:
   `from_block`/`to_block` (or a height) on a flight; `slope` on a platform.
6. **A flight's treads have no surface.** They take the room's floor, which in a lava room is the lava: every step of
   the tower ramp and of the channel hall's bridge and ramps is red lava (pictures 01, 02, 08). A take with the lava
   as a sunken level inside a stone ledge fixed the look and was thrown away: it invents a ledge 192 wide (round 5).
   Field: `tread` beside `riser`.
7. **An opening cannot say which walls it joins.** The build takes the pair of facing walls with the longest shared
   stretch within 512, silently. It took the wrong pair for the L-shaped entrance landing (door cut through 384 of
   rock; the first playtest could not leave the room) and the tower corridor, and by the same rule would have for
   rooms 7, 12, 26/27, 33, 38/39, 43, 44 and 45. Done instead: rooms split into a room and a lobby (seven lobbies), edges moved 8 to be 520 apart, the
   loop of 25/26/27 made one room with a pillar. Field: `from_wall`, `to_wall`.
8. **Kerbs, rails and posts on free blocks.** The gallery walkway's kerbs (21 wide, 64 high), the machine room's
   bridge rails and corner posts. `parapets` stand on the room's floor or a level only. Not drawn.
9. **A block against a slanted wall.** The tower's eight corner landings follow two walls and a diagonal; a block with
   an `outline` must keep 32 clear of the walls, so they are turned rectangles with square ends.
10. **A door as wide as its passage, and a lift as thin as a floor.** The five gates are 224 where the original's
    fill 256; the lift is a solid block 2,024 high where the original is a floor 16 thick.
11. **A strip of another texture at the ends of a wall.** Every corner of the eight-sided rooms (10, 14, 20, 23) and
    of rooms 1 and 29 has a `D8wlBLE` strip 24 to 32 wide: the largest texture miss (about 400 rays). `walls` gives
    one surface per wall. Field: a wall panel with `offset` and `length`.
12. **Ceilings that slope.** Rooms 10, 14 and 23 rise from the walls to a flat middle; room 42 from -512 to -384.
    Done instead: a raised panel, or flat.
13. **A floor that runs on under a wall.** The lava of rooms 3 and 39 continues 128 to 256 under the end walls
    through a slot 64 high. Not drawn.
14. **Spawns and items.** A spawn takes a slot 1 to 3; the original's indices 4 to 12 choose the slot's weaker or
    stronger kind (the laboratory's warlocks are sorcerers here). The 17 item spawns are placeholders. A chest
    cannot be empty of random items or be one of two.
15. **A level between other levels from wall to wall.** In the channel hall a lava level touching both end walls
    between the bank levels "cannot be cut out of the room"; only a strip 8 clear of everything builds.
16. **Two rooms in one space.** The original's hall 14 stands 128 inside the stair passage 46 (never seen together).
    The hall ends at x 864 here. Not a wish, a note.

## Tool defects

1. **`oymap solve` does not follow floors that move.** `oymap solve 6d18.blv --world mm6 --assets assets_dev` stops
   at 22 of 47 sectors, before the sliding bridge; `oymap solve devdocs/map_studio/briefs/mm6_6d18/L4 --assets
   assets_dev` stops at 45 of 61, before the lift (the game rides it: playtest). It also counts every lever of a
   sector as usable once the sector is entered (step 5 lists the levers of all eight balconies at once).
2. **An opening is cut in the wrong walls without a word** (gap 7). With the entrance landing as one L-shaped room,
   `oymap validate` had no issues and `oymap audit --reach` reached the tower, while the built map had a solid wall
   across the arm and the portal on the leg (faces at x -2176; `oymap export <L4>/build/cal6d18.blv`). A check:
   warn when another pair of facing walls is as long or touches.
3. **`oymap probe` reports a step that is not there** at the last sample when floors lie over one another:
   `oymap probe 6d18.blv --world mm6 --assets assets_dev --from 1920,5250,0 --to 1920,6600,0` says "a step is too
   high at sample 675 of 675, step 768" (the balcony over the lava) while its planner finds the route.
4. **`teleport` and `script` presets take no source in a new project.** `wiring.yml: a teleport preset cannot have
   the switch switch:tile43 as its source`; `core/IndoorLowering.cpp` accepts sources only for door, switch, chest,
   exit and text. The schema describes both presets without saying so.
5. **A flight's end finds the region listed last** (levels after blocks, earlier flights' steps after both), and the
   message names only two heights: "a flight runs from a point on the lower floor ... (here 1024 to 576)". Say which
   block, level or step each end found.
6. **Blocks are not checked against the walls.** A rectangular block is tested at its centre only: a chest of size
   [638, 126, 256] with `facing: n` against a south wall validated and built with 250 of it outside the room
   (`compare` found it: 91.2 %). A block with an `outline` is refused within 32 of a wall with "the block does not
   stand inside room:x with its whole footprint", and the schema states the 32 only for rock islands.
7. **A lift's top is 8 above `floor + travel`** (the block is 8 thick when down), where the schema says "level with
   the floor; raised it stands `travel` higher". And a gap of 2 between a lift and the next block stops the walk
   check ("blocked by a face"); the lifts here overlap the balconies by 1.
8. **`oymap compare` stands on the original's own 256 grid**, so in a map drawn on that grid many points lie exactly
   on walls, door lines and slab edges: 90 of 577 had "no floor" in round 1 because blocks stand 1 unit clear of
   edges, and the last 12 are all on wall or door lines. `--step 200` gives 93.0 % against 91.5 % for the same build.
   An offset of half a step would do.
9. **`oymap install <L4> --mount ...` reads only `<L4>/build`** ("build the project first") though `oymap build
   --out` writes elsewhere; the build folder therefore lies in the brief.
10. **`oymap export` writes no door records** (the procedure promises them); they are only in the map's
    `.scene.yml`.
11. **`compare.py`'s original metrics** count a closed door's portal (1 unit high) as a doorway 1 wide
    (`scale.doorway_width.min 1`).
12. Scenario runner, not the studio: `walk_to` with `clear_hostiles: true` is accepted and kills nothing; it wants a
    radius.

## What I was unsure of in the original

- Which pose of a door record is "closed". Taken from `oymap probe` on the original (door 1, gates 49, 51, 52, the
  lava wall and the lift block; gates 48 and 50 do not) and from the solve, not from the state numbers.
- The tiles' flag `0x02000000` is read as "clicked"; they may be stepped on in the original engine.
- Event 62 is also bound to a ceiling face of the crystal room (face 2481). Not understood, not built.
- Chest contents were not read, except chest 5's first item (2053, from the scene's raw bytes). Chests here roll
  three items of level 4.
- Whether a `6torch01` decoration lights by itself: both the 83 torches and the 83 light records are placed.
- The teleports' directions (502, 1550, 896 of 2,048) are passed on raw in the Lua.
- The wall trim `CTTRIM2` of the cavern and the channel hall (about 100 rays) was not placed: I did not measure its
  band heights.

## Round two (2026-11-12, later the same day)

The project files were edited by hand in this round; the scripts in `gen/` no longer reproduce them. Scratch data,
measuring scripts (`q.py`, `secinfo.py`, `bq.py`, `rep.py`), the check loop (`check.sh`) and the playtest runner
(`play.sh`) are in `output/studio_cal/mm6_6d18/r2/`; the comparison is `output/studio_cal/mm6_6d18/compare_r2/`.

### Scores

| | `oymap compare` | distances | textures | points without a floor | rooms | `solve` |
|---|---|---|---|---|---|---|
| start of round two | 93.2 % | 94.7 % | 90.6 % | 2 of 554 | 61 | stops at 45 of 61 (before the lift) |
| lower balconies back under the upper ones | 93.8 % | 95.5 % | 91.1 % | 2 | 61 | 61 of 61 |
| stair tower's first turn solid | 94.3 % | 96.0 % | 91.6 % | 2 | 61 | |
| leaning ceilings of 10, 14, 23; hall 14's true outline | 95.2 % | 97.1 % | 91.9 % | 2 | 61 | |
| lobbies undone, laboratory ceiling, riser textures, kerbs | **95.4 %** | **97.3 %** | **92.2 %** | 2 | 57 | **57 of 57 in 16 steps** |

- With `--step 200`: 96.2 % (distances 97.9 %, textures 92.2 %; no point without a floor).
- `compare.py`: `18 in, 11 near, 6 out` (the six are the same kinds as before plus the reached-sector and
  walkable-area figures, which now exceed the original's because its own solve stops at the sliding bridge).
- `oymap audit --reach`: 57 of 57 rooms. `oymap validate`: no issues.
- **The playtest passes**: 256 steps (the 237 of round one, with the lower-balcony legs moved, and 19 new ones at
  the start for the lava, below).
- In-game pairs at the changed places (`output/studio_cal/mm6_6d18/ingame_r2/diff`, 11 pairs): edge agreement
  0.79, blurred difference 0.061. Halls 14 and 23, the laboratory and the stair tower are close; the two views
  from the lower balconies are the least alike (0.57 and 0.54): the lift that stands for the sliding bridge is a
  solid block from the lava to the bridge's height right beside them, with its texture stretched over the whole side.

### What changed

- **Lava** (gaps 1 and 3 of round one, closed). `objects.yml` `floors`: the seven lava rooms' own floors are
  `kind: lava` (the built faces carry `0x40000000`). `wiring.yml`: variable `on_lava` (map variable 0); `evt:lava_on`
  (step, the seven lava rooms: original event 51), `evt:lava_off` (step, the four islands, the channel hall's two
  floors and four banks, the river's two banks, the cavern's recess: event 53), `evt:lava_load` (load: 52),
  `evt:lava_burn` (timer every 2, condition `on_lava`, 25 magic damage to all: 54), and the six fountains
  (`evt:fountain_*`, timers every 1 with the original's points; Lua, because no effect throws an object).
  **Both mechanisms are on**: the engine's lava flag burns every second and the original's timer burns 25 once a
  minute on top. OpenYAMM's own override of the shipped map keeps only the flag; a rebuild that wanted the same
  would drop `evt:lava_burn`.
- **Escape tiles**: the four wall plates use `preset: teleport` with a switch source (no Lua). The tower's raised
  tile (event 32, placeholder in round one) is a platform with an `id` and a `trigger: step` teleport: stepping on
  it puts the party back at the start. The original tile is clicked.
- **Machine room**: the four lower balconies, their passages, gates and levers stand straight under the upper ones
  again (two openings one above another in one wall build).
- **Sloped ceilings**: rooms 10, 14 and 23 have a whole-ceiling level with `top_outline` (the eight walls lean in
  to the measured flat panel). The laboratory (42) is three rooms joined by open mouths (neck, widening part with
  `ceiling_slope`, hall), because its ceiling is level, then sloping, then level. The lower stair (47) has a raking
  ceiling over its steps.
- **Hall 14** has its true outline cut off flat at the stair passage's wall (x 896) instead of a squeezed octagon.
- **Lobbies undone** with `from_wall`/`to_wall`: the entrance landing is one L-shaped room; rooms 33, 43, 44 and 45
  are L- and comb-shaped rooms again (five lobbies gone); the three edges moved by 8 (rooms 2, 7, 12) and the
  passage narrowed by 8 (45) are back on the original's lines. Kept as rooms of their own: the pieces behind a
  gate (a door needs a room each side), the cavern's door neck and recess and the lift's foot (other floor or
  ceiling heights).
- **Stair tower**: the first turn stands on solid blocks from the floor, as in the original (its west and south
  ramps were hanging flights).
- **Tower**: the three flights along the east wall have the ramp's full width (`to_height`).
- **Gallery**: the walkway's kerbs are blocks standing on the slabs; the slabs have the original's full width.
- Stair risers `gset05` (rooms 46, 47 and the channel hall's bridge steps); the cavern recess's walls `ctwl2`.
- **The lift** stands flush with the door side of its shaft (y 2320 to 2560, the original's place).

### New features: what worked, what did not

Worked first time, as the schema says: `floors` `kind: lava`; `trigger: step` with rooms, levels (`id`) and a
platform (`id`) as sources, `sources`; `trigger: timer` with `every` and a `condition` on a map variable;
`trigger: load`; `effects` `damage`, `set` on a map variable; `preset: teleport` with a switch source and with
`trigger: step`; two openings one above another in one wall (four pairs, floors 512 apart, no `sill` needed);
`from_wall`/`to_wall` (thirteen openings, compass sides and edge numbers); whole-ceiling `ceiling_levels` with
`top_outline` over eight-sided rooms; `ceiling_slope` in a level room and over a stepped floor; `to_height` on
flights, and flights that overlap in plan at different heights; platforms against walls and platforms standing on
platforms (`base`); `slope.riser`. No build failed on a new feature, so there is no repro project.

Not used: `summon`, `cast` (the fountains throw objects, not spells or monsters), floor holes, raking beams,
plates (the original's step faces are whole floors).

Not in the binary (`openyamm-studio/build/oymap` of 17:43) though the gallery uses them:
`oymap validate openyamm-studio/examples/shapes_gallery --assets assets_dev` reports `rooms[9].walls[0].panels:
unknown key`, `rooms[9].walls[0].ends: unknown key` and `doors[1].back_surface: unknown key`. The corner strips
below wait for that.

### Why `solve` stopped before the shaft in round one

The lift block stood 8 short of the shaft's door wall (y 2312 to 2552 in a shaft that ends at 2560), so between
the door's threshold and the lift's top was a slot 8 wide open down to the shaft floor 2,032 below. The solver's
walk treats that as a drop and never steps onto the lift (the game's party strides over it: the round-one
playtest rode the lift). Moving the lift flush (its measured place) opened all 61 rooms. A check would help:
warn when a lift or platform leaves a slot narrower than the party between itself and a doorway it serves.
`oymap probe ... --doors-open` cannot show this: with the doors out of the way the lift is gone too and the
probe reports "a step is too high ... step 2024".

### Gaps still open, most harmful first

1. **A mover that slides sideways and carries the party, with its own shape** (round one's gap 2). The machine
   room's bridge and the first hall's bridge are still lifts: solid blocks from the lava up. They now cost the
   most in the machine room (sectors 16 and 17: about 6 of the 25 points lost), and they wall the lower
   balconies' view of each other.
2. **A sloping free slab, and a flight whose steps are slabs.** The tower (16 ramps) and the stair tower's upper
   two turns (8 ramps) are flights whose steps are solid down to the height the flight starts at, where the
   original is a slab 32 thick: a wedge of up to 128 hangs under every ramp (sectors 37 and 5: about 10 points).
3. **A flight's foot cannot name its floor** (`from_height`, the twin of `to_height`). Where landings lie one above
   another in the same plan (every corner of both towers), a flight's `from` takes the highest. So the upper
   landings stay smaller than the lower ones (tower 380 against 500, stair tower 130, 108, 86) and the stair
   tower's top landing stays a strip 36 deep, where all are the same size in the original.
4. **Surfaces of a flight's treads and of a block's underside.** Treads and the undersides of hanging steps take
   the room's floor (lava in the tower: red strips under every ramp in the pictures; `ctflor5` under the stair
   tower's wooden ramps); a hanging block's underside takes its `top_surface` (the balconies' `d2ceil1`
   undersides are `vlctrm3`). About 480 rays. Fields: `tread`, and `bottom_surface` on a platform.
5. **Corner strips and wall panels** (round one's gap 11; `ends` and `panels` are in the gallery but not in the
   binary used). `D8wlBLE` strips 24 to 32 wide at every corner of rooms 1, 10, 14, 20, 23, 29 and 42, `CTTRIM2`
   strips 64 wide in the corners of the cavern and the channel hall, `ctwl5LE`/`ctwl5RE` at door jambs: about 600
   rays, the largest texture loss.
6. **Two rooms in one space** (hall 14 and the stair passage 46): the hall is cut off 128 short; its east wall
   and two east corners are what `compare` still finds wrong there (sector 14: 1.8 points).
7. **A ceiling that is level, then sloping, then level** needs the room split (the laboratory, three rooms), and
   a slope with a level end cannot be said at all (the lower stair's ceiling: pitch 240 in 384 against 240 in
   352). A `top_outline` level stands on walls of one height, so over hall 14's cut-off wall the ceiling is
   steeper than the original's.
8. **A switch on a floor or a block** (the tower's tile is stepped on, not clicked; three tiles are wall plates
   where the original has floor tiles 64 square and 16 high), an **effect that throws an object** (fountains are
   Lua), and a step source that is a flight (the channel hall's two bank ramps carry event 53 in the original).
9. A platform inside a level stands on the room's floor, not on the level (the tower's tile needed `rise: 80` to
   stand 64 above its island); objects stand on the highest floor, platforms do not. The schema does not say.
10. Unchanged from round one: a floor that runs on under a wall (the lava slots of rooms 3 and 39), a door as
    wide as its passage, a lift as thin as a floor, posts and rails on a mover, the levers' posts on the balcony
    corners (levers are on the walls beside the balconies), spawn tiers, item spawns, the second hourglass chest,
    the bookcase's random scrolls, the fire-resistance wall (Lua).

### Tool defects seen in round two

1. `oymap compare`'s report holds only the 40 worst points; sectors scoring above about 0.9 have no points listed,
   so what they lose cannot be read (channel hall, cavern, tower). A `--points all` would do.
2. `oymap compare` still counts two points of sector 1 "without a floor" that lie exactly on a wall line
   (round one's defect 8): 2.2 of the 25 points lost.
3. `oymap probe` says "route found" for a route that ends short of the target: `oymap probe <L4> --assets
   assets_dev --from 4736,3000,0 --to 4736,2500,-16 --doors-open` ends at (4736, 2584, 0).
4. A flight's `sides` stand beside the flight from the height it starts at, outside its `width` (tested on a
   hanging flight in the stair tower and removed); the schema reads as if they flanked the steps inside the width.
5. Round one's defect 10 is fixed (`oymap export` lists door records) and so is defect 9 (`oymap install --build`).

## Round three (2026-11-12, night)

Edited by hand (the `gen/` scripts were not run). Scratch data, the measuring helpers (`doorfaces.py`, `facesin.py`,
`strips.py`, `strip_u.py`, `thresholds.py`, `switch_audit.py`, `rep.py`), the one-off insert scripts for the wall strips
(`add_strips.py`, `add_jambs.py`, `add_bxl.py`, `add_panels.py`, `add_panels_b.py`, `add_door_jambs.py`; each checked by
its diff), the start snapshot (`start/`), the check loop and the playtest runner are in
`output/studio_cal/mm6_6d18/r3/`. The comparison is `output/studio_cal/mm6_6d18/compare_r3/`.

### Scores

| | `oymap compare` (256 grid) | distances | textures | no floor | `--step 200` | distances | textures |
|---|---|---|---|---|---|---|---|
| start of round three | 95.4 % | 97.3 % | 92.2 % | 2 | 96.2 % | 97.9 % | 92.3 % |
| movers, sideways doors, full-width gates, treads | 96.2 % | 98.0 % | 94.4 % | 4 | | | |
| corner strips (`ends`, jamb `panels`) | 96.8 % | 98.0 % | 96.3 % | 4 | | | |
| balconies at their measured 256, lever posts | 96.1 % | 98.0 % | 96.3 % | 8 | 97.9 % | 98.9 % | 96.2 % |
| channel hall on its measured lines, banks under the bridge, pilasters | 95.8 % | 97.5 % | 96.4 % | 8 | 98.0 % | 98.9 % | 96.4 % |
| both towers' flights and blocks at their measured 128 | 91.6 % | 97.8 % | 96.9 % | 34 | 98.2 % | 99.0 % | 96.9 % |
| **end**: edge strips beside doors, thresholds, leaves 32 thick | **91.6 %** | **97.8 %** | **97.0 %** | 34 | **98.5 %** | **99.0 %** | **97.8 %** |

- **Why the 256-grid total fell.** Every one of the 34 points "without a floor" lies exactly on an edge of a slab, ramp
  or bridge of the original (x -2048 and y -512 in the tower, y -512 in the stair tower, x 256 on the first bridge,
  x 2048 and 3328 on the balconies). Round one had widened those blocks and flights by 2 to 4 units (balconies 260 for
  256, the channel bridge 788 by 260 for 768 by 256, flights 254, 132 and 126 for 256 and 128, levels at 4354/5118
  for 4352/5120, the stair tower's first turn 130 for 128) so that such points found a floor: a wrong shape that
  measured better. Round three put them back on the original's lines; that costs 4.2 points on the 256 grid and
  nothing on the offset grid, where distances rose from 98.9 to 99.0 %. The offset-grid figure is the one to read.
- `compare.py`: `20 in, 12 near, 3 out` (round two `18 in, 11 near, 6 out`). The three: smallest sector floor,
  median sector height, doorway width minimum (all as before).
- Rooms: 57. `oymap solve`: 5, 6, 8, 9, 25, 28 of 57 in five steps (split door, bridge lever, west corridor, gallery
  levers, machine room) and then it stops at the machine room's sliding bridge, as the original's own solve does (22
  of 47, at the same bridge). The cause is now known: the bridge stands 16 short of the balconies at both ends (as
  measured), and the solver's walk does not cross a 16 gap between two slabs at the same height (repro below). With
  the bridge drawn 1,022 long (touching, scratch copy only) the solve opens all 57 in 16 steps in the original's
  order. `oymap audit --reach` reports 29 unreached (tool defect 2 below). The game crosses both gaps (playtest).
- **The playtest passes**: 270 steps (round two's 256 and 14 new): the stretching bridge asserted retracted and then
  stretched; the machine bridge asserted at the west balconies, slid east after the lever (8 s for 1,280 at 200 a
  second), with its four posts; the party walks across both gaps at both places (positions asserted on the bridge);
  gates 50 and 48 (full width, starting open) toggled shut and open again; door 23 (sideways) opened and walked
  through into the chest room passage and back; door 1 (sideways) as before; the channel hall's moved doors.
  `oymap probe` confirms both sideways leaves block when shut and clear when open.
- In-game pairs (`output/studio_cal/mm6_6d18/ingame_r3`, `_r3b`, `_r3c`, `_r3d`; 26 pairs). Looked at: the machine
  bridge with its kerbs and moving posts reads almost as the original (0.71, the difference is the lever post's
  handle and lighting); the channel hall's pilasters and flush door are close (0.80; the door 16 off the pilaster);
  the corridor corner 0.99; the laboratory door's flanking columns now match on both sides (0.87); the towers' treads
  are the original's wood and stone. Two pictures are spoiled by things not mine: a monster in front of the stair
  tower camera, and a lava fountain's fireball in front of the gallery camera (`ingame_r3c/diff/01`).

### What changed

1. **Moving parts as the original's door records say** (`oymap export ... --world mm6 --assets` door list):
   - First lava hall (door 4): `movers` `mover:bridge3`, `stretch: true`, the stub 256 by 64 at the south wall,
     -128 to -16, `travel: [0, 959, 0]` at 200. The stub platform and the lift that rose out of the lava are gone.
   - Machine room (door 14): `mover:machine_bridge`, 256 by 992, -32 to 0, `kerbs: {height: 64, width: 16}`,
     `travel: [1280, 0, 0]` at 200, `bemvwal` all over as measured. Its four corner posts (64 by 16, deck to ceiling)
     are four more movers (`mover:machine_post_*`, 48 by 16 so as to stand clear of the kerbs) with the same travel,
     moved by the same lever. The two lifts that swapped are gone.
   - Doors 1/2 and 23/24: `kind: slide_left` / `slide_right` (the lower half's direction: north), `surface` and
     `back_surface` from the two faces of the original's leaves (`vlcwl1lg`/`vlcwl1` and `d2wlactr`), openings
     `width: full` (256, the lever room's and the chest passage's whole end; they had to be 224).
   - The five gates: openings `width: full` (256 as measured, were 224), leaves `vlcgnrc3` on both faces (were three
     wrong textures).
   - Every door leaf `thickness: 32` (the original's leaves fill the wall; the default was 16).
   - The lift: unchanged. Round one's note was wrong: the original's lift is a solid column too (only the four
     corners of its top move; its front face runs from the shaft floor to the top), so `thickness` is not wanted.
   - Play: neither bridge carries the party in the original's design (each lever is elsewhere: the lever room, the
     lower south-east balcony), so the game's rule that a level slide does not carry changes nothing here.
2. **Surfaces.** `tread` on all flights: `d2wlactr` in the tower (round two's lava-red steps), `bemvwal` in the stair
   tower, `ctflor4` in the channel hall; landing tops `top_surface` as measured. Corner strips: `ends` (room or
   wall) of `d8wlble` 32 (34, 36, 45, 27, 23 on slanted walls, as measured per wall) in rooms 1, 3, 7, 8, 10, 12, 14,
   16/17, 20, 23, 29, 42; `cttrim2` 64 in the cavern; jamb `panels` of `d8wlble` beside the machine room's eight
   balcony doorways (both storeys) and the first hall's mouths; `ctwl5LE/RE`, `vlcwl3LE/RE`, `D2WlCLE`,
   `d8wlbxL`, `vlcwl1LE/RE`, `ctwl2LE/RE`, `ctwl4LE/RE`, `D2WlALE/RE` strips at wall ends and beside doors in 27 more
   rooms (measured from the original's faces, including faces the original lists in its door records); one lobby
   wall wholly `vlcwl3re`. `threshold` on 22 openings with the original's doorway floor (`vlcflora`, `ctflor1`,
   `6voltyl`, `vlctrm3`, `ctflor5`, `ctflor2`, `vlcflore`; the rebuild had the wall texture there).
3. **Shapes on the original's lines.** The channel hall: levels, banks, bridge and stairs on the measured lines, the
   banks running on under the bridge (the stairs end on the bridge by `to_height`), and the four corner pilasters
   (64 square, `cttrim2`) as notches of the outline. The gallery's four corner pilasters (32 square) likewise. The
   tower's four lower corner landings have the original's six-sided shape against two walls and the diagonal (an
   outlined block may now touch walls). Balconies 256, the eight lever posts (32 by 32 by 160, `d2wlactr`) on the
   balcony corners. All flights 128 wide on the ramps' centre lines.

### New features: what worked, what was refused

Worked as the schema says: movers with `stretch`, with level `travel` and `kerbs`; four movers moved by one switch;
doors `slide_left`/`slide_right` with `back_surface` and `thickness: 32`; a door in a `width: full` opening; `ends` on
a room and per wall; `panels` with `offset`, `from: end`, `bottom`, `height` (also a panel that runs on into a
doorway is cut by it, which shifts its texture: used for the seven strips right of doors); `tread`; `threshold`;
`to_height` onto a bridge over a level; an outlined block flush against a wall and a diagonal wall; blocks on
blocks (lever posts on hanging balconies).

Not used, because the original has nothing for them: `leaves: 2` (no door here parts down the middle), lift
`thickness` (the lift is a solid column), `auto_return_seconds`, mover `state: end` or `outline`, `top_surface` on
flight sides (no flight here has sides), a climbing `path` room.

Refused or wrong (repros under `output/studio_cal/mm6_6d18/repro/`):

1. **A switch above a hanging block that touches its wall is refused.**
   `oymap validate output/studio_cal/mm6_6d18/repro/switch_over_hanging_block --assets assets_dev` gives
   `objects.yml: switches[0]: the object does not fit on that wall of room:tower`: the lever is 1,276 above the
   floor, the landing's top 416. With the landing 2 short of the wall it validates. In the brief: the stair tower's
   lowest north-east landing stays 2 short of the north wall for this reason (the lever over it is the original's,
   door record 37, at -774).
2. **The solver does not cross a 16 gap** between two slabs at the same height (the machine bridge to its balconies).
   `oymap solve output/studio_cal/mm6_6d18/repro/solve_gap16 --assets assets_dev`: `never reached: 1 sectors (1)`;
   make the second slab 528 long so that the two touch and it reaches both. `oymap probe ... --from 128,400,0 --to
   128,700,0` on the repro: "a step is too high ... step 768". The game walks across.
3. `random_items: 0` on a chest (the bookcase): `objects.yml: chests[0].random_items: must be at least 1` (not new).

### Gaps still open, most harmful first

1. **A sloping free slab** (round two's gap 2). The tower's 16 ramps and the stair tower's upper 8 are flights whose
   steps are solid down to where the flight starts, where the original's ramps are slabs 32 thick: a wedge hangs
   under every ramp. Sectors 5 and 37 lose about 6 points on the offset grid, and the largest texture misses left are
   these wedges' sides (`vlcwl1lg` seen as `d2wlactr`, 148 rays; `ctwl2` as `bemvwal`, 137). Field: `slope` on a
   platform (`{to, toward}`), or `thickness` on a flight.
2. **A flight's foot cannot name its floor** (`from_height`). Where landings stand one above another (every corner of
   both towers) the upper ones must be smaller than the lower so that each flight finds its own: the tower's upper
   four are turned rectangles 380 long standing inside the lower six-sided ones; the stair tower's are 128, 108, 86
   and its top landing a strip 36 deep.
3. **The underside of a block** (`bottom_surface` on a platform): it takes the top's surface. The machine room's
   eight balconies (`d2ceil1` under `vlctrm3` tops, 178 rays), the cavern walkway (`d2ceil1`, 90), the channel bridge
   (`ctflor1`, 59).
4. **Texture offsets.** The original anchors wall textures to the world (u from x or y, v from z); the rebuild to each
   face or panel. Wall rows stand at other heights (channel hall picture), and ten corner strips 96 long show the
   left part of an `RE` texture where the original shows its right part (`strip_u.py` lists them). Field: an `offset`
   on a surface, or `align: world`.
5. **An opening flush against the end of a wall.** The channel hall's west and north doors stand right beside the
   corner pilasters in the original; an opening needs 16 of wall each side, so both stand 16 farther off.
6. **Two rooms in one space** (hall 14 and the stair passage 46): the hall is cut off 128 short (offset grid: 2.5
   points).
7. **A ceiling that is level, then sloping, then level** (the laboratory as three rooms; the lower stair's ceiling).
8. **Posts on a mover**: said as four extra movers on the same lever (works, but they are four objects).
9. **A door of two halves one above the other that slide sideways in opposite directions** (doors 1/2, 23/24):
   `leaves: 2` parts down the middle. Here one leaf slides north as the lower half does. Field: `split: across` or a
   direction per leaf.
10. **A switch on a block or a floor**: the eight machine-room levers stand on posts in the original (here on the
   walls beside the balconies, 244 to 554 away); four escape tiles lie on floors (here wall plates); the original's
   levers are small plates that sink 16 (door records), which could be movers but not switches.
11. A floor that runs on under a wall (the lava slots of rooms 3 and 39); an effect that throws an object (the
   fountains are Lua); a chest with no random items; one chest of two by a condition; spawn tiers 4 to 12; item
   spawns; the fire-resistance wall (Lua); a raised level does not carry a platform (the tower's tile keeps `rise:
   80`, only a sunken level does).

### Tool defects

1. Switch above a hanging block refused (repro `switch_over_hanging_block`, above).
2. **`oymap audit --reach` puts every mover at its start "with every door out of the way"**: the stretching bridge
   counts as retracted, so `oymap audit devdocs/map_studio/briefs/mm6_6d18/L4 --assets assets_dev --reach` reports
   29 of 57 sectors unreached, among them room:s4 behind the first bridge, which `solve` reaches at step 2. A mover
   that carries a floor should count in both poses.
3. Solver and 16 gaps (repro `solve_gap16`, above). This is why the original's own solve stops at the sliding bridge
   (S3: "not understood yet").
4. **A wall-placed object's `wall` is an edge number, and an outline edit renumbers the edges without a word.** Giving
   the channel hall its notched corners moved `switch:lever18` from the west wall (edge 3) to the east wall (the new
   edge 3); `validate`, `build` and the playtest (whose `click` takes the event, not a place) all passed. Found only
   by measuring the built plates against the original's lever records (`switch_audit.py`). The tool cannot know the
   intent, but it could make the slip visible: `build` (or `fmt`) could print each wall-placed object's position and
   compass side, so that a renumbering shows in the output's diff. Compass sides are no remedy in a notched room
   (several walls face the same way).
5. **The fix batch changed what a switch's `height` is measured from** (now the highest floor under it). Without any
   message the channel hall's door lever rose 212 (from the lava to the floor level; set back to 122 here) and the
   escape tiles 16. Projects written before the batch shift silently; `build` could warn where the floor under a
   wall object is not the room's floor.
6. **`oymap compare` still stands on the 256 grid and on edges** (round one's defect 8): measured shapes score 4.2
   points lower than shapes widened by 2 to 4 units. A half-step offset (or excluding points within 2 of an edge)
   would remove the pull towards wrong shapes.
7. `ingame_compare.py`: timers keep running until the capture, so a lava fountain's fireball can stand in front of one
   camera and not the other (`output/studio_cal/mm6_6d18/ingame_r3c/diff/01-gallery-south.png`).

### What I was unsure of

- Doors 1/2 and 23/24: which half the rebuild's single leaf should follow. The lower (it is where the party walks).
- The `D8wlBLE` faces in every lifting door's record: the floor one is the leaf's underside (it moves), not a
  threshold; the thresholds were taken from the original's floor at the doorway.
- Door 53 (the lava wall) has no vertices; its direction (+z, 255) says lifting, so the lifting door stays.

## Round four (2026-11-12, night)

Edited by hand and by one-off scripts, each written from the original's export and checked by its diff:
`output/studio_cal/mm6_6d18/r4/tower_edit.py` (the tower's landings, foot, kerb, bridge and nine flights, from faces
40-59, 61-97, 165-168, 2486-2516) and `stair_edit.py` (the stair tower, faces 1336-1393); the chest, laboratory,
slot-room, alcove and switch edits were inline Python replacements of single entries (numbers in the text below).
Start snapshot: `output/studio_cal/mm6_6d18/r4_backup/`. Scratch, measuring helper (`sect.py`: loss by sector from
`points.json`), check and play scripts, solve outputs and variant comparisons: `output/studio_cal/mm6_6d18/r4/`. The
comparisons are `compare_r4_start/` and `compare_r4/`.

### Scores (the merged measure)

| | score | shape | textures | `--step 200` (shape, textures) |
|---|---|---|---|---|
| start of round four | 98.7 % | 99.1 % | 97.9 % | 99.0 % (99.4, 98.1) |
| towers: open flights from their own landings | 99.3 % | 99.5 % | 98.8 % | |
| laboratory one room, bank ramps as wedges, lava slots, alcove neck, door 6 | 99.4 % | 99.6 % | 98.9 % | |
| **end** | **99.4 %** | **99.6 %** | **98.9 %** | **99.5 % (99.7, 98.9)** |

- Loss by sector (`sect.py`, share of all points, start to end): tower (5) 0.27 to 0.02, stair tower (37) 0.34 to
  0.02, lava cavern (39) 0.09 to 0.05, channel hall (34) 0.06 to 0.05, gallery (9) and south hall (15) to 0.
  Left: hall 14 (0.26, two rooms in one space), the machine room's balcony undersides (16, 17: 0.11) and the rest.
- `compare.py`: `18 in, 10 near, 7 out`. Out: smallest sector floor, smallest and median sector height (the lava
  slots are sectors 64 high of their own; in the original they are part of the halls), doorway width minimum, and
  the three reach figures, which `calibration/originals/mm6_6d18.metrics.json` still holds from the original's old
  solve (22 sectors reached; S3 says these files are stale).
- Rooms: 59 (57 at the start: the laboratory's three rooms are one, four lava slots are new). `oymap solve`: 5, 6,
  8, 9, 25, 32, 34, 36, 40, 41, 42, 44, 46, 47, 48, 54, 55 of 59 in sixteen steps, in the original's order (its own
  solve: 47 of 47 in fourteen; split door and bridge lever, which it takes in one step, are steps 1 and 2 here; the
  lift's foot, part of sector 31 there, is a step of its own here). The four sectors never reached are the lava
  slots, 64 high, which the party cannot enter in the original either (tool defect 2). `audit --reach`: the same
  four.
- **The playtest passes**: 276 steps (round three's 270, unchanged, which now walk the open flights of both towers;
  and six new: the lava wall opened from its lever, the party into the chest alcove through the neck and back; the
  bookcase, chest 2 and chest 3 looted with their measured items asserted).
- In-game pairs (`output/studio_cal/mm6_6d18/ingame_round4/diff`, 13): edge agreement 0.84, blurred difference
  0.043 (round three's 26 pairs: about 0.8 and 0.06). Looked at: the laboratory from its neck (0.95; one room, the
  sloping middle ceiling as in the original), the channel hall's bank ramp (0.93), the lava hall's end wall (1.00),
  the stair tower's hanging landings (0.85), chest 1 (0.88; its ends now `ch3side`, its top still the front's
  texture), the gallery's south door (0.57, the vertical banding of `vlcwl2` sits at other offsets: no word; the
  leaf now has the original's two faces). Two cameras show only walls (tower from the bridge, the lava cavern's
  slot below the walkway: shots have no pitch).
- `build/game/openyamm` changed during the round (21:55 at the start, 22:28 at the end), not by this session.

### What changed

1. **The two ramp towers as the original builds them.**
   - Tower (5): all eight corner landings have the original's six-sided outline (the upper four were turned
     rectangles 380 long), the bridge is 1,664 by 256 from wall to wall (was 1,662 by 258), the foot is the
     measured slab (-640 to -512, 480 to 768, top 0) with its kerb 64 high (y 480 to 512; was a slab 126 by 286 from
     y 513 to 799 and no kerb). Each of the nine ramps is a flight from the landing edge to the landing edge with
     `from_height` and `to_height`, `open_below: true` (the raking underside 32 under the steps' line) and eight
     steps of 16.
   - Stair tower (37): the first turn stands on the floor as in the original: the step of 20 at the foot, the north,
     west and south ramps as blocks with `top_slope` (20 to 128 toward the west, 128 to 192 toward the south, 192 to
     320 toward the east) and the three corner blocks. The rest hangs: eight corner landings 128 square (were 128,
     108 and 86 in the three turns) and the top landing 256 by 128 against the north wall (was a strip 254 by 36,
     2 short of the wall), nine open flights with `from_height`/`to_height` (eight steps on the north and south
     walls, four on the east and west).
   - Measured choice: with the ramps as hanging `top_slope` blocks instead (a smooth top, a level underside) the
     tower scored 0.989 against 0.997 for open flights of eight steps and 0.993 for four. The flights are also the
     nearer shape (an underside that rakes as the original's, a top within 8 on average), so they were kept; the
     step count of eight is the nearest a flight gets to a ramp, not the original's (it has none).
2. **Warnings and the lever over the landing.** `floor_height` on the five switches over levels or landings
   (`lever18` -2048, `lever20` -2048, `tile31` -752, `tile41` -240, `tile42` -752): positions unchanged (checked
   against the original's lever records with `r3/switch_audit.py`: lever 37 at -772 against -774). The stair
   tower's top landing now touches the north wall under lever 20. The build gives no warning but the placeholders
   and the false thin-wall warnings (tool defect 1).
3. **Chests** (the original's chest faces and `6d18.scene.yml` chest records). The lead's quarter turn was right
   for all seven: each chest's width (96) runs along its front, which looks where the original's does. Corrected:
   depth 64 (was 62) and the measured centres (1 or 2 off), so every back touches its wall as in the original;
   `end_surface` `chXside` on the two ends; contents from the records: random items as many as the original rolls
   (4, 4, 4, 5, 3, 4, 4) and one treasure level per chest, the mean of the original's per-roll levels (3, 3, 3, 3,
   4, 3, 3); chest 2 holds the Letter to Marcus (2148), chest 3 the Scrap from Gharik's Journal (2149) (both new in
   `project.yml` items). The bookcase is the measured block (640 by 128 by 256, touching the south and east walls)
   with `random_items: 0` and its four scrolls.
4. **The laboratory as one room** (42): `ceiling: -384`, `ceiling_points` at the neck's four corners (-512) and
   `ceiling_lines` along the two creases (x 5376 and x 5888): three ceiling faces, level, sloping, level, as the
   original's (1558, 1557/2559/2560, 1567). Corner strips 32, 34 on the two diagonal walls. The bench is the measured
   256 by 128 block and the low block against the east wall (128 by 64 by 64) is new.
5. **The lava under the end walls** (rooms 3 and 39): four low rooms (`s3w`, `s3e`, `s39w`, `s39e`: 256 or 128 deep,
   64 high, lava floors with the lava kind and step event, `d2wlactr` ends, `6voltyl` sides, `d2ceil1` ceilings, as
   measured), each open to its hall along the whole wall (`width: full`, `height: 64`).
6. **Other items of round three's list.** The channel hall's bank ramps are solid wedges (`top_slope`, 192 over 512)
   where they were flights of six steps; the bridge's sides `ctwl2` as measured (were `ctflor1`). The lower stair's
   ceiling rakes to x 864 and is level for the last 32 (`ceiling_points` with `ceiling_lines`; was one plane to the
   head). The "lava wall" door stands in the south hall's wall plane: the neck is part of the alcove and ends 32
   short of the hall (`from_wall`/`to_wall`, `width: full`, threshold `vlcflora`), so the leaf's face is where the
   original's face 2255 is (it stood in the middle of the neck, 114 farther in). Door 6 (gallery south) has the
   original's two leaf faces (`vlcwl2` to the corridor, `d2wlactr` to the gallery; was `cvdor1`). The cavern
   walkway is 256 by 1,152 wall to wall (was 260 by 1,150).

### New features: what worked, what was refused

Worked as the schema says: `from_height`, `to_height` and `open_below` on 18 flights; `top_slope` on blocks standing
on the floor (stair tower, bank ramps); `ceiling_points` with `ceiling_lines` (laboratory; lower stair, see tool
defect 3); `floor_height` on wall switches (it also cleared the refusal of `repro/switch_over_hanging_block`: lever 20
validates with the landing against its wall); `random_items: 0`; chests touching their walls (validate accepts a
back flush with the wall); `end_surface` on chests.

Tried and not kept: hanging `top_slope` blocks for the tower ramps (they build correctly, but a hanging sloping
block has a level underside: a wedge up to 160 thick under each ramp, the round-three loss in another form);
channel-hall stairs on the original's tread lines (`from: [4032, 640], to: [4416, 640], steps: 6`: the original's
last rise is the bridge's edge, so the sixth step has to lie on the bridge, and the build makes it a block from -2048
to -1952 through the bridge and 32 below its underside).

Refused or wrong (repros under `output/studio_cal/mm6_6d18/repro/`):

1. `opening_flush_to_corner`: an opening cannot stand against the end of its wall, and `along` beyond the limit is
   moved without a word: along 0.75, 0.9 and 1.0 all build the door at y 16 to 144. The channel hall's west and
   north doors stay 16 off (`oymap build output/studio_cal/mm6_6d18/repro/opening_flush_to_corner --assets
   assets_dev --out <scratch>` and `oymap export` the result).
2. `thin_wall_full_mouth`: false warning (tool defect 1).
3. `ceiling_points_over_steps`: a raking ceiling over a stepped floor is split into slivers (tool defect 3).

### Gaps still open, most harmful first

1. **Two rooms in one space**: hall 14 stands 128 inside the stair passage 46 in the original; cut off at x 896
   here (sector 14: 0.26 of the 0.6 points lost).
2. **The underside of a block** (`bottom_surface` on a platform): the machine room's eight balconies (`d2ceil1` under
   `vlctrm3` tops; 39 of the differing points), the cavern walkway (`d2ceil1` under `ctflor5`), the channel bridge
   (`ctflor1` under `ctflor4`).
3. **A ramp that is a sloping slab**: a raking underside under a smooth top. The towers' 18 ramps are open flights
   of steps 16 high: the top differs by up to 16 from the original's slope. Field: `open_below` (or `thickness`) on
   a `top_slope` block, or `smooth: true` on a flight.
4. **Texture offsets** (walls anchored to the world, `align: world` or an `offset`): the gallery's and corridors'
   `vlcwl2` banding, strips that show the wrong half of an `RE` texture.
5. **A chest's own top and front** (`top_surface` on a chest; the front's three strips `frLE`, `frntB`, `frRE`):
   the top takes `surface` (the front), so the original's ornate lids are missing.
6. **A flight whose last rise is the upper floor's edge** (steps 64 deep that stop one rise short of `to`): the
   channel hall's two stairs keep six steps of 54 that end on the bridge.
7. **An opening flush against the end of a wall** (above).
8. Unchanged: posts on a mover (four extra movers), two door halves one above the other, a switch on a block or a
   floor (the eight machine-room levers on posts, four escape tiles on floors), an effect that throws an object
   (fountains are Lua), one chest of two by a condition (chest 8), a treasure level per roll, spawn tiers 4 to 12,
   item spawns, the fire-resistance wall (Lua), a raised level that carries a platform (the tower's tile keeps
   `rise: 80`), a slope with a level end on a room's own ceiling over a passage (the 12 lower ceiling over the
   foot of the lower stair, faces 2435).

### Tool defects

1. **False "wall without thickness" warning.** A room with any `walls` entry makes the build warn that an opening "is
   in a wall without thickness and leaves wall round it ... move them at least 16 apart", even where the room's
   whole side is the opening and nothing lies in one plane: `oymap build
   output/studio_cal/mm6_6d18/repro/thin_wall_full_mouth --assets assets_dev --out <scratch>` warns; remove the
   slot's `walls` entry and it does not; the built faces are the same. Eighteen such warnings in this brief.
2. **`solve` and `audit --reach` count a sector lower than the party as never reached** (`never reached: 4 sectors`
   here, the lava slots 64 high; the same repro reports it). The niche rule looks at floor area only; a sector the
   party cannot stand in should count as a niche.
3. **`ceiling_points` over a stepped floor** builds a plane of four points as a fan of slivers through the side walls'
   step corners, with rounded heights so they are not merged (`repro/ceiling_points_over_steps`: 9 raking faces; the
   lower stair here: 23 for the original's one).
4. **`build --out` writes `ids.lock.yml` into the project folder**, also for a repro (the round's brief says it does
   not). Removed by hand from the repros.
5. **`along` is clamped without a word** (repro `opening_flush_to_corner`).
6. **Moving an opening's wall pair silently, again** (round one's defect 2): giving the alcove a neck moved
   `open:s15_alcove` from the neck's end to 128 of the alcove's north wall 256 away (the pair with the longest shared
   stretch), with no message; found by exporting the build. Fixed here with `from_wall`/`to_wall`.

### What I was unsure of

- Whether the lava slots belong in the rebuild as rooms of their own. They are the original's shape (the lava floor
  runs on under both end walls), but they make four sectors the solver cannot reach and two `compare.py` figures
  fall out of range; `oymap compare` gains (sector 39 from 0.983 to 0.991).
- Which way a chest's front looks cannot be said (every side but the ends takes `surface`); checked only that the
  width runs along the original's front.

## Round five (2026-11-13, night)

Briefed by [ROUND_FIVE.md](../../../rounds/ROUND_FIVE.md). The project files were edited by hand and by one-off scripts
in `output/studio_cal/mm6_6d18/r5/`, each written from the original's export and checked by its whole diff:
`ramps_edit.py` (the 18 ramps, from faces 41-57, 65-97, 2486-2516 and 1340-1393), and inline replacements for the
undersides (12 platforms), the posts' ids and the eight levers on them, the bridge's parts, the tiles, panels and
bookcase, the chest tops, the five pinned openings, the playtest and the placeholders' notes. Start snapshot:
`output/studio_cal/mm6_6d18/r5_backup/`. Measuring helpers `r5/faces.py` (the original's faces by number or sector)
and `r5/bfaces.py` (the rebuild's faces in a box); comparisons `compare_r5_start/`, `compare_r5/`,
`r5/compare_r5_step200/`; the rebuild's `flow` and `solve` in `r5/`.

### Scores

| | score | shape | textures | `--step 200` (shape, textures) |
|---|---|---|---|---|
| start of round five | 99.4 % | 99.6 % | 98.9 % | |
| ramps as sloping slabs | 99.5 % | 99.6 % | 99.1 % | |
| undersides, chest tops, levers on posts, bridge parts, tiles, bookcase | **99.6 %** | **99.6 %** | **99.7 %** | **99.7 % (99.7, 99.5)** |

- Loss by sector (`r4/sect.py`, share of all points, start to end): tower (5) 0.02 to 0.002, stair tower (37) 0.02
  to 0, lava cavern (39) 0.05 to 0, machine room (16, 17) 0.11 to 0.02, channel hall (34) 0.05 to 0.02, laboratory
  (42) 0.007 to 0.009 (the bookcase's west end, below). Left: hall 14 (0.26, two rooms in one space).
- `compare.py`: `18 in, 10 near, 7 out`, as in round four (the same seven figures).
- Rooms 59; `oymap solve`: 55 of 59 in sixteen steps in the original's order, as in round four (the four lava slots
  stay unreached, tool defect 2 of round four). `audit --reach`: the same four.

### Contents: monsters and items

- **The original places no monster and no item.** Its scene's `initial_state.actors` and `sprite_objects` are
  empty, and so are the counts in its `6d18.dlv` (0 actors, 0 sprite objects, read from the file). Placed: 0 of 0
  monsters, 0 of 0 lying items. Everything that lives in the Forge comes from its 35 monster spawn points, all kept
  as `spawns` (slots as in round one; the original's tiers 4 to 12 still cannot be said).
- **The 17 item placeholders stay, explained** (each now has a `notes` field). Every one is an item spawn point of
  the original (spawn type 2 with a treasure level: the game rolls a random item there when the map is first
  entered; `IndoorWorldRuntime::materializeTreasureSpawn`). `items[]` lays a fixed item (one roll made the same in
  every game) and `spawns[]` takes monsters only, so neither is the original's thing. The task names item44,
  item47 and item49; the other fourteen are the same kind. Field: `spawns[].kind: item` with `treasure_level`.

### Events, the original's against the rebuild's (`oymap flow`)

| Original | Rebuild | Same? |
|---|---|---|
| 1, 22-26, 29, 30 | (bound to nothing in the original) | not built, as before |
| 2, 13 (doors 1/2, 23/24) | `evt:door1`, `evt:door23` | differs: one leaf slides north where two halves one above the other slide apart (no word) |
| 3 (bridge stub) | `evt:lever3`, stretching mover | same |
| 4-7, 9-12, 14, 17-21 (lever and door) | `evt:lever4` ... `evt:lever21` | same |
| 8 (bridge slides east, opens 49) | `evt:lever8` | same; the bridge's posts are now parts of its one mover (one door record, as the original's door 14), the lever on its post |
| 15 (lift, top and foot) | `evt:lever15_top`, `evt:lever15_foot` | same |
| 16 (laboratory door, key or qbits) | `evt:lever16` | same tests and effects |
| 31, 41, 42 (floor tiles, clicked) | `evt:tile31`, `tile41`, `tile42` | **same since round five**: platforms 64 square and 16 high on their islands, clicked (were wall plates). The variable is set after the teleport, the original sets it before (a preset's own work runs before its `effects`); no effect of it |
| 32 (raised tile, clicked) | `evt:tile32` | **same since round five**: clicked (was stepped on) |
| 43 (wall tile, clicked) | `evt:tile43` | same; now a wall panel with an `id` (the original's face 1497 lies in the wall) where it was a switch plate |
| 33-36, 38-40 (balcony levers) | `evt:lever33` ... `evt:lever40` | same; the levers stand on their posts since round five |
| 35 (lava wall) | `evt:lever35` | same toggle; the wall is a lifting door where the original's face vanishes |
| 44-47, 49, 50 (chests) | `evt:chest1` ... `evt:chest7` | same; one treasure level per chest where the original rolls each item at its own |
| 48 (chest 5, or chest 8 for a party with qbit 1029) | `evt:chest5` | differs: one chest with chest 5's contents and both qbits; chest 8 cannot be said (one chest of two by a condition) |
| 51-53 (lava step events, on load) | `evt:lava_on`, `lava_off`, `lava_load` | same; `lava_off` now also on the channel hall's two bank ramps (faces 1184, 1187), which are blocks with an `id` |
| 54 (lava burn timer) | `evt:lava_burn` | same (both lava mechanisms kept, as decided) |
| 55 (door won't budge) | `evt:budge*` | same |
| 56-61 (fountains) | `evt:fountain_*` | same behaviour, as Lua (no effect throws an object) |
| 62 (bookcase) | `evt:bookcase` | **same since round five**: the clicked block (four searches, "Found something!", one scroll of six at random; a `lua` condition for the count, a Lua step for the draw); was a chest holding four fixed scrolls. Its second binding, the crystal room's ceiling face 2481, is not built (not understood) |
| 90 (exit) | `evt:exit` | same |
| 91 (fire resistance once) | `evt:fire_wall` | **same since round five**: the wall over the north door is a panel with an `id`; condition and effects in words (`not: {map_var}`, `set`, `add: FireResistance 25`), the player bit by a `lua` test and a Lua step; was a plate with the original's Lua |
| 65000, 65001 (Nicolai, global) | the same global events | same |

Of the original's 53 map handlers that are bound to something (events 2-21, 31-36, 38-62, 90, 91), 49 do the same
thing under the same condition here (the six fountains, the bookcase's draw and the fire wall's player bit through
Lua; the chests open the same chests with one treasure level each where the original rolls each item at its own); 4
differ: events 2 and 13 (one leaf for two halves), 35 (the lava wall lifts where the original's face vanishes) and 48
(chest 8). Seven came over from differing since round four: tiles 31, 41 and 42 (wall plates), 32 (stepped on), the
bookcase (a chest of fixed scrolls), the fire wall (a plate) and event 53 on the bank ramps (missing).

### What changed

1. **The towers' 18 ramps are sloping slabs** (`top_slope` with `thickness: 32`; the round-four compromise undone).
   Each runs from landing edge to landing edge, its top and underside the original's planes (tower ramp 1: top 0 to
   128 over y 768 to 1536, underside -32 to 96, as faces 41 and 97), `d2wlactr` in the tower and `bemvwal` in the stair
   tower on sides, top and underside (`bottom_surface`). The flights' steps are gone (the tower's faces fell from 2,741
   to 2,105). Tower and stair tower: 0.04 of the 0.6 points lost at the start, nothing now. The playtest walks both
   towers up and down on them.
2. **Things on blocks and movers.** The eight lever posts have ids and the eight balcony levers stand on them
   (`switches[].block`, the side the original's lever arm comes out of, the plate 96 to 128 above the balcony: door
   records 13 and 41 to 47); they were on the walls beside the balconies, 244 to 554 away. The machine bridge's four
   posts are `parts` of its mover (one door record, as the original's door 14) instead of four movers; the south posts
   are 64 wide as measured (two parts each, so that none overlaps the kerb: an overlapping part built a face in the
   kerb's end plane). The four floor tiles are platforms with ids, clicked; the wall tile and the fire wall are wall
   panels with ids; the bookcase is a platform with an id.
3. **Undersides and lids.** `bottom_surface` on the eight balconies (`d2ceil1`), the cavern walkway (`d2ceil1`), the
   channel bridge (`ctflor1`) and the gallery walkway's two slabs (`d2wlactr`, faces 396, 397, 2522-2524; not named in
   the task, measured the same way). `chests[].top_surface`: each chest's lid middle (`ch3tpbv`, `ch3topb`, `ch2topb`,
   `ch1topb`, `ch2tpbv`: the `v` ones on the two chests that face north, as in the original).
4. **Warnings.** The five openings that could have taken another wall pair are pinned with `from_wall`/`to_wall`
   (the pairs the build took, each checked: the door walls 32 apart or the flush mouths). Left: the 18 false "wall
   without thickness" warnings (round four's tool defect 1, as instructed) and the 17 placeholders.
5. **Playtest** (288 steps, was 276): the tower's tile is clicked; the fire wall clicked twice sets its variable once;
   the bookcase searched five times gives four scrolls (the game puts each on the cursor, the walk stows it) and counts
   to 4; the four escape tiles put the party where the original's do (positions asserted); the bridge's posts are no
   longer checked as doors of their own. The lead's two fixes are kept with their comments: `clear_hostiles` on the
   walk off the tower's island and the `make_room` before the chests (its keep list now holds all six scrolls).

### Playtest

288 steps from a new game, **passes four runs of four** on the final build (`r5/play4.sh`, logs
`r5/final_play_1.log` to `_4.log`), and two more during the round. Two failures on the way, both mine and fixed: the
walk still asserted the bridge's posts as doors 30 to 33 (they are parts of door 29 now), and the bookcase's count
missed the scroll the game leaves on the cursor (the walk now stows it, as a player would).

### Pictures

16 same-camera pairs (`output/studio_cal/mm6_6d18/ingame_r5/diff`, shots `r5/shots_r5.yml`): edge agreement 0.83,
blurred difference 0.055. Looked at: the tower from its lava (0.88; the ramps' smooth slopes and their raking
undersides as in the original), the stair tower (0.85 and 0.94), the cavern from its recess (0.92), the channel bank
under the bridge (0.87; the `ctflor1` underside matches; the north door's leaf shows where the original shows wall,
round four's flush-door gap), chest 2 (0.82; the lid is the original's `ch3topb`), the alcove chests (0.99), the
bookcase with the laboratory's two warlocks from the spawns in front of it in both maps (0.86). Three machine-room
cameras and the machine island's stand too low or against a wall (shots have no pitch and the floor under a point is
the lowest there): they show walls and lava, alike in both. The pictures were taken before the south posts were split
in two parts (the same outline). The Forge has no placed monsters or items to picture.

### New features: what worked, what was refused

Worked as the schema says, first time: `platforms[].thickness` with `top_slope` (18 hanging ramps, tops and undersides
exactly the original's planes) and `bottom_surface` (30 blocks); `switches[].block` with `side` (8 levers on posts);
`movers[].parts` (4 posts, two of them in two parts); `chests[].top_surface` (7); a platform with an `id` as a click
source (four tiles, the bookcase) and as a step source (the two bank ramps); a wall panel with an `id` as a click source
(the wall tile, the fire wall); a `lua` condition, alone and beside `not: {map_var}`; `from_wall`/`to_wall` on the
five openings the build warned about. Nothing was refused, so there is no repro this round.

Not used, because the Forge has nothing for them: `monsters[]` and `items[]` (none in the original), `kills`, lights
on and off, `doors[].secret`, `solid: false` / `visible: false`, ladders, placed sounds, `floor_surfaces`,
`ceiling_surfaces`, shaped mouths, `trim_to_wall`, `chests[].rides`.

### Compromises

- **Undone:** the towers' 18 ramps (open flights of eight steps; now sloping slabs 32 thick); the eight levers on the
  walls beside the balconies (now on their posts); the bridge's posts as four movers (now parts of its one mover);
  three floor tiles as wall plates and the tower's tile stepped on (now clicked tiles on their islands); the wall tile
  and the fire wall as switch plates (now wall panels); the bookcase as a chest of four fixed scrolls (now the clicked
  block with the original's searches); the balconies', walkways' and channel bridge's undersides in their tops'
  texture; chest lids in their fronts' texture.
- **Left** (no word, not faked): both lava mechanisms (kept by decision); texture offsets on walls; hall 14 inside
  passage 46 (two rooms in one space); doors 1/2 and 23/24 as one leaf; the channel hall's two doors 16 off the
  pilasters (an opening flush against a wall's end); the fountains as Lua (objects thrown by an event); chest 8 (one
  chest of two by a condition); per-roll treasure levels; spawn tiers; item spawn points (placeholders).

### Gaps still open, most harmful first

1. **Two rooms in one space**: hall 14 stands 128 inside the stair passage 46 in the original; cut off at x 896 here.
   Sector 14 is now 1.45 of the 1.8 points lost in all (0.26 % of 0.33 %).
2. **Item spawn points** (17, all over the map): a random item of a treasure level appears there when the map is first
   entered. Field: `spawns[].kind: item` with `treasure_level`.
3. **One chest of two by a condition** (event 48, chests 5 and 8) and a **treasure level per roll** (every chest).
4. **An effect that gives one item of a list** (the bookcase's draw, Lua) and **a count in a condition**
   (`{map_var: n, at_least: 4}`; the bookcase's limit is a `lua` test that must name the variable's number).
5. **Texture offsets** on walls (`vlcwl2` banding in the gallery and corridors, `RE` strips showing the wrong half).
6. **An opening flush against the end of a wall** (the channel hall's west and north doors stand 16 off the
   pilasters; seen in the channel picture).
7. **A platform with a surface per side and a click on one face**: the bookcase's west end is `bemvwal` in the
   original (`bookcas2` here: the laboratory's one texture miss, 0.009 % of the points), and only its front face runs
   event 62 there (every face here).
8. Unchanged: two door halves one above the other, an effect that throws an object (fountains), the player bit of the
   fire wall (Lua), spawn tiers 4 to 12, the channel hall's stairs whose last rise is the bridge's edge, a slope with a
   level end on a room's own ceiling over a passage, a raised level that carries a platform (the tower's tile keeps
   `rise: 80`), event 62's second binding on the crystal room's ceiling (face 2481, not understood).

### Tool defects

1. **A `lua` condition must name a map variable by its number, and the number is not the declaration order.**
   `wiring.yml` declares `variables: [on_lava, fire_wall_used, bookcase_searches]`; `ids.lock.yml` numbers them
   `on_lava: 0, bookcase_searches: 1, fire_wall_used: 2` (new names apparently in sorted order). The first build used
   `MapVar(2)` for the bookcase (the third declared) and so tested the fire wall's variable, with no message; found by
   reading `build/cal6d18.lua`. A `map_var` condition with `at_least` (or a way to name the variable inside `lua`) would
   remove the guess. Shown by `grep -A3 '^map_vars' devdocs/map_studio/briefs/mm6_6d18/L4/ids.lock.yml`.
2. **A mover's part may overlap its kerbs without a word**, and builds a face in the kerb's end plane over the post's
   face (two coplanar faces, both seen): the south posts as single parts 64 wide gave faces 2086 and 2096 at y 5392
   (`r5/bfaces.py 1792 1856 5392 5420 -40 390` on an export of that state). Split here; the build could merge or warn.
3. `oymap flow` reads a Lua give with a variable item as "give item 0" (evt:bookcase), and teleport presets run their
   own move before their `effects` (the escape tiles set the lava variable after the teleport; the original sets it
   before): no field says the order.
4. `ids.lock.yml` keeps the removed ids (`switch:tile31` ... `switch:tile43`, `switch:fire_wall`, `mover:machine_post_*`, `chest:bookcase`)
   with their numbers: probably by design (numbers stay stable); noted because the lock no longer lists only what is
   built.
5. Unchanged from round four: the 18 false "wall without thickness" warnings (`repro/thin_wall_full_mouth`); `solve`
   and `audit --reach` count the four lava slots as unreached.
6. `ingame_compare.py` shots have no pitch and stand on the lowest floor under a point where a balcony or island lies
   over lava, so pictures of undersides and of things on islands are hard to take (the machine room's four shots).

## Finishing round (2026-11-13, morning)

Briefed by the lead's task message (rules of [ROUND_FIVE.md](../../../rounds/ROUND_FIVE.md)): make "is it done, mechanisms
and scripting included, and playable?" a plain yes. Start snapshot: `output/studio_cal/mm6_6d18/r6_backup/`. Scratch,
helpers and logs: `output/studio_cal/mm6_6d18/r6/` (`spawns_edit.py` wrote the item spawns and the spawn tiers from the
original's spawn records, `r6/orig.json`; the chests, doors, wiring and playtest were edited by one-off inline
replacements, each checked by its diff; `floors_at.py` lists the floors under a point in an export). Comparison:
`compare_r6/`.

### Scores

| | score | shape | textures |
|---|---|---|---|
| start of the round (`compare_r5`) | 99.6 % | 99.6 % | 99.7 % |
| end (`compare_r6`) | **99.7 %** | **99.6 %** | **99.7 %** |

The gain is the laboratory's doorway wall (it had D8wlBLE corner strips the original does not have: its ends are vlcwl4b
faces 64 wide, 1510 and 1530) and the bookcase's west end (bemvwal, `end_surface`). Rooms 59; `oymap solve`: 55 of 59 in
sixteen steps, the other four the lava slots, now counted as niches ("never reached: 0 sectors"). One build warning
left, the false "wall without thickness" at `open:n50_machine` (round four's tool defect 1).

### What changed

1. **Item spawn points.** The 17 placeholders are `spawns[]` with `kind: item` and the original's `treasure_level`, at
   the original's points (spawns 0, 4, 9, 12, 15, 16, 18, 19, 22, 36, 37, 38, 41, 43, 44, 47, 49; levels 1 to 6). The
   built spawn records are the original's one for one (position, type 2, level). **No placeholder is left.** In the
   game they roll on the first visit (a heap of gold lay at spawn 47 in the alcove picture).
2. **Spawn tiers.** The seven monster spawns whose original index is 4 to 12 have their `tier` (1, 28, 39, 42: slot 1
   tier c; 34, 35: slot 1 tier a; 33: slot 3 tier a). Spawn 28 is back at the original's x 5888 (was 5880); spawn 35
   stands 1 unit into the corridor (3073, 2912): the original's point lies on the line between rooms 40 and 41 and a
   spawn must lie inside its room (it stood 40 into the passage). Spawns 21 (tower) and 8 (gallery) take
   `floor_height` -512 and -256, the original's lava floors under them (the build had put them on a landing at 786 and
   the walkway at 0).
3. **Doors 1/2 and 23/24** are the original's halves that pass each other: `leaves: 2`, `split: across`, `fold: true`,
   `travel: 255`, `tile: true` (lower half north, upper half south, each shrinking against its jamb as the original's
   records 1, 2, 23, 24 do). Each half shows the original's texture on each side (vlcwl1LG / D2WlActr and vlcwl1 /
   D2WlActr: both halves the same per side). Events 2 and 13 open both halves (`door 5 open, door 1 open`; `door 12
   open, door 2 open`); event 13 keeps the original's hint "Lever", event 2 none.
4. **The lava wall** (event 35). The original's handler toggles door 43 (the lever plate) and door 53, whose record has
   no vertices and moves nothing; the shipped map's supplement (`6d18_mmmerge.lua`, face 2255 given cog 1 by
   `6d18_1.scene.yml`) makes the face invisible and untouchable, and visible and solid on the next pull. Said with the
   face effects: `evt:lever35` with a condition on `lava_wall_gone`, `hide` and `passable` of `door:lava_wall`, and
   `show` and `solid` in `else_effects`. The leaf never moves (audit: "door 27 is never moved", as door 53 moves
   nothing). The playtest walks south at it: stopped 37 short of it while it stands, through the neck into the alcove
   once it has gone, stopped again after the second pull.
5. **Chest 8.** `chest:c8` with `box_of: chest:c5` holds the original's chest 8 (rolls 6, 5, 3, 1); `evt:chest5` is
   event 48's three paths: chest 5 and qbits 1029 and 1207 (noting map variable `hourglass_chest_opened`) for a party
   without qbit 1029 or once noted, chest 8 (`open_chest`) for a party that comes with qbit 1029. `oymap flow` gives
   the original's three paths. `r6/chest8.yml` plays the second path.
6. **Chests as the original's records**: `random_levels` per roll (5,3,2,1 / 5,5,2,1 / 4,4,3,1 / 4,4,3,2,1 / 6,4,3 /
   4,3,2,1 / 4,3,2,1; chest 8 6,5,3,1) in place of one level per chest, and `trap_level: 1` on chests 2, 3, 5 and 8,
   whose records carry flag 1 (trapped; the damage is the map card's 8 d20).
7. **The bookcase** in words: `condition: {map_var: {name: bookcase_searches, below: 4}}` and `give_item: {one_of:
   [...]}` (was a Lua test and a Lua draw). Its west end `end_surface: bemvwal`.
8. **The exit** is as wide as the original's (256, the landing's whole north wall; was 224).
9. **Spawn 34** (on the lift's top at z 0 in the original) is left where the studio puts it, on the shaft's floor at
   -2048 inside the raised lift: the lead's fault 4, which the studio's code agent fixes; not worked round.

### The lava, decided by the lead

What the original does: its 31 OrFyrLgA faces carry `0x84000110` (fluid 0x10, the step trigger 0x04000000 with event 51,
XY plane, and the stale "picked" bit); **no lava flag**. Event 51 sets map variable 2, event 53 (dry floors) and 52 (on
load) clear it, timer 54 deals 25 magic damage to all every two half-minutes while it is set. The lava flag is
OpenYAMM's own (`6d18_1.scene.yml` adds `0x40000000` and drops the step trigger). So the rebuild keeps the timer alone:
the eleven `floors` are `kind: water`, the word that lowers to the fluid flag alone (the faces are now fluid + step
trigger, as the original's; the indoor shader draws Lava and Fluid faces with the same swirl, and no liquid of
`liquids.yml` matches orfyrlga, so the look is unchanged), and `evt:lava_burn` is the only thing that hurts.

Checked in the playtest: the walk's party regains 80 hit points a second (1000 to 1400 in five seconds, measured), more
than the timer takes, so a bare "is the party hurt" never sees it (the first try failed for that reason; the timer does
fire: `--gameplay-trace` shows event 64 every two seconds). Each check therefore sets the hit points to 1000 and reads
them five seconds later with the party mortal: on the island 1400 (not hurt), on the lava 1350 (two burns of 25), the
same in all six runs.

### Events, of the original's 53

All 53 do the same thing under the same condition (events 2-21, 31-36, 38-62, 90, 91). Since round five: 2 and 13 (both
halves), 35 (the face vanishes and comes back), 48 (chest 8), and 44-50 (per-roll levels, traps). Still Lua, with the
same behaviour: the fountains (56-61; no effect throws an object, `cast` casts spells and the fountains throw gold
too) and the fire wall's player bit (91). One visible difference inside event 35: the lever's picture changes only on
the first pull, because a failed condition skips the preset's own work (doors and picture) and runs `else_effects`; it
is the same switch picture fault as the lead's fault 2.

### Playtest

349 steps (288 in round five). New: the lava checks above; both halves of doors 1 and 23; the lava wall blocked, gone,
back (three `movement_segment` steps at the wall); the escape tiles in another order so that the last puts the party in
the tower corridor; the climb up both turns of the tower's ramps to the landing (the opening walk's waypoints
reversed); the exit (event 25), `select_topic: map_transition_confirm`, and `oute3.odm` asserted at the original's
arrival (15585, 11125). **Passes six runs of six** on the final build (`r6/play6.sh`, logs `r6/final_play_1.log` to
`_6.log`, the same hit points in every run), and `r6/chest8.yml` passes.

### Pictures and the lead's five faults

Start check and nine shots in `output/studio_cal/mm6_6d18/r6/shots/` (tour `r6/tour.yml`; stills, so movement is not
seen). Of the user's five faults: **1 seen** (the levers on the machine room's posts and beside the lift door are flat
plates with a red knob, `04-lever35-post.png`, `07-machine-bridge.png`, `06-lift-lobby.png`); **3 seen** (each chest
front is one stretched picture, `05-chest2.png`, `09-alcove-items.png`); **2, 4 and 5 not seen** (2 and 5 need motion
or a close camera; the lift's top is behind its closed door in the lobby shot). Places this round touched near them:
event 35's picture (fault 2, above), spawn 34 (fault 4, left as built), doors 1/2 and 23/24 (now folding halves; door 1
is the lever room's door by the first lava hall, so it is one of "the doors near the lava" of fault 5: worth a look
once the studio's fix is in).

### Gaps still open

1. **Two rooms in one space** (hall 14 inside passage 46): 0.26 of the 0.3 % still lost (sector 14). No word.
2. **A spawn's height above its floor.** The original's flying monster spawns hover 20 to 256 above the lava (river
   -2240 over -2260, machine room -512 over -768, -2048 over -2260); a spawn stands on a floor. No word.
3. The lead's faults 1 to 5 (studio). Chest fronts in three strips (fault 3) are also what `compare` still names in
   sectors 29 and 42 (`ch1frRE`, `ch2frRE`).
4. Smaller, from `compare_r6/points.json`, none with a word now: the channel hall's door 16 off its pilaster (opening
   flush to a wall's end) and its stairs whose last rise is the bridge (sector 34); the bench's recessed d2wlactr kick
   (sector 42; three platforms could say it, 0.001 %); single-ray texture pairs in sectors 1, 3, 5, 7, 16, 17, 29, 46
   (0.001 to 0.01 % each, not traced).

### Tool defects

1. A switch preset with a `condition` skips its own picture change when the condition fails (`oymap flow` of
   `evt:lever35`: `SetTexture(16, ...)` only on the first path); a toggling lever with two branches cannot flip its
   picture back even once fault 2 is fixed, unless the picture is run outside the condition.
2. `kind: water` is the only word for the fluid flag alone; a lava floor that flows and does not burn (the original's)
   reads as water in the project. A `kind: fluid` (or `burns: false` on lava) would say it.
3. `oymap audit` reports the never-moved `door:lava_wall` as `door.unused` (info), right but worth a word that face
   effects use it.

### For the user: play it

```
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated forge --world mm6 --map cal6d18.blv --assets output/studio_cal/mm6_6d18/play_root --visible --seconds 0
```

(Leave out `SDL_AUDIODRIVER=dummy` to hear the game; `--seconds 0` keeps it open until closed.) The root
`output/studio_cal/mm6_6d18/play_root` is a hard-link copy of `assets_dev` with the final build installed by
`oymap install --root` (its `cal6d18.blv`, `.scene.yml`, `.lua` and `map_stats.txt` are its own files; `assets_dev` is
unchanged). Checked: the game starts on `cal6d18.blv` at the original's party start, (-2688, 1216, 1152) on the
entrance landing, facing east; the exit door on the landing's north wall leads to New Sorpigal.

## Ninth merge lines (2026-11-13, afternoon)

Copy before: `output/studio_cal/mm6_6d18/m9_backup/`.

- **The carved chest** (chest:c1, the original's faces 1908 to 1915 at x -1472..-1408, y 6656..6752): `lid: v`, the
  carved ch3tpbv middle with ch3tplev and ch3tprev ends, as the original's. Picture `output/studio_cal/mm6_6d18/m9_pics/
  sheets/01-carved-chest-above.png`: the middle is right; **the end strips are laid wrong by the studio**: ch3tplev and
  ch3tprev are 64 by 16 and the original lays them with u across the chest's depth (64) and v along its width (16)
  (face 1910: us -1408..-1472, vs -6656..-6672); the build lays u 0..16 and v 0..64 (16 columns of the picture,
  repeated 4 times), so the ends show studded bands, and puts LEv at the low-y end where the original has REv. A studio
  fix (`chests[].lid: v` with the kinds' v strips), not the project's.
- **Faces in one plane** (the lead's request): 11 before, 0 after (the original has 3, elsewhere). Recorded edit:
  `output/studio_cal/mm6_6d18/m9_coplanar_edit.py`. (1) The three teleport tiles (events 31, 41, 42) stood from the
  room's floor through their island's edge, one side in the island edge's plane: now `base: 16, rise: 16` on the
  island, as the original's faces 654 to 657 (-752 to -736). (2) The east branch of the bridge in room s9 overlapped
  the main bridge by 27: it starts at x -1704, where the original's underside (396, 2523) starts. (3) The two flights
  onto the lava channel hall's bridge ran 10 onto it: now from 4032 (5440) to the bridge's end at 4352 (5120), six
  risers of 16 as before. The original's last riser is the bridge's own end (face 1118) and its treads are 64; a flight
  cannot end with a riser on the floor it climbs to (only into a doorway), so the treads are 53 (they were 54).
- **Scores**: 99.7 % before and after (sector-weighted 99.649 to 99.659), offset agreement 0.432 both. Playtest four
  of four after both changes (`output/studio_cal/mm6_6d18/m9_play/`).
- **Audit**: the lines add no finding. Click.silent 6 (the original's 6: the bookcase after four searches, event 62;
  the fire wall, event 91, untitled and silent in the original too). Torches 6torch01 inside the tower's and s37's
  stair slabs (20 across): at the original's places (-520, 896 there, -524 here) against the original's stairs: the
  original has them the same way.
- Installed into `output/studio_play/forge_root` from `output/studio_cal/mm6_6d18/m9_build`.
