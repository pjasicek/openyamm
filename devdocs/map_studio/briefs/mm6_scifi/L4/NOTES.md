# Control Center (MM6 `sci-fi.blv`) as a Map Studio project: notes

Rebuilt on 2026-11-12 per [the rebuild procedure](../../../REBUILD_PROCEDURE.md). Project id `calscifi`, map table row
9713, the original's own frame. 132 rooms, 157 openings, 21 doors, 375 lights, 80 spawns, 14 chests, 10 switches
(one button, nine terminals), 46 events.

The project files are the truth. They were first written by scripts from hand-typed room tables
(`output/studio_cal/mm6_scifi/gen.py`, `gen_extra.py`, `mkplay.py`; scratch, not tracked). Running `gen.py` again
overwrites `rooms.yml`, `objects.yml` and `wiring.yml`, so do not run it after editing them by hand.

## Where it stands

| Round | What changed | `oymap compare` score | distances | textures |
|---|---|---|---|---|
| 1 | shell: 133 rooms from the sector measurements, one theme per room | 90.1 % | 92.5 % | 84.6 % |
| 2 | three doorways the build had put in the wrong wall; the lower hall's riser, core and notch walls; wall bands and per-wall surfaces from the original; the upper hall's ceiling at its mean height; the pit as one room | 93.8 % | 94.2 % | 92.9 % |
| 3 | vault lobby outline, award effect (no geometry of weight) | 93.8 % | 94.2 % | 92.9 % |
| 4 | 20 coffered ceilings (`ceiling_levels`), entry room, west lobby's dropped ceiling | 94.3 % | 94.6 % | 93.4 % |
| final | generator room walls, wider hall window | 94.3 % | 94.6 % | 93.5 % |

Final totals: 2,576 points, 0 without a floor in the rebuild, 8 of the rebuild's 2,585 without one in the original (the
four shafts), mean floor difference 2.9, mean ceiling difference 34.4. Reports and maps:
`output/studio_cal/mm6_scifi/compare_r1` ... `compare_final`.

- `compare.py`: first round 17 in, 14 near, 4 out; last round **17 in, 15 near, 3 out**. The three out are artefacts
  of counting: the original's smallest doorway is a 1-unit door slit, its lowest "sector" a 10-high mover, and the
  rebuild's lower quartile of room area is small because one sector became several rooms (132 rooms for 87 sectors).
- Rooms reached: **132 of 132** with the doors out of the way, 47 at the start (`oymap audit --reach`).
- `oymap solve`: the same doors in the same order as the original, with one difference. The original reaches the
  lower hall at the start (one drops into it through the four shafts in the upper hall's floor); the rebuild reaches
  it one step later, through a door, so the east wing behind the lower hall's east door opens one step later too
  (five steps instead of four).
- Playtest: **passes** (`playtest.yml`, 199 steps, no jumps, no replans). It walks the pit and its stair, the airlock
  and the whole tube, every door, the two interlocks, the button, a container in each wing, the walkway and the
  lower hall's floor, all four ramps to the upper hall, and stands at (-2000, -383) at 1184 and later at the same
  spot at 0.
- In-game pairs: `output/studio_cal/mm6_scifi/ingame` and `ingame2` (20 pairs). Mean edge agreement 0.77 and 0.79.
  Best: repair bay 0.96, west passage 0.94, generator room 0.92, meeting hall 0.91. Worst: lower hall from the
  walkway 0.52, lower hall 0.63, tube 0.66, upper hall 0.68.

## How the levels connect (the reason this map was chosen)

The map's main floor heights are -985 (vault), -452 (the pit), -393 (east hall), 0 (lower hall), 196 (west wing),
393 (corridors round the lower hall), 591 (rooms over the west passage) and 1184 (upper hall and its ring of rooms). The upper hall (floor 1184) stands on the lower hall (ceiling 768), and its ring of corridors stands
over the 393 corridors.

| Connection in the original | Said with | Result |
|---|---|---|
| Ramps: 393 to 788 to 1184, twice (sectors 21+12 and 47+46) | `slope` rooms | exact floors; ceilings level instead of parallel |
| Ramps 0 to -393, -417 to -985, 196 to 0, 393 to 196, 393 to 591 and others | `slope` rooms | the same |
| South stair, six steps 293 to 393 | `slope` with `steps` | exact |
| Rooms above rooms (upper hall over lower hall, lounge over the west passage, corridors over corridors) | stacked rooms | accepted without trouble; 42 pairs of rooms overlap in plan |
| Four shafts 448 square through the upper hall's floor into the lower hall | nothing | **not said**: placeholders |
| Walkway 256 above the lower hall's floor, along its wall | 12 rooms | walls and floors right; one drops off it as in the original |
| Window from the lounge (591) down into the west passage; slot from the balcony room into the low passage | nothing | not said: placeholders |
| Movers that go down: the hatch (door 13) and the plug (door 17) | `slide_down` | exact |

No lift exists in the original. Every door record was read: 22 leaves slide sideways (four pairs of them are double doors), two
sink (13, 17), one slab lifts (23), one is a pressure plate (24), one a button (26); door 22 is named by a script
and does not exist.

## The five worst remaining differences

1. **The four shafts between the halls.** The upper hall's floor is solid. Seen from below (in-game pair
   `walkway-from-above`) and from above (`upper-hall-shaft`) the lit shafts are missing, and the solve differs by
   one step. No word for a hole in a floor onto the room below.
2. **The lower hall's vault.** The original's core spreads into four arched arms that carry a curved soffit from 256
   up to 768; the rebuild has a box core under a flat ceiling. In-game edge agreement 0.52 to 0.70. No curved or
   sloping ceiling, no arch between a pillar and a wall.
3. **The upper hall's ceiling.** An eight-sided pyramid from 1696 at the walls to 2183 at the lantern; drawn flat at
   1940. Sector 5 holds 632 of the 2,576 points and its distances agree on 88 %. No sloping ceiling.
4. **The tube.** 14,600 units of corridor with a six-sided section (floor strip 128 wide, banks sloping up 74, the
   same overhead) drawn as a box 305 wide. Sectors 72, 75 and 76 score 0.76 to 0.86, floors differ 29 to 53 where
   the points stand on the banks. No chamfered section.
5. **Ramp ceilings and the pit's stair.** The ramps' ceilings run parallel to their floors in the original (255
   clear); level ceilings stand up to 536 too high at the low end (sector 21: mean ceiling difference 282; 47: 146;
   46: 104). The pit's stair is one straight flight instead of two flights with a landing, and a 32-wide ledge runs
   round the pit (points there score 0.56 to 0.61).

## Gaps of the vocabulary, most harmful first

1. **A hole in a floor onto the room below.** Sectors 86 to 89: four shafts 448 by 448, 416 deep, at (-1920, -2048),
   (-1920, 1280), (2688, 1280), (2688, -2048), from the upper hall's floor (1184) to the lower hall's ceiling (768).
   Did instead: four `placeholders`. Would have said it: a vertical opening between two stacked rooms
   (`openings` entry with an `outline` instead of a wall, or `shafts`).
2. **An opening cannot name its walls.** The build takes the pair of facing walls with the longest shared stretch
   (the first of two equal ones) and says nothing when that is not the pair meant. Three doorways were built in the
   wrong place before a check of my own found them: balcony room 27 to corridor 28 (a doorway 384 deep through
   solid wall), corridor 42 to the H-shaped room 41 (into the west wing instead of the east), upper hall to
   corridor 10 (into the corridor's alcove). Did instead: split rooms until only the wanted pair is left
   (`s27_east_arm`, `s41_h_bar` and `s41_h_west`, `s10_alcove`), shortened the plate room's ramp from 384 to 240 so
   its end is longer than its side, and split both T-shaped stair heads into three rooms because two rooms can
   have only one opening. Would have said it: `from_wall` and `to_wall` on an opening (and several openings
   between one pair of rooms).
3. **A raised or sunken part of a floor that reaches the room's walls.** `levels` must keep clear of the walls and
   platform outlines 32 clear. Occurs: the lower hall's walkway (12 rooms instead of one level), the pit (sector
   66: the low part is a sunken level with a false 32-wide ledge along three walls), the airlock hall's raised end
   (a room), the generator room's balcony (a beam 128 wide along the wall, because a platform with a `base` may
   not touch the wall either), the bay shelves in sectors 14, 17, 18, 20, 63, 64 (99 high, left out). Would have
   said it: a level whose outline may run along the walls (the floor split along a line), and a `balconies` entry.
4. **Ceilings that are not level.** The upper hall's pyramid; every ramp (sectors 6, 12, 21, 24, 32, 33, 36, 44,
   45, 46, 47, 53, 59, 60); the shallow vault of the 1184 corridors and of the entrance corridor (452 to 551, drawn
   at the top); the lower hall's soffit; the west porch (256 rising to 888). Would have said it: `ceiling_slope`
   beside `slope`, and a `vault` profile for a corridor.
5. **A chamfered room section.** The tube (sectors 72 to 76, 90, 91). Did instead: boxes with the bank textures as
   wall bands. Would have said it: `section: {chamfer: [run, rise]}` on a room or path.
6. **Doors that slide sideways, and double doors.** 18 of 21 doors; all lift instead. Would have said it:
   `kind: slide_left | slide_right | split`.
7. **A door event that also moves other doors, and floor triggers.** The two porch doors shut each other and the
   three storage rooms shut each other; the `door` preset moves only its own door and the `switch` preset refuses a
   door as its source, so the wiring carries Lua lines with door numbers copied from `ids.lock.yml`. The pressure
   plate of the plate room (door 24) and the tube's 15 floor plates that switch its lights (events 38 to 52,
   `SetLight`) have no word at all: the plate is a placeholder and the store door opens on a click; the light
   plates are left out. Would have said it: `opens`, `closes`, `toggles` on the `door` preset; a `plates` object
   with a `plate` preset; a `lights` effect.
8. **Two openings one above the other in one wall.** The lounge's window over the west passage's mouth (sectors 62
   and 9) and the slot over the low passage (35 and 60). Holes of one wall are checked along the wall only. Did
   instead: placeholders.
9. **A ramp or a flight inside a room that ends at a doorway, and a flight to a landing in a sunken level.** The
   plate room's ramp up to its west door's sill (a room of its own with walls along its sides) and the pit's first
   flight (left out). Would have said it: `flights` and a `ramps` entry that may end at a wall, on a sill.
10. **Two open mouths side by side in one wall** must stand 16 apart, so one room cannot open on a row of rooms
    without piers between them (met while drawing the pit as rooms; avoided in the end).
11. **Small ones.** A spawn's encounter index (the original uses 1, 4, 7 and 10; only the slot is kept). A light's
    type (the original's are type 5, the build writes 0; the rebuilt pictures are darker by a gain of 1.1 to 2.5).
    A message window (`evt.SetMessage`) for the terminals: the `switch` preset's `text` shows a status line. An
    effect for every member (`ForPlayer(All)` before the award of event 34). Arched arms of a pillar.

## Tool defects

- **Wrong wall pair, silently.** `oymap build devdocs/map_studio/briefs/mm6_scifi/L4` with `s27_upper_room_s` drawn
  as the original's seven-point outline and one opening to `s28_upper_corridor` builds a doorway 384 deep between
  the room's notch and the corridor instead of at their touching ends; `oymap compare` then lists
  `floor_only_in_rebuild` at (-5632, -1792, 591). No warning. A check that the opening's `along` is reachable, or
  a warning when two candidate pairs exist, would have caught all three cases.
- **Order of `levels` decides whether they can be cut.** With the upper hall's 16 sunken panels in measured order
  (the triangle `[[-2688, -2304], [-2176, -2816], [-2176, -2304]]` third), `oymap validate` says
  `rooms[1].levels[2]: the region cannot be cut out of room:hall_upper`; with the four triangles last it validates.
- **A platform inside a sunken level stands at the room's floor.** In `s66_pit` (floor -196, level -452) a platform
  `{at: [-7022, 6831], size: [256, 478], rise: 144}` and a flight to it give `oymap validate`:
  `flights[0]: ... (to: here -452 to -452)`. `IndoorLowering.cpp` adds the platform's region before the level's and
  measures its top from `baseFloorAt`, though the schema says "what stands inside the outline stands on the level".
- **A chest of no height passes `validate` and breaks `build`.** `size: [64, 16, 0]` far from the origin gives
  `the indoor compiler refused the lowered map: indoor source UV exceeds native int16 range in TRIGGER_c3b`.
- **A warning with no cause.** `oymap build` (since mid-session) warns for 43 openings: "is in a wall without
  thickness and leaves wall round it ... one will show through the other". In all of them one room's wall is
  wholly open (a corridor's end) and only the other keeps wall round the hole; the in-game pairs
  `zero-wall-s26-s65`, `zero-wall-hall-s7`, `zero-wall-s23-s25` show nothing showing through. Following it would
  move 43 measured walls by 16.
- **`oymap solve` counts a doorway as its `from` room.** With the tube's exit door drawn from `s72_tube` to
  `s22_west_junction`, `oymap solve` lists the tube's last room at step 0, before its door opens, while the next
  tube room is not reached; with the opening turned round it is right.
- **`oymap compare` stands inside movers and on level edges.** Its worst points are (-3584, 512) in the plug,
  (-7424, 2560) in the gate slab, (-9728, -2816) and (-4352, 4352) in door leaves, and two rows of the upper hall
  (y 1536 and y -1792) that lie exactly on the edges of sunken panels, where it reads the original at 1184 and the
  rebuild at 1120 ("the floor is 64 lower") and then finds the hall's windows shut.
- **`oymap export`**: a sector's `lights` list does not seem to index the map's `lights` (light 93 at
  (-9664, -2752) is listed under sector 75, the tube). Not followed up.
- **`ingame_compare.py`** installs into `output/studio_slice_root` unless `--root` is given, one root for every
  agent working at once; I used `--root output/studio_cal/mm6_scifi/root`.
- `oymap build` leaves a `build/` folder in the project folder, which git does not ignore.

## Unsure in the original

- Whether the shafts are meant as a way down. `oymap solve` reaches the lower hall at the start, which only a drop
  through them explains (the stair passages to the walkway open later).
- Container contents: the original's 14 used chests hold fixed items in the map's saved state (`raw_items_hex`); I
  did not decode them, and each container here rolls three random items of treasure level 5.
- Chest events 29, 32, 33 and 36 are also bound to faces far from their box (shelf tops in sectors 18, 20 and 64,
  one face of a neighbouring box in sector 57). I took them for leftovers and built one box for each chest.
- Event 1 ("The door won't budge") is bound to faces of three doors (sectors 6, 39, 43); I kept it on the door
  behind the meeting hall only. Events 3, 16 and 27 are door handlers bound to nothing. Events 62 to 64 ("It's a
  short circuit!", 200 fire damage) and 71 (Sparks across storage room 2) are bound to nothing I could find; 71 is
  a placeholder.
- The H-shaped room's west wing has a second door place with a portal 51 wide and no door record; not built.
- Sector 92 is one loose face carrying the `trekscon` texture; not built.
- 17 of the 392 lights stand inside what are walls or shafts here and were dropped.

## Round two (2026-11-12, later the same day)

The sections above describe round one and are left as written; where they say "not said" for the shafts, the two
stacked openings, the ramp ceilings, the upper hall's pyramid and the lower hall's vault, this section replaces them.
The project files were edited by hand; `gen/` and `output/studio_cal/mm6_scifi/*.py` were not run. Scratch data of
this round: `output/studio_cal/mm6_scifi/r2/` (`compare_0` before, `compare_1` ... `compare_final`, `ingame/`,
`loop.sh`, the measuring scripts `sec.py`, `tex.py`, `rank.py`). Round one's `compare_r2` folder was not overwritten.

### Scores

| | `oymap compare` | distances | textures | mean ceiling difference | points lost (of 2,557) |
|---|---|---|---|---|---|
| Start of round two (same project, today's tool) | 94.4 % | 94.7 % | 93.6 % | 34.6 | 144.0 |
| End of round two | **96.6 %** | **96.7 %** | **96.6 %** | 15.8 | 86.0 |

- 0 points without a floor in the rebuild, 0 of the rebuild's 2,572 without one in the original (8 before: the shafts).
- `compare.py`: 18 in, 14 near, 3 out (17, 15, 3 before).
- `audit --reach`: 132 of 132 rooms with the doors out of the way, 48 at the start.
- `solve`: **four steps (0 to 3), like the original**; the lower hall is reached at the start through the shafts and
  its two porch doors now open in step 1, as the original's event 2 does.
- Playtest: **passes**, 218 steps, no replans, no jumps (`output/studio_cal/mm6_scifi/run/walk_r2.log`). New steps
  walk into the south-west shaft at (-1920, -1500, 1184), land at (-1922, -1938, 0) in the lower hall and climb
  back by the west passage, the generator room and the two south-west ramps.
- In-game pairs (`r2/ingame`, 10 pairs, mean edge agreement 0.81): upper hall under the pyramid 0.93, upper hall
  at a shaft 0.86, under a lower-hall arch 0.87, C-shaped store 0.86, south corridor's vault 0.83, south-west ramp
  0.82, west ramp with the lounge's window 0.79, lounge 0.71, lower hall from the walkway 0.71 (0.52 in round one),
  lower hall's arches 0.68 (a monster stands in front of the rebuild's camera). All sheets were looked at.

Score after each change: shafts and pyramid to the lantern's rim 94.2 (see below), pyramid to the sky's height
95.1, lower hall's arches 95.9, ramp ceilings 96.1, the two stacked openings 96.2, corridor and tube ceilings 96.3,
C-shaped store 96.4, generator room's pipe panels 96.5, landings and the two long upper corridors 96.6.

### What changed

1. **Four shafts** as `in: floor` openings with `at` and `size` (`open:hall_shaft_ne`, `_nw`, `_se`, `_sw`); the
   four placeholders are gone. The hall theme's `reveal` is the shafts' wall texture (swll4dk).
2. **Upper hall's ceiling**: `ceiling: 1696` with one whole-ceiling level whose `top_outline` is the lantern's
   measured octagon. See the first gap below for the height of its top.
3. **Lower hall's vault**: the four arched arms as 24 raking beams (`bottom`, `bottom_end`), three for each haunch
   at the original's stations 256, 473, 671, 768, 768 wide. Sectors 1 to 4: 0.946 to 0.969 before, 0.992 to 0.994 now.
4. **Sloping ceilings** (`ceiling_slope`) on eleven rooms: both first rises of the stacked ramps (s21, s47), the east
   ramp (s6), the west ramp and its porch as one plane (888 to 593 to 256), s32, s36 (passage and ramp), s45, the
   low ramp s60 and the tube's entry ramp s91.
5. **Two stacked openings**: `open:lounge_window` (lounge over the west passage's mouth, `sill: 128`) and
   `open:balcony_slot` (98 high, `sill: 110`, over the low passage's mouth); both placeholders are gone.
6. **Ceilings that narrow as they rise**: the south corridor (s8), the entrance corridor (s65) and five tube runs
   (s73 to s76, s90) as whole-ceiling levels with a ridge `top_outline`; the north and east upper corridors (s10,
   s11, not convex) as levels with an outline 16 inside the walls.
7. Round-one mistakes found on the way: the C-shaped store's girder is the edge of three ceiling coffers, not a
   wall band (texture agreement 0.75 to 0.91); both ramp landings had their ceiling at 1184 instead of 1539; three
   of the upper hall's triangular panels are swrdk2; the generator room's four pipe panels (outline points added on
   the walls so each panel is a wall of its own).
8. No teleport exists in the original (`flow` lists none), so no switch-sourced teleport was needed.

### New features: what worked and what did not

Worked as described, first try: `in: floor` with `at` and `size` (built, seen from both rooms in the game, fallen
through in the playtest, ridden by `solve`); `ceiling_slope` on ramps and on level rooms, with openings in the end
walls; `top_outline` on a whole ceiling and on an outlined level; raking beams; an opening above another in one wall,
by `sill` and by the upper room's higher floor, also across a wall 135 thick. `from_wall` and `to_wall` were not
needed. `teleport` and `script` presets were not used.

Did not, or has a limit worth knowing:

- **A beam may pass through the ceiling, unseen by any check.** A raking beam with `depth` larger than the room
  above its underside builds without a warning; its faces stand in the room above (they are in the lower room's
  sector, drawn whenever that sector is seen, here through the shafts) and `compare`'s rays hit them: the upper
  hall fell from 0.928 to 0.905. Repro: `output/studio_cal/mm6_scifi/repro/beam_through_ceiling` (`validate`: no
  issues; the lower room's sector holds faces up to 992 under a ceiling at 512 and a floor above at 768). Wanted:
  the beam cut at the ceiling, or an error. Here each depth is chosen so the low end meets the ceiling.
- **A whole-ceiling level allows no second level, and levels may not stand in each other**, so a lantern on a
  pyramid cannot be said. Repro: `repro/lantern_on_pyramid`: "rooms[0].ceiling_levels[1]: the region cannot be cut
  out of room:hall: keep it inside the room and clear of its walls and of the room's other regions" (with both
  levels outlined), and "a ceiling level without an `outline` is the room's whole ceiling: the room can then have no
  other ceiling level ..." (as documented).
- **An opening in the end wall of a ridge ceiling is held to the eaves' height**, though the wall there stands to
  the ridge. Repro: `repro/ridge_end_opening`: "openings[0].height: the opening reaches 288 but the lower ceiling of
  its two rooms is at 224". So every tube joint and corridor end under such a ceiling has a lintel the original
  lacks (77 in the tube, 99 in the corridors); the south gate passage (s7) and the tube's exit run (s72), short
  rooms open at both ends, were left flat for that reason, and 20 openings went from a number to `height: full`.
- **Misleading follow-on messages**: the same repro then prints "objects.yml: doors[0].opening: there is no opening
  open:end in rooms.yml" and "wiring.yml: events[0].source: there is no object door:end in objects.yml", though
  both exist.
- **A level's leaning sides take the wall's surface by default**; in this map every chamfer is ceiling texture, so
  each needs `edge`. Under a ridge the natural default would be the ceiling's.
- `walls[].surface` applies above the room's bands only, and bands are the same on every wall: a wall cannot have a
  dado of its own.

### Gaps still open, most harmful first

1. **The lantern's drum on the pyramid** (upper hall, sector 67: drum 197 high from 2183 to 2380). Two honest
   choices were measured: the pyramid at its true pitch ending in a flat sky at 2183 scores 94.2 % in all (the sky
   is 197 low over 44 % of the hall), the pyramid run on to the sky's height 2380 scores 95.1 %. The second is in
   the project, and it is a misstatement of the pitch (30 degrees for 22): the eaves, the lantern's outline and the
   sky's height are right, the slope's faces stand up to 197 too high at the rim. With a level on a level it is one
   number back (2183) and one more entry.
2. **`compare` on the edges of the upper hall's sunken panels** (a tool defect, listed in round one, now the
   largest single loss): 45.5 of the 86.0 points still lost are in sector 5, and its map (`r2/compare_final/
   geometry.png`) shows them only on the grid rows y = 1536, 0, -1792, -3840 and the column x = 768, which are panel
   edges; there the tool reads the original's floor at 1184 and the rebuild's at 1120 ("the floor is 64 lower",
   about 83 points), though the built panel polygons equal the original's point for point. Every other point of
   the hall is green.
3. **The pit** (sector 66, 4.6 points): the stair of two flights with a landing inside the sunken level, and the
   false 32-wide ledge; unchanged from round one (a level touching the walls; a platform in a sunken level).
4. **The tube's banks** (sectors 72 to 76, 90, 91, about 7 points): the ceiling half of the six-sided section is
   now said, the floor's sloping banks are not (floors differ 29 where points stand on a bank), and the corners keep
   box ceilings.
5. **Openings at vault ends** (above), and the vault over a bent or a sloping corridor: s10's and s11's stubs to the
   hall, the gate passage s7, both upper ramps s12 and s46 (ceiling difference 28 and 104) stay flat.
6. **A dado on one wall, and a wall under a window's sill**: the C-shaped store's two wall textures under one girder
   (solved here by the coffers), the lounge window's parapet (panel texture toward the ramp; the ramp's wall here).
7. **The shafts' rim** (a 32-wide swhorzdb border in the floor round each hole) and a `reveal` of its own for a floor
   hole (it takes the room theme's, which the hall's doorways share).
8. Unchanged from round one: sliding and double doors, door events that move other doors, floor triggers and the
   tube's light plates, the bay shelves, light type, spawn encounter index, message windows.

**Lead's correction after round two:** the upper hall's pyramid was run up to 2380 because that scored higher; it is
set back to the lantern's rim (2183) at the true pitch. A wrong shape that measures better is the trick the
procedure forbids. Score with the true pitch: 95.7 % (distances 95.4 %, textures 96.5 %). The lantern needs a
ceiling level standing on a whole-ceiling level, which is on the list.

## Round three (2026-11-12, night)

The sections above are left as written; this one replaces them where they differ. The project files were edited by
hand. The one-off helpers that changed them are kept with their inputs in `output/studio_cal/mm6_scifi/r3/`:
`doorside.py` (reads the door records and says left or right; changes nothing), `doorkinds.py` (the 18 door
kinds), `rewire.py` (the wiring attempt that was refused, then set back by hand), `walltex.py` (measures wall
textures per plane). Snapshots of the project after each group of changes: `r3/snap_doors`, `snap_wired`,
`snap_panels`, `snap_events`. Measurements: `r3/compare_0` (start) to `compare_11` and `compare_final`; `solve_N.txt`
beside them. Round one's `compare_r3` folder was not overwritten.

### Scores

| | `oymap compare` | distances | textures | mean ceiling difference | points lost (of 2,557) |
|---|---|---|---|---|---|
| Start of round three | 95.6 % | 95.4 % | 96.2 % | 24.3 | 111.9 |
| End of round three | **97.8 %** | **98.1 %** | **97.1 %** | 2.4 | 56.4 |

- 0 points without a floor in either map; mean floor difference 2.9 (unchanged).
- `compare.py`: 18 in, 14 near, 3 out (as in round two).
- `audit --reach`: 132 of 132 rooms with the doors out of the way, 48 at the start.
- `solve`: four steps (0 to 3) with 48, 58, 23 and 3 sectors, the original's order (porch doors in step 1, the vault
  and the button's room last).
- Playtest: **passes**, 221 steps, no replans, no jumps (`output/studio_cal/mm6_scifi/run/walk_r3b.log`). New in it:
  the party walks onto the pressure plate and the store door must be open three seconds later (no click); both
  leaves of the two porch doors are checked.
- In-game pairs (`r3/ingame`, 10 pairs, mean edge agreement 0.82, all sheets looked at): generator room's west wall
  0.96, hall's south wall 0.96, upper hall under the pyramid 0.94, west lobby 0.89, north corridor 0.81, C-shaped
  store's windows 0.81, tube 0.80, upper hall at a shaft 0.76, storage door 0.66, airlock hall's windows 0.61. The
  low ones differ in brightness (the rebuild 1.4 to 2.5 times darker, the light type of round one) and, at the
  shaft, in its missing rim; their walls, pilasters, windows and leaves line up.

Score after each change: lantern drum 97.6; landing and second flight in the pit (refused, set back) 97.6; door
kinds, plate and rewiring 97.6; tube chamfers' texture 97.7 (textures 96.7); panels on the hall's south wall and the
north corridor 97.7 (96.9); west lobby, airlock hall and C-shaped store panels 97.8 (97.1); generator room as panels,
the lounge window's sill strip, the two spark events 97.8 (97.1).

### What changed

1. **The lantern's drum** (sector 67) as a second ceiling level standing on the pyramid's flat top: 2183 to 2380,
   swfloor2b sides, sky at 2380. The pyramid keeps its true pitch. Sector 5 went from 0.890 to 0.969 and its mean
   ceiling difference from 88.5 to 0; the whole map's from 24.3 to 2.4. This one entry is most of the round.
2. **The tube's chamfers** (s73 to s76, s90) were textured swflorb: the fix batch changed a leaning side's default
   from the wall's surface to the ceiling's, and round two had relied on the old default. Each now has
   `edge: swll4dk` as the original (two sloped faces per run, SWll4dk).
3. **Panels where a wall changes texture along its length**, all measured from the original's faces (`walltex.py`
   lists every original wall plane with more than one texture): the upper hall's south wall (swll5 for 768 round the
   south gate), the north corridor (swll5dk for its east 1,114), the west lobby (swall5 only on the middle 384 of its
   two long walls, 316 high, where round one had a band on all four walls), the airlock hall's south wall (five
   swgirder pilasters, swrdk2 sills 24 high and swr1dk lintels 16 high at its two windows), the C-shaped store's side
   of the same wall (pilasters and sills) and its east wall's swall1 stretch, the generator room (its outline from
   14 points back to its 8 corners; the four swpipes panels and the swr1dk strip over the west lobby's doorway are
   panels), and the swildk2 strip between the west passage's mouth and the lounge's floor. The west window was moved
   1 unit (`along` 0.696 put it at -11057). Built faces checked against the original's: every panel lands on the
   original's edges.
4. **Moving parts as they are.** The 14 single leaves are `slide_left` or `slide_right`, each toward the jamb its
   record's direction points at (`doorside.py`: the leaf is stored closed, its free edge moves along the record's
   direction). The four double doors (airlock 27/28, east porch 2/3, tube exit 10/11, west porch 15/16) are
   `leaves: 2`. Gate slab 23 (lifts), hatch 13 and plug 17 (sink) were already right. The pressure plate (door
   record 24, event 24) is a `plates` entry (128 square, 1 high, swrdk2) whose `trigger: step` event toggles the
   store door; its placeholder is gone and the store door still opens on a click as the original's event 25 does.
5. **Two traps that round one had not found.** Event 71 is not "bound to nothing": GrayFace's script and the
   exported Lua run it on a timer every three half-minutes (Sparks, skill 100, Master, across storage room 2). It is
   now `evt:spark_trap` (`trigger: timer, every: 3`), and its placeholder is gone. Event 47 (the tube's south-west
   corner square, face 2589, which is exactly the corner room's floor) also casts Sparks down onto the south-east
   corner: `evt:tube_sw_sparks` (`trigger: step`, the corner room as source). Both are Lua lines (see the defect on
   `cast` below). Neither can be observed by the playtest (`assert projectiles` sees actors' and the party's only);
   both are in the built Lua, the timer in its `timers` table exactly as in the original's.

### New features: what worked and what did not

Worked first time: a ceiling level standing on another's flat top; `panels` with `offset`, `from: end`, `bottom`
and `height` (cut round openings and placed over and under them, as described); `slide_left`/`slide_right`;
`leaves: 2` (the second leaves are numbered in ids.lock.yml, both move with one click, the playtest checks them);
`plates` with a `trigger: step` switch preset (walked in the game); `trigger: timer` with a script preset; `trigger:
step` with a room as its source. Not needed here: `ends`, `back_surface`, `tread`, `top_surface` on flight sides,
`threshold`, a climbing `path`, `movers`, lifts (the original has none of these; its four double-door porches have
the same texture both sides).

Refused or wrong:

- **A flight to a platform inside a sunken level is refused, though the build places the platform right.** The
  pit's landing (platform 256 by 478, rise 144, inside the -452 level of a room at -196) and its two flights:
  `rooms.yml: rooms[85].flights[0]: a flight runs from a point on the lower floor (`from`) to a point on the higher
  one (`to`: here -52 to -196), in steps of at most 40`, and `flights[1]: ... (`to`: here -452 to -52)`. With
  `to_height` set to the platform's true top: `rooms[0].flights[0].to_height: there is no floor at -112 at the
  flight's `to` point: the floors there are at -256, 144 (the room's floor and the tops of the levels, platforms and
  steps that hold the point or have it on their edge)`. Built without the flight, the same platform's top is at -112
  (on the level). Repro: `output/studio_cal/mm6_scifi/repro/platform_in_sunken_level` (`oymap validate` on it). The
  flight check measures platform tops from the room's floor; the fix batch moved only the build.
- **A door event cannot move other doors without copied numbers.** A switch preset on a door is refused:
  `wiring.yml: events[1].source: a switch preset cannot have the door door:west as its source`; `closes:` on a door
  preset passes `validate` and the build drops it without a word (the handler only triggers its own door). Repro:
  `repro/door_preset_closes` (`build`, then read the Lua; the refused variant is `wiring_switch_on_door.yml.txt`).
  So the porch and storage handlers keep Lua lines with numbers from ids.lock.yml, now four of them per porch door
  because each has two leaves (east porch shuts 21 and 25, west porch 3 and 23).
- **The `cast` effect writes its arguments in the wrong order.** The game's `evt.CastSpell(spell, skill level,
  mastery, from, to)` (the exported original: `CastSpell(15, 100, 3, ...)`, GrayFace: Mastery Master, Skill 100);
  `{cast: {spell: 15, ..., mastery: master, level: 7}}` builds `evt.CastSpell(15, 3, 7, ...)`, skill 3 at mastery 7.
  The test map's fire bolt (`mastery: expert, level: 1`) is skill 2 at mastery normal. Repro:
  `repro/cast_mastery_swapped`. Also, `level` cannot reach the original's skill 100 through the mastery slot. Both
  traps here are Lua lines with the original's numbers for this reason.
- **A changed default re-textured an existing project without a message**: the leaning sides' default (wall surface
  to ceiling surface) turned the tube's five chamfers from swll4dk to swflorb between round two and round three.
  `oymap build` of round two's project said nothing; only `compare`'s texture pairs showed it (swll4dk against
  swflorb, 407 rays).

### Gaps still open, most harmful first

1. **`compare` on the edges of the upper hall's sunken panels** (a tool defect, see round two): 18.3 of the 56.4
   points still lost are in sector 5, and all 28 of its worst points lie exactly on panel edges with the floor read
   64 apart (`r3/compare_final/report.json`, `worst_points`). The geometry there agrees with the original point for
   point.
2. **The pit** (sector 66, 4.6 points): the original's stair of two flights with a landing (blocked by the defect
   above) and the false 32-wide ledge, because a level may not reach the room's walls. Field: a level whose outline
   may lie on the walls (the floor split from wall to wall).
3. **The tube's floor banks** (sectors 72 to 76, 90, 91, about 6 points; floors differ 29 where points stand on a
   bank) and **the lintels at its joints**: a run and its corner are one sector in the original, here two rooms, and
   the opening between them stops at the eaves (621) under a ridge to 698, because a rectangular opening may rise into
   a gable only to 16 under its top line at the opening's sides. Fields: a chamfered section (`section: {chamfer:
   [run, rise]}`), and an opening shaped like the section it joins.
4. **Light switching** (the tube's 15 floor triggers, events 38 to 52, and the lights half of event 47): there is no
   light effect and lights have no numbers in ids.lock.yml. Field: an effect `lights: {on: [light:...], off: [...]}`.
5. **Door events that move other doors** (events 2, 15, 7 to 9): Lua with copied numbers, as above. Field: `opens`,
   `closes`, `toggles` honoured on the door preset, or a switch preset sourced on a door.
6. **Sliding leaves that shrink against their jamb.** The original's sci-fi doors are stretched faces: the free edge
   moves, the fixed edge stays, so a doorway may be as wide as its wall. The east porch's and the airlock's doorways
   are 512 wide in the original (leaves y -640 to -128 and 3377 to 3889) and stay 256 here, because two leaves of 256
   need 256 of wall on each side and the hall's notch leaves 128. Field: a door kind that shrinks rather than slides
   into a pocket.
7. **The shafts' rims and bands**: a 32-wide swhorzdb ring in the floor round each hole and swhorzad bands 32 high at
   the top and bottom of each shaft (sectors 86 to 89); in-game pair `upper-hall-lantern`. Fields: a floor panel, and
   bands on a floor hole's sides. (A ring of four plates without an event would draw it; not done: plates are
   triggers.)
8. **Per-leaf surfaces of a two-leaf door**: the west porch's leaf 15 is swaled/swared, leaf 16 swpnl. Field: a
   surface for the second leaf.
9. **The west lobby's ceiling** (sector 25): a flat middle at 512 between two 128-wide end strips vaulted to 610;
   here a 384-wide beam under a flat 610. Splitting it into three rooms would trade the beam for jambs and lintels at
   the two vault ends (the gable limit of gap 3).
10. **A sloping sill**: the lounge window's sill is a wedge inside the lounge (591 at the window to 719 at 170 in);
    here a 128-high upright sill. And a ceiling lower over part of a room (the plate room's east notch, 460 under
    724; face 1270): a ceiling level can only rise.
11. Unchanged from round one: the bay shelves, light type (the brightness gain in every pair), spawn encounter index,
    message windows, the 25-deep niches between the airlock hall's windows.

### Tool defects (new this round)

- `oymap validate output/studio_cal/mm6_scifi/repro/platform_in_sunken_level`: the flight check measures a
  platform's top from the room's floor though the build stands it on the sunken level (above).
- `oymap build output/studio_cal/mm6_scifi/repro/door_preset_closes --assets assets_dev --out <dir>`: `closes` on a
  door preset validated and dropped.
- `oymap build output/studio_cal/mm6_scifi/repro/cast_mastery_swapped ...`: `CastSpell(15, 3, 7, ...)` for mastery
  master, level 7.
- `ingame_compare.py` has no pitch, so a ceiling (the lantern) cannot be pictured from below; the shots stand level.
- `oymap script-reference` lists no `evt.*` functions (no `SetLight`, `SetDoorState`, `CastSpell`), so what a Lua
  line may call has to be read from the shipped maps' Lua.

### Unsure

- Whether the original's event 47 Sparks is meant to land in the far corner: it is cast from (-10880, -4224, 660)
  straight down, 3,000 east of the plate that runs it. Kept as it is.
- Events 62 to 64 ("It's a short circuit!", 200 fire damage) are still bound to nothing and on no timer; not built.

### Score against shape

Nothing in this round was moved away from the original's measured shape. Two things that would have scored higher
were left: nudging the upper hall's panel outlines off their true lines would hide `compare`'s edge defect (18
points), and plates without events would draw the shafts' rims.

## Round four (2026-11-12, night)

The sections above are left as written; this one replaces them where they differ. Brief:
`devdocs/map_studio/rounds/ROUND_FOUR.md`. The project as it stood before this round: `output/studio_cal/mm6_scifi/r4_backup/`;
before the vault change: `r4/snap_before_vaults/`. Scratch of this round: `output/studio_cal/mm6_scifi/r4/`
(`compare_1` ... `compare_6`, `compare_final`; the start is `../compare_r4_start`; `ingame/`, `ingame2/`).

Scripted edits, each number measured from the original's export (`r4/sec.py` prints a sector's faces) and every diff
checked: `r4/tubes.py` and `tubes2.py` (the tube runs, the entry ramp, the airlock strip, the mouths),
`r4/fixlights.py` (66 light heights set so the built z equals the original light's z at the same x, y; `lightz.py`
checks it: 0 of 375 off by more than 8 now, 66 before, most from round one, up to 256 off), `r4/vaults.py` (sectors 12
and 46). The rest by hand.

### Scores (the corrected measure)

| | `oymap compare` | distances | textures | mean floor / ceiling difference | points lost (of 2,556) |
|---|---|---|---|---|---|
| Start of round four | 98.5 % | 99.0 % | 97.3 % | 2.9 / 2.4 | 36.5 |
| End of round four | **99.0 %** | **99.5 %** | **97.9 %** | 0.1 / 1.8 | 24.1 |

After each change: tube sections 98.7 (tube sectors 0.76-0.98 to 0.96-1.00); pit with its stair 98.9 (sector 66 0.954
to 0.999); light heights, events as words, door back faces (no change in the measure); the plate room's ramp 98.9
(sector 55 0.920 to 0.992); vaults of sectors 12 and 46 99.0 (0.967 and 0.963 to 1.000).

- Rooms 130 (132 before: + `s72_tube_door`, `s91_airlock_strip`; - `s55_door_ramp`, `s12_ramp_landing`,
  `s12_ramp_up_2`, `s46_ramp_landing`). `audit --reach`: 130 of 130 with the doors out of the way, 45 at the start.
- `solve`: four waves (0 to 3) with 45, 59, 23 and 3 rooms, the original's order (porch doors in wave 1, the vault and
  the button's room last). `compare.py`: 18 in, 14 near, 3 out (unchanged).
- Playtest: **passes**, 239 steps, no replans, no jumps (`output/studio_cal/mm6_scifi/run/walk_r4.log`). New steps:
  the pit's stair (seven steps down to the landing at -308, nine down to -452, asserted on the landing and at the foot,
  and back up), the pit's south-east corner where round three had a false ledge, up the tube's east bank in the west
  run (stood at 428, 35 up the bank), the plate room's ramp entered from its open side (239 at x -9424), the middle of
  sector 12's ramp under the vault (979).
- Upper hall (sector 5): with the corrected measure it loses 1.1 points of 632 (0.998). Round three's 18.3 points on
  the sunken-panel edges were the measure's; what is left there is the shafts' swhorzdb rims and views through
  doorways.
- In-game pairs, all sheets looked at: `r4/ingame` (8) and `r4/ingame2` (7). The tube now has the original's eight-sided
  section in every picture (edge agreement 0.55 to 0.63: the shape lines up, the swll4dk pattern runs at another phase
  along the walls); the airlock's mouth 0.90; the pit 0.78 to 0.90; the vaults of sectors 12 and 46 0.89, 0.90, 0.99;
  the plate room's ramp 0.81. Brightness gains are 0.85 to 1.29 now (1.4 to 2.5 in round three's pairs).

### What changed

1. **The tube** (sectors 72 to 76, 90, 91) as `path` rooms with a `section`, measured from the original's faces for
   all seven runs: the given section `[[-64,0],[64,0],[154,74],[154,228],[64,305],[-64,305],[-154,228],[-154,74]]`
   holds within 1 unit for runs 72, 73, 74, 76 and 91 (walls 153 and 154 from the strip's middle); runs 75 and 90 are
   not centred on their strip (147 and 160; 146 and 159) and have their own sections. The corners stay box rooms, as
   in the original (each corner is one sector with the run before it), and each run meets them with a
   `shape: section` mouth: no lintels at the joints (round three's 621-to-698 lintels are gone), and the banks are
   floor. The entry ramp is a climbing tunnel (`path` points with z, 393 down to 240). Its mouth into the airlock rises
   to 545 over an airlock 492 high: in the original the airlock's west 64 has its ceiling at 545 (swGIRDER), so that
   strip is now a room of its own (`s91_airlock_strip`), and the airlock's ceiling is swankdk as the original's (round
   one had swll4dk). The exit run's last 48 (x -7748 to -7700), where the original's sides run from the section to the
   door passage's smaller octagon, is a box room `s72_tube_door`. Round two's five chamfer ceiling levels are gone.
2. **The pit** (sector 66): the room's floor is the low floor (-452); the west part (-196) is a platform standing
   against the south, west and north walls (a platform may touch the walls; a level may not), so round three's false
   32-wide ledge is gone; the landing (-308) is a platform; the two flights are the original's (nine steps of 16 north,
   99 deep, then seven west, `from_height: -308`). Every tread lands on the original's to the unit (built faces
   checked). Each flight's `to` lies one step inside the floor it climbs to, so that its steps are 99 deep; its top
   step is cut out of that platform so that no two floors lie on each other.
3. **Events as words.** The two Sparks traps (events 71 and 47) are `cast` effects; the built Lua is
   `evt.CastSpell(15, 100, 3, -5632, -4736, 660, -5632, -4000, 660)` and `evt.CastSpell(15, 100, 3, -10880, -4224, 660,
   -10880, -4224, 400)`, the original's calls to the number. The porch doors (`closes: [door:west_porch]` and the
   mirror) and the three storage rooms (`closes` with the other two) are door presets with door lists; no Lua is left in
   the wiring. The built handlers equal round three's Lua lines (both leaves of each two-leaf door).
4. **The plate room's ramp** (sector 55) is a platform with `top_slope` (384 by 256, up 92 to the store door's sill), open
   on both sides as in the original; round one's walled ramp room is gone and the store's doorway is 256 wide, as the
   original's (224 before).
5. **Sectors 12 and 46** are one room each, as in the original: landing, ramp and level passage as `floor_points`
   under the vault as `ceiling_points` (springing at 1440 on every wall, a flat top 196 wide at 1539; every face of it
   is swll5dk, so one surface is right). Their mouths into the hall and into each other are two touching openings, a
   doorway to 1440 and a part 196 wide to 1539 over it (the vault's end less two 99-by-99 triangles).
6. **Light heights**: 66 lights moved to the original's z (the pit's wall lights over the low floor were 256 low; the
   entry ramp's and the four ramps' lights up to 180 high; the upper hall's ring 64 low).
7. **Door faces**: the tube exit shows swor2 toward the tube (`back_surface`), the hatch swtrdk toward the closet and
   swtrpnl toward the ramp, the plug swall3 (the corridor's wall) toward the west corridor. The pit's terminal has
   `floor_height: -196`. The first flight's risers and sides are swll4dk (its sides, the larger part, are swll4dk in
   the original; its risers swrdk2: one surface for both).

### New features: what worked and what did not

Worked first time: `section` paths with asymmetric sections; a climbing tunnel by `[x, y, z]` points; `shape: section`
mouths into box rooms; tunnel banks walked; a platform against three walls with an L-shaped outline; `from_height` on a
flight from a platform; `top_slope` as an open ramp; `floor_points` and `ceiling_points` in one room with `floor_lines`
and `ceiling_lines`; two touching openings as one mouth at a `ceiling_points` vault's end; `closes` on door presets;
`cast` with `level: 100, mastery: master`; `back_surface`; `floor_height` on a switch.

Refused or limited (no new repro needed: each is documented behaviour):

- A section mouth may not rise over the room's ceiling: the entry ramp into the airlock (545 over 492). The original's
  raised strip is the answer, so this cost nothing.
- Inside a sectioned tunnel platforms, lifts, movers and wall switches are refused. Cost here: nothing; the tube has
  none of them. Its 15 light-switching floor triggers (events 38 to 52) are whole floors of runs and corners (faces
  1424, 1583, 1604, 1646, 2578, 2600, 2630 and the corners' floors), so they would be step events on the rooms, which a
  tunnel takes; what they do (`SetLight`) has no word, so they are not built (a trigger that does nothing would be a
  fake).
- A square `end` was not usable for the exit run: its rectangle is the section's height (305) and must open into a wall
  at least as high; the original narrows to another octagon 255 high instead.
- `ceiling_points` gives an uneven ceiling one surface and excludes `ceiling_levels`: see gap 1.

### Gaps still open, most harmful first

1. **The vaulted corridor ring at 1184** (sectors 10, 11, 17, 8, 13, 14: about 6 of the 24.1 points lost): the north
   corridor's stub (x 197 to 593), the east corridor's stub (x 3968 to 4768) and the groined joints where every side
   opening of the east corridor meets its vault, the north-east gallery's east arm and north stub. `ceiling_points`
   would say the shapes, as it does in sectors 12 and 46, but the ridge tops of the north and east corridors are swwala
   (the north one over 5,460) and an uneven ceiling has one surface; side openings would need two-part mouths whose upper
   part enters the neighbour's ceiling (refused where the neighbour is lower: the east cells, the south-east gallery).
   Left as round two built them rather than trading the corridors' swwala tops for the stubs. Field: a surface for a
   region of an uneven ceiling (`ceiling_surfaces: [{outline, surface}]`), or `ceiling_points` beside `ceiling_levels`.
2. **Light switching**: the tube's 15 floor triggers and the lights half of event 47. Field: an effect
   `lights: {on: [...], off: [...]}` and light numbers in ids.lock.yml.
3. **The shafts' rims and bands** (sectors 86 to 89; the rest of what sector 5 loses). Field: a rim or band on a floor
   hole's edge and sides.
4. **A tunnel that narrows into another section** (the exit run, x -7748 to -7636: SWall5 triangles from the tube's
   section to the door passage's octagon, 192 floor, 320 wide, 648 high; then the SWrt2 passage of that octagon with the
   door): a box room and a rectangular doorway here. Field: `end: {section: [...]}` and a doorway of a section's shape
   that carries a door.
5. **Leaves that shrink against their jamb** (the east porch's and the airlock's doorways are 512 wide in the original,
   256 here).
6. **Per-leaf surfaces** (the west porch's leaf 15 swaled/swared, leaf 16 swpnl).
7. **Flights**: risers and sides take one surface (the first flight's risers are swrdk2, its sides swll4dk); a flight
   whose steps are the original's depth must end one step inside the floor it climbs to, so the second flight's top
   tread is swrdk2 where the original's upper floor is swfloor2b (99 by 512). Fields: `side` on a flight; a flight
   whose last riser meets the higher floor's edge.
8. Unchanged: the west lobby's ceiling, the lounge's sloping sill, the plate room's lower ceiling notch, the bay
   shelves, spawn encounter index, message windows, light type, the 25-deep niches of the airlock hall.

### Tool defects (new this round)

- **A misleading index for touching openings.** `oymap validate output/studio_cal/mm6_scifi/repro/vault_end_mouth_197`
  says `openings[0].height: the opening reaches 355 but the lower ceiling of its two rooms is at 354 there`; the cause
  is `openings[1]` (the upper part, 197 wide, half a unit wider than the vault's top). With 196 it validates
  (`repro/vault_end_mouth`).
- **A flight's top step inside the platform it ends on**: `oymap build output/studio_cal/mm6_scifi/repro/
  flight_top_step_inside_platform --assets assets_dev --out <scratch>` builds the step's top (swrdk2) and the
  platform's top (swfloor2b) on one another at 144 (faces 50 and 55 of the export), without a warning.
- **`oymap build <project> --out <scratch>` still writes `ids.lock.yml` into the project folder**, though the brief
  says `--out` avoids it (both repros above; removed by hand afterwards).
- **`ingame_compare.py` took no pictures of the original** three times running (`r4/ingame.log`, `r4/ingame2.log`:
  `original 0 pictures`), once while `build/game/openyamm` was being rewritten (22:23), twice not; the same tour by
  hand (`tools/run_game.sh --isolated ... --set debug.screenshot_tour_path=<folder>/original.tour.yml`) worked each time
  and `--no-game` then measured the pairs. The script hides the launcher's output (`capture_output=True`), so the
  cause is not visible.

### Unsure

- The tube's light triggers' order (lights going off as one walks) was not checked against the game: not built.
- Whether the flow's `close` for a door's own event in this map means the rebuild's `open` (rounds two and three read it
  so, and the playtest's porch and storage checks rely on it): unchanged.

### Score against shape

Nothing in this round was moved away from the original's measured shape. The one place the two could pull apart is gap
1: `ceiling_points` on the north and east corridors would have given their shape and would probably measure about the
same (shape up, textures down); it was not done because it puts a wrong texture over 5,460 of corridor to gain a stub.

## Round five (2026-11-13, night)

The sections above are left as written; this one replaces them where they differ. Brief:
`devdocs/map_studio/rounds/ROUND_FIVE.md`. The project as it stood before this round: `output/studio_cal/mm6_scifi/r5_backup/`.
Scratch of this round: `output/studio_cal/mm6_scifi/r5/` (`compare_1` ... `compare_5`; the start is `../compare_r5_start`;
`ingame/`, `ingame2/`, `ingame_bay_before/`; trial copies `pitsplit/`, `bays/`, `lounge/`; `sec.py` prints a sector's faces,
`worst.py` a sector's worst points, `lightkeys.py` the switched lights' records).

Scripted edits, every number read from the original (its export, its scene file or `oymap flow`) and every diff
checked: `r5/chests.py` (chest contents and traps from `initial_state.chests`), `r5/lights_events.py` (the 15 light
events from `oymap flow`, the floors from the faces' `cog_triggered`), `r5/pitsplit.py`, `r5/bays.py`, `r5/lounge.py`.
The vault ring, the arms, the shelves, the niche, the pins and the playtest steps were written by hand.

### Scores

| | `oymap compare` | distances | textures | mean floor / ceiling difference | points lost (of 2,556) |
|---|---|---|---|---|---|
| Start of round five | 99.0 % | 99.5 % | 97.9 % | 0.1 / 1.8 | 25.8 |
| End of round five | **99.2 %** | **99.7 %** | **98.2 %** | 0.1 / 0.9 | 20.1 |

After each change: vault ring, arms, pins 99.2 (21.7 lost); the pit's upper floor as a room 99.2 (21.7); window bays
99.2 (20.6, textures 98.1); lounge's window end 99.2 (20.5, textures 98.2); shelves and niche 99.2 (20.1, distances 99.7).
Sectors: 7 0.986 to 1.000, 8 0.992 to 1.000, 10 0.969 to 0.996, 11 0.982 to 0.998, 13 0.973 to 0.986, 17 0.951 to
0.980, 14 0.970 to 0.978, 62 0.989 to 0.997, 18 0.932 to 0.962, 63 0.979 to 0.992, 64 0.985 to 0.994.

- Rooms 136 (130 before: + `s17_east_arm`, `s17_north_stub`, `s13_east_stub`, `s13_south_stub`, `s66_pit_upper`,
  `s18_niche`). `audit --reach`: 135 of 136 with the doors out of the way, 50 at the start; the one left is the
  office's niche, 98 high and 67 above the floor, which no party enters (in the original it is part of sector 18).
- `solve`: four waves (0 to 3: 50, 59, 23 and 3 rooms), the original's order (porch doors in wave 1, the vault and the
  button's room last).
  `compare.py`: 18 in, 14 near, 3 out (unchanged).
- Warnings: the nine "face each other across N pairs of walls" are gone (six pinned with `from_wall`/`to_wall`, all
  six as the build had taken them; three vanished when sector 17 lost its arms). Left: 32 "wall without thickness"
  warnings, the round-one false positive (in each, one room's wall is wholly open; following them moves measured walls
  by 16). `open:lounge_window` left that list with the lounge's new end and `open:s28_s62_lounge` joined it.
- Playtest: **passes four runs of four** (`output/studio_cal/mm6_scifi/run/walk_final1.log` ... `walk_final4.log`,
  261 steps, no replans). New in it: every tube light event (19 asserts: the airlock's floor darkens the entry run, each
  run's floor lights its run, each corner darkens the runs on both sides, the last 48 before the exit door darkens the
  exit run); the chests' items checked after the loot (blaster, blaster rifle, both memory crystals, Proclamation and
  Control Cube); the blaster terminal in the pit sets qbit 1300.
- In-game pairs, all sheets looked at: `r5/ingame` (12, mean edge agreement 0.80) and `r5/ingame2` (8, 0.82). The
  vaults line up in every picture (s10 stub 0.83, groin to s17 0.84, s11 stub 0.91, s13 arm 0.91, s7 0.84, s17 north arm
  0.82; the rest of the difference is the pipe texture's phase); the lounge's window end 0.95 and 0.98 from the ramp;
  the pit's flight head 0.97; brightness gains 0.97 to 1.04 in 15 of the 20 pairs.

### Contents

The original places **no monster and leaves no item lying**: `initial_state.actors` and `sprite_objects` of
`sci-fi.scene.yml` are empty, and the export's only entity is the party start. So 0 of 0 placed; `monsters` and
`items` stay empty. What the original does hold, and rounds one to four left out, is its **chest contents**: 14 chest
records with fixed items (28-byte records, `raw_items_hex`; flag 1 = trapped). Now each chest has `random_items: 0`
and the original's `items`: blasters (1666) in chests 1, 2, 4, 7, 10, 13; blaster rifles (1667) in 8, 9, 12; the
Proclamation (2166) and the **Control Cube** (2076) in chest 5 (the one whose event gives award 103); Memory Crystals
Alpha and Delta (2170, 2172) in 6; chests 0, 3 and 11 empty, as in the original. The eleven with items are trapped
(`trap_level: 8`: the game takes only "trapped" from it and the damage from the map row's Trap 8, the reference's
row). No placeholder was left in the project.

### Lights

- **Switching.** The original's events 38 to 52 are step events on the tube's floors and only call `SetLight`. Each is
  now a script event with `lights_on`/`lights_off`, on the rebuild's room that holds the original's trigger face:
  the seven runs' floor strips (38 to 44 light their own run), the airlock's floor at 228 (45), the five corners (46
  to 51; 47 also casts its Sparks) and the 48 before the exit door (52). 49 lights switch; all start lit, as the
  original's (attributes 0). The built handlers name the original's lights in the original's order; the rebuild's
  numbers are those of ids.lock.yml `lights`.
- **The light record.** The original's 392 records are all alike but for position and radius: type 5, brightness 31,
  colour 0, 0, 0, attributes 0, id 0. The rebuild's (`oymap export` of the built map): type 0, brightness 31 (as given:
  every light of the project has `brightness: 31`), colour 255, 255, 255, attributes 0, id 0 (1 to 51 for the switched
  ones). The project can say radius, colour, brightness (1 to 31), `on`, `pulse`; it cannot say the type, and does
  not need to: the game reads the type and never uses it, ignores brightness except that it must be above 0, and turns
  MM6's black lights white when it loads them (`normalizeMergedMm6IndoorStaticLights` in `game/maps/MapAssetLoader.cpp`).
  So the two maps' lights are the same to the renderer; the sector light lists differ (the original lists about 14
  lights per sector, the build each light in its own sector only) and the renderer uses them only to know that a
  light is listed. Pairs agree in brightness now (gains 0.97 to 1.04) except the two window bays (1.3 and 1.9, the
  rebuild darker) and the north-east arm (1.2); not traced further.

### Events against the original (`oymap flow`)

71 map events in the original. **55 do the same thing under the same condition**: the door handlers 2, 4 to 15, 17 to
21, 23 to 26, 28 (23); event 1 on the locked room's door; the 14 chest handlers 29 to 37 and 65 to 69 (now with the
original's contents, and 34 with its award); the 15 light handlers 38 to 52; the exit 70; the spark timer 71.
**9 differ in presentation**: the terminals 53 to 61 show their text as a status line where the original opens a
message window (no word). 61 now also teaches every member without it the Blaster skill, as the original's (MMMerge)
handler does. **7 are not built**, as in the original nothing runs them: 3, 16, 22 and 27 (door handlers bound to no
face or to no door record), 62 to 64 (bound to nothing, on no timer).

Second click sources the rebuild does not have: chests 0, 4 and 7 open also from the office niche's floor (sector 18,
face 946), the closet's shelf (sector 64, faces 1036 to 1038) and the north-east cell's shelf (sector 20, face 957),
and event 1 also answers on a 64-wide face in the east porch's doorway (face 1126). The shelves and the niche are built
now; a chest preset cannot take a platform as its source (refused, below).

Two round-four handlers were wrong and are corrected: chest 5's award was `{add: {var: Awards, value: 103}}`, which the
game reads as award 0 for the current member (`oymap flow` showed "set award 0"); it is now a Lua line
`evt.ForPlayer(Players.All) SetAward(Award(103))`, the original's. Terminal 61's Blaster skill was missing. Both are
Lua lines because no effect word gives an award or works on each member in turn.

### What changed

1. **The vaulted corridor ring at 1184** (round four's gap 1). Sectors 10, 11, 8 and 7 are one room each under
   `ceiling_points` (14, 34, 16 and 4 points; heights at the chamfers' feet and the flat top's edges only): springing at
   1440, a flat top 197 wide at 1539 (sector 8's north chamfer 131 wide), and groins where every side mouth crosses a
   chamfer (the stubs to the hall, the arms of sectors 13 and 17, the corner joints). `ceiling_surfaces` give the
   original's second textures: swwala on the corridors' tops (north and south corridors, both stubs' tops, the
   north-east arm) and swll4dk on the north corridor's south chamfer between its two groins (face 2124); the east
   corridor's top is swll5dk as the original's. Sector 17's two arms and sector 13's two arms are rooms of their own
   under their vaults (the north arm's chamfers twist from 1440 to 1381, two triangles each, faces 315, 317, 2162,
   2163); every mouth between them is `width: full, height: full` and follows the lower roof, so the wall over each
   arm's mouth is the room's (faces 297 to 299, 311 to 313). The east corridor's band went from 304 to 256: a band ends
   at the ceiling's lowest point. Over the east cell's door the west chamfer springs at 1480 (face 890); the original's
   two upright 40-high triangles at its ends are leaning triangles 49 long here.
2. **Light switching** (round four's gap 2), above.
3. **Chest contents and traps**, above.
4. **The pit's second flight ends in a doorway** (round four's gap 7, second half). The pit's upper floor (-196) is a
   room of its own (`s66_pit_upper`) open to the low floor along its three edges (`width: full, height: full`, pinned),
   and the flight runs to the mouth at x -7744 with `to_height: -196`: seven risers, the last in that mouth's wall (face
   914), six treads 99 deep, and the top step is the upper floor (swfloor2b) as in the original. Round four's top
   tread cut out of the platform is gone. The terminal moved with the wall (`along` 0.857 of the upper room's south
   wall, x -7552 to -7424 as face 2888).
5. **The window bays** of sectors 17 and 14 (faces 995 to 998, 1006, 1010 to 1012): sides and top swankdk, sill
   swfloor2b. A doorway takes its sides from its `from` room's `reveal`: the two windows now run from the galleries
   (themes `..._bay` with `reveal: swankdk`) to the hall, with `threshold: swfloor2b`; the galleries' four cell doors
   run from the cells, whose reveal is swll4dk as the original's recess sides (faces 786, 807, 824, 840). `along` became
   1 - along; every portal lands where it did (checked on the built faces).
6. **The lounge's window end** (round three's gap 10): a ledge 14 wide at 719 (faces 764, 767), a sill sloping from it
   to the floor at the window (face 770, a platform with `top_slope`), the room flaring to the window's whole width
   (593, the diagonal wall swankdk), and the ceiling rising from 847 to 888 at the window (`ceiling_points`, swankdk by
   `ceiling_surfaces`). Round two's upright sill 128 high and window 505 wide are gone.
7. **Shelves and a niche** (round one's "bay shelves", left out until now because a level could not touch a wall):
   blocks 99 high against the walls in sectors 20 and 63 (96 by 496, swll4dk sides, swfloor2b tops) and a triangular
   one against sector 64's diagonal wall (swr1dk sides); the office's niche (sector 18: 98 deep, 98 high, 67 above the
   floor, under its terminal) as a room with a mouth. The other "shelves" of round one's list (sectors 14 and 17) were
   the window bays' sills.
8. **Pins**: six openings with `from_wall`/`to_wall`.

### New features: what worked and what did not

Worked first time: `lights_on`/`lights_off` with ids.lock.yml `lights` and the built `evt.SetLight` numbers; step
events on tunnel rooms, on box corners and with `sources`; `ceiling_points` with groins and `ceiling_surfaces` by `at`
(four regions in one roof); `height: full` mouths between two vaults given by points and between a vault and a flat
room; a flight ending in a mouth with `to_height`; `from_wall`/`to_wall`; platforms against walls (a shelf, a triangle
against a diagonal wall, a 14-wide ledge); a wedge (`top_slope` with `rise` above `to`); `threshold`; chest `items`,
`random_items: 0` and `trap_level`; a `lua` effect inside a chest preset and a switch preset.

Not needed here: placed `monsters` and `items` (the original has none), `kills`, `lua` conditions, `secret`, `solid:
false`, `visible: false`, ladders, sounds, `movers[].parts`, sloping slabs with `thickness`, `trim_to_wall`.

Refused:

- **A chest preset with a platform as its source.** The original opens chests 0, 4 and 7 also from the niche's floor
  and two shelves. `oymap validate output/studio_cal/mm6_scifi/repro/chest_from_shelf --assets assets_dev`:
  `wiring.yml: events[1].source: a chest preset cannot have the platform platform:s20_shelf as its source` and, with
  the chest as source and the shelf in `sources`: `wiring.yml: events[2].source: chest:c7 already has an event; one
  object runs one event in v0`. A script preset with `evt.OpenChest(n)` would work with the chest's number copied from
  the build; not done.

### Compromises undone and left

Undone: the vault ring (round four's gap 1); the light switching (gap 2); the second flight's last tread (gap 7, its
second half); the lounge's sloping sill (round three's gap 10); the shelves; the chests' contents (round one's
"not decoded"); chest 5's award and terminal 61's skill (wrong or missing since round three).

Left:
- The first flight's risers and sides take one surface (`riser` is "the steps' upright faces and sides"; `sides` are
  side walls that rake with the flight, not the steps' own ends). Its risers are swrdk2, its sides swll4dk; swll4dk is
  kept, the larger part. Field: a surface for the steps' ends apart from the risers.
- The first flight still ends one step inside the landing (a platform, not a doorway); a flight ends in a doorway
  only at a wall. Field: a flight whose last riser meets the edge of the platform it climbs to.

### Gaps still open, most harmful first

1. **The shafts' rims and bands** (sectors 86 to 89; most of what sector 5 still loses): a 32-wide swhorzdb ring in the
   floor round each hole and swhorzad bands at the top and bottom of each shaft. Field: a rim or band on a floor hole's
   edge and sides.
2. **Leaves that shrink against their jamb**: the east porch's and the airlock's doorways are 512 wide in the original,
   256 here (sector 6 loses 1.0 point, its worst points stand in the doorway).
3. **A tunnel that narrows into another section** (the exit run, x -7748 to -7636): a box room and a rectangular door.
4. **Per-leaf surfaces** (the west porch's leaf 15 swaled/swared, leaf 16 swpnl).
5. **A second click source for a chest** (above), and a message window for the terminals.
6. **A ceiling lower over part of a room**: the plate room's notch (460 under 724, face 1270), the window recesses of
   the cells (1480 over 1579). `ceiling_points` cannot step down.
7. Unchanged: the west lobby's ceiling (sector 25: a flat middle at 512 between two 128-wide strips at 610 with
   chamfered ends; now sayable as three rooms with `ceiling_points` and full mouths, not done: it is worth a few
   hundredths), spawn encounter index, the 25-deep niches between the airlock hall's windows.

### Tool defects (new this round)

- **`assert light: {key}` takes the light's record index in the built map, not its ids.lock.yml number.** The first
  run of the new playtest (`output/studio_cal/mm6_scifi/run/walk_r5a.log`) failed `light 22 is unset` for light:l050,
  whose ids.lock.yml number is 22 and whose record is 49 (`evt.SetLight(22, ...)` resolves to the record whose id is
  22). The shapes gallery's asserts pass by chance: its two switched lights are its first records. The playtest now
  uses the records (`r5/lightkeys.py` prints them); a key that follows ids.lock.yml would not move when lights are
  added before it.
- **`{add: {var: Awards, value: 103}}` validates and builds as award 0.** `oymap flow
  output/studio_cal/mm6_scifi/repro/award_by_add --assets assets_dev --event 11` prints `set award 0`; `oymap validate`
  on it: no issues. A selector that needs an index (Awards, QBits, AutoNotes) should be refused in `var`, or an
  `award` effect added.
- **The "wall without thickness" warning** (round one) is still given for 32 openings where one room's wall is wholly
  open; it moved from `open:lounge_window` to `open:s28_s62_lounge` when the lounge's outline changed, with no change
  at that opening.

### Unsure

- Whether the shelves' and the niche's chest events (29, 33, 36) are meant: they open chests 0, 4 and 7 far away
  (chest 0 is in sector 57, across the map). They look like a leftover of an earlier layout; they are in the shipped game.
- Why the two window bays are darker in the rebuild (gain 1.3 and 1.9): same lights, same ambient; the bays' faces lie
  in the hall's sector here and in the gallery's in the original.

### Score against shape

Nothing in this round was moved away from the original's measured shape. The pit's upper floor became a room of its own
where the original has one sector: the shape is the original's (the floor's edges, the stair to the unit), only the
room count differs, and it is what lets the flight end where the original's does. The bays' and the cell doors'
`from`/`to` were turned round to choose which room's reveal a doorway takes; every portal stands where it stood.

## Round six (2026-11-13, morning)

The sections above are left as written; this one replaces them where they differ. The project as found:
`output/studio_cal/mm6_scifi/r6_backup/`. Scratch: `output/studio_cal/mm6_scifi/r6/` (`compare_start`, `compare_1` ...
`compare_10`; `faces.py` lists a map export's event faces and door records, `frames.py` every door's frame faces,
`region.py` the faces in a box, `worst.py` a compare's worst points, `secdiff.py` the sectors two compares differ in,
`things.py` the picture list `shots.json` (each interactive thing of the original, its faces, both maps' events),
`pairs.py` takes those shots in both maps in one boot each, with the events run by console between them, and lays
them side by side; `snap_before_frames/` the project before the door frames). Pictures:
`output/studio_cal/mm6_scifi/ingame_r6/` (`start/` the round's start, `r1/`, `r2/`, `final/` builds before the
studio's 11:20 merge, `final2/` and `gate_final/` the end, `probe_*` single questions); in every folder `pairs/`
holds original left, rebuild right, and `pixels.json` the edge agreement. Every edit was by hand or by a one-off Python
replacement whose diff was read; no generator was run.

### Scores

| | `oymap compare` | shape (distances) | textures | points lost (of 2,556) |
|---|---|---|---|---|
| Start of round six | 99.2 % | 99.7 % | 98.2 % | 20.1 |
| End of round six | **99.4 %** | **99.7 %** | **98.9 %** | 13.9 |

Mean floor / ceiling difference 0.1 / 0.9 (unchanged). No sector went down. Sectors (start to end): east porch 6
0.951 to 0.989, west passage 9 0.991 to 1.000, east lobby 50 0.978 to 0.995, east store 51 0.992 to 0.999, east
hall 49 0.995 to 0.999, locked room 43 0.985 to 0.999, generator 23 0.989 to 0.996, east bay 56 0.954 to 0.981,
gate corridor 45 0.960 to 0.968, airlock step 58 0.958 to 0.968, the hall's four sectors 1 to 4 0.992-0.995 to 0.997.
`compare.py`: 18 in, 14 near, 3 out (unchanged). Rooms 139 (+ `s9_porch_recess`, `s39_door_recess`,
`s43_door_recess`); `audit --reach`: 138 of 139 with the doors out of the way (the niche, as before), 50 at the start;
`solve`: four steps, 50, 60, 25, 3 sectors, the original's order. In-game pairs (132 of them, every interactive thing
before, during and after use): mean edge agreement 0.754 at the start, 0.817 at the end.

Playtest: **passes four runs of four** (`output/studio_cal/mm6_scifi/run/walk_r6_end1.log` ... `_end4.log`, 267
steps; also four of four on each intermediate build). New: before each loot the party drops every pack item the walk
does not assert, and each loot counts what its own chests give (`item_count` before and after: one blaster from chest
4, one from chest 2, two blasters and a rifle from the repair bay, one rifle from chest 8), so a full pack can never
fail a later chest; terminals 61 and 56 open their message windows (`assert dialog text_contains`), which the walk then
closes. Every walk step already had `clear_hostiles`; no assert counts anything map-wide.

### What changed

1. **Doors fold as the original's** (`fold: true` on all 21, `travel` the record's own move length: 250, 252, 254,
   245 on the porches, 198 in the airlock, 110 at the tube exit, 125 at the west porch, 232 for the gate slab, see 6).
   The doorways are the original's width again: 253 to 255 (were 224 and 240, so that sliding leaves had a pocket),
   `width: full` where the original's leaf fills its wall (east lobby, vault, hatch, east porch and airlock: the
   last two 512 as the original's, round five's gap 2). Pictures: `final2/pairs/02-east-lobby-b-opening.png`,
   `61-east-porch-hall-b-opening.png`, `67-airlock-hall-b-opening.png`, `35-west-porch-passage-b-opening.png`.
2. **Door frames.** The original's sci-fi doors stand in recesses whose sides are swgirder at the east store, the
   H-shaped room, the panel room and the repair bay (`frames.py`; faces 633, 644, 1139, 1140, 1179 to 1183, 1209 to
   1213, 1226 to 1230): themes `..._frame` with `reveal: swgirder` on the rooms the doorways are built from, and the
   two east lobby openings turned round (from the lobby to the hall, from the store to the lobby, kinds swapped
   left/right) so that the lobby's own swaled frames door 4 and the store's swgirder frames door 5. The swgirder
   strips either side of the east store's recess (faces 2560 to 2563) are panels. Every door and every doorway through
   a thick wall has `threshold: swfloor2b` (swfloor5a in the airlock): rounds one to five drew the wall's texture on
   the floor of every doorway. Pictures `05-east-store-b-opening.png` (0.33 better), `25-repair-bay-b-opening.png`.
3. **The west porch door's recess** (sector 1: 514 wide, 21 deep, 256 high, swll4dk either side of the doorway, swr4dk
   overhead; faces 1283, 1341 to 1343, 1675 to 1678) as a room, the door between it and the passage, the passage's
   frame panels (swll5dk, swll4dk; faces 1673 to 1677) and the leaves' own pictures (`pictures`/`back_pictures`:
   swpnl and swaled toward the hall, swared and swpnl toward the passage: round five's gap 4). Leaves now stand where
   the original's do (x -2456 to -2392; 10 off before). `39-west-porch-hall.png`, `34-west-porch-passage-a-shut.png`.
4. **The locked room's door recesses**, both splayed from 255 to 297 under swfloor5a, swall1 on the hall's side and
   swaled on the room's (faces 891 to 895, 1349 to 1352), as two rooms either side of the door; the door's jamb and
   edge take swr4dk (the recess's reveal), as the original's faces 893 and 1173. `75-locked-room-after-button.png`.
5. **Chests where the original's stand.** Every chest's `at` was its front's middle; the build takes it as the box's
   middle, so all 14 stood 9 to 48 off (most 32 forward of the wall). Now the box centres of the original's faces.
   `kind: ch5` on all 14 (the studio's merge of 11:20): left end, middle and right end on both long sides and on the
   top, ch5side on the ends. `101-chest-0-b-above.png`, `120-chest-10-a-front.png` (edge agreement 1.0).
6. **The button** (door record 26) is `kind: button` (the 11:20 merge): a block 32 by 32 standing 16 out, swr4 on its
   face and sides (faces 1750, 1752 to 1754), pushed in when used and out again on the next press, toggling the
   locked room's door. `71-button-a-before.png` to `74-button-d-third.png`. The lead's message gave `off: SWFloor2b`;
   in the original that is the block's top (face 1751, normal up); its face toward the room is swr4 (face 1750).
7. **Gate slab** (door 23): its doorway stands on the original's 16-high sill (`sill: 16`, the floor under the slab at
   409, face 748) and reaches the corridor's ceiling; the slab folds up 232 to 641 as the original's rises 200 from
   441. The corridor south of it is under swceilf (faces 571, 2732; it was swll5dk) and its jambs swankdk.
   `gate_final/pairs/04-gate-slab-north.png`.
8. **Other surfaces the player sees beside the doors**: the east porch as the original's room (576 wide with 32-deep
   swhz3dk returns at both ends, swtrdk sides, a swrdk2 grate floor with a swll5dk panel; faces 124, 125, 129, 130,
   1124, 1125, 2552, 2553, 2739 to 2742), the east hall's two swrdk2 floor strips (faces 2735 to 2738, 2743, 2744; both
   floors by `floor_points` at one height, `floor_lines` and `floor_surfaces`: the only way to give a level floor parts
   of another texture), the airlock step's ceiling (492 with a swgirder frame and a swankdk coffer to 556, faces 1071,
   1980 to 1998, 2009; it was flat swankdk at 524: 32 off in both directions) and its swfloor6a step over the mouth
   (face 1298), the hatch closet's walls (swall4 south, a swgirder strip beside the hatch, swll4dk to 265; faces 637,
   1659, 628), the east bay's south wall swtrpnl (face 1051) and its bands to the ceiling's edge (264).
9. **The generator room's balcony** (sector 23) is a platform with `base` (outline the original's faces 2536 to 2540:
   top swrdk2 at 580, sides swildk, underside swankdk at 452). Round one's beam stood 31 past the cut-corner walls into
   both balcony rooms, whose floors flickered over it (8 of the 9 `geometry.coplanar` findings), and its top was
   swildk. Sector 23 0.989 to 0.996.
10. **Events**: the terminals 53 to 61 open their text in a message window (`{message: ...}`, new in the studio), as
    the original's `evt.SetMessage` with press-any-key does, with the original's quotes; chest 5's award is
    `{award: 103}` (every member) instead of round five's Lua line; the closet's triangular shelf and the north-east
    cell's shelf open chests 4 and 7 as the original's events 33 and 36 do on faces 1036 to 1038 and 957 (script
    events with `open_chest`, the shelves with ids; round five's refusal concerned the chest preset only).

### Events against the original (`oymap flow` of both)

71 handlers in the original. **64 do the same thing under the same condition**: the 23 door handlers, event 1, the 14
chest handlers (34 with its award, now by word), the 15 light handlers, the exit, the spark timer and, new this round,
the nine terminals (message window, trekscon, 61's qbit and Blaster skill). **7 are not built**, as nothing runs them
in the original: 3, 16, 22, 27 (door handlers bound to no face or to no door record; 22 is bound to the gate slab's
underside, face 753, but names door 22, which does not exist), 62 to 64 (bound to nothing, on no timer). Second click
places the rebuild still lacks: chest 0 from the office niche's floor (face 946: a room's floor cannot be a click
source), event 1 on the east porch leaf's edge (face 1126), and chest 3 from the 16-wide end of chest 1's lid (face
2790 carries event 32 in the original; a data slip of the shipped map, left out on purpose). No placeholder is left.

### What the player sees: differences per interactive thing

Pictures are `output/studio_cal/mm6_scifi/ingame_r6/final2/pairs/NN-<name>.png` unless named otherwise.

| Thing | Original | Rebuild now | State |
|---|---|---|---|
| 18 single doors (records 1, 4 to 9, 12 to 14, 17 to 21, 25) | leaves fold to the jamb, picture riding with the edge | the same (`fold`, `travel`) | fixed |
| Door frames (records 5, 12, 20, 21) | swgirder recess sides | swgirder reveal | fixed |
| Door frames elsewhere (records 1, 4, 6 to 9, 14, 18, 19, 25) | swll4dk, swaled, swall1, swall3 recess sides | the from room's wall or reveal, the same textures | as the original |
| Plate store's frame on the store side (record 25) | splayed swhorzdb sides (faces 1247, 1248) | swll4dk | studio: one reveal per doorway, from one room |
| Door edges (the leaf's free edge) | swr4dk (swr3 on records 5 and 14: faces 1141, 1160) | the from room's reveal, drawn as one flat colour | studio, below |
| Doorway floors | swfloor2b | swfloor2b (`threshold`) | fixed |
| East and west porch, airlock double doors | 512 / 256 wide, leaves part from the middle and fold | the same | fixed |
| West porch leaves | swaled and swpnl toward the hall, swared and swpnl toward the passage | the same (`pictures`) | fixed |
| East porch leaves' picture phase | swor2 laid in world phase (u 128 to 640: seams at y -256, -512) | one picture per 256 from the doorway's side | studio: no picture offset on a door |
| Tube exit (records 10, 11) | an octagonal frame round the doors (swrt2, swall5, swr4dk; faces 1445 to 1526) | a rectangular doorway | studio (round four's gap 4) |
| Gate slab (record 23) | slab 441 to 657 over a 32 slit and a 16 sill; underside swceilf (face 753) | slab 409 to 649 on the sill, opening to 641; underside swankdk | slit: studio (a leaf fills its doorway); underside: the door-edge gap |
| Hatch (13), plug (17) | sink into the sill | the same; closet walls fixed | fixed |
| Button (record 26) | 3D block, swr4 face and sides, swfloor2b top, pushed in 13 and out again | `kind: button`, swr4 all round, pushed to 1 short of the wall | studio: the top's own surface; the 13 travel |
| Pressure plate (record 24) | swrdk2 plate 1 high and a swrdk2 grate beside it at floor level (face 1741) | the plate; the grate is refused | studio, below |
| 9 terminals | trekscrn turns trekscon, text in a message window | the same | fixed (message windows) |
| 14 chests | ch5 end-middle-end, at the original's places | the same (`kind: ch5`, positions) | fixed |
| Chest tops | ch5top/LE/RE on chests facing x, ch5topb/Lb/Rb on chests facing y | ch5topb/Lb/Rb on all, laid along each box | studio (looks the same in the pictures: the kind lays the lid along the box) |
| Shelves opening chests 4, 7 | click | click (events 64, 65) | fixed |
| Niche floor opening chest 0 | click (face 946) | nothing | studio: a room's floor as a click source |
| Exit | swdoorb | the same | as the original |
| Tube light floors | lights switch | the same | as the original |

Things over moving parts: none in this map (no lift, no mover, nothing stands on a door). Levers: none (the only switch
that moves is the button, done). Toggling pictures: no plate here changes its picture (the button moves instead).

### `geometry.coplanar` findings of the build (the 11:20 studio)

Nine at the start of the round's last part, one left:

- Fixed (8): the generator room's balcony beam against the floors of the two balcony rooms at 580 (faces 779 to 783 of
  the build against 821, 976, 977: overlaps of 56 to 15,417 square units at the two cut corners), by item 9.
- Left (1): face 768 (swildk, the balcony's east side, room:s23_generator) and face 1886 (swankdk, room:s9_west_passage)
  at x -6320, y -678 to -85, z 452 to 463 (6,523 square units): the generator's east wall and the west passage's
  ceiling step meet in one plane across the zero-thickness mouth `open:s23_s9_west_passage`, and the balcony's
  side, which stands in the wall's plane against the east wall, runs over that step. Not fixed: it needs the balcony
  to stop short of the mouth, or the mouth's top to end under the balcony, and neither was checked in the game.

### Studio gaps found this round (for a code agent), most visible first

1. **A door leaf's free edge has no surface of its own and no texture coordinates.** Every folding leaf's edge face
   takes its from room's reveal and all its texture coordinates are 0 (`oymap export` of the build: e.g. the west
   porch leaves' edge, u 0..0, v 0..0), so it shows as one flat colour (`final2/pairs/35-west-porch-passage-b-
   opening.png`, the orange strips). The original's edges: swr4dk on every door but two (faces 1126, 1129 east porch,
   1385 storage 2, 1362 storage 1, 1543 junction, 1511/1507 tube exit, 1679/1680 west porch, 893/1173 locked room,
   1715 wedge, 1730 meeting hall, 1181 panel room, 1211 H room, 1228 repair bay, 1246 plate store, 2646/2647 airlock
   `swhor4DK`), swr3 on the east store (1141) and the vault (1160), swceilf under the gate slab (753). Wanted:
   `edge_surface` on a door, laid at its texel size.
2. **One reveal per doorway, from one room.** A doorway's sides, top, threshold default and the leaf's edge all come
   from the `from` room's theme; this round needed four new themes and two openings turned round to give four doors
   their frames, and still cannot give the plate store's swll4dk-then-swhorzdb or the east porch's swankdk (hall side,
   faces 127, 128) and swhz3dk (porch side, 1124, 1125) halves. Wanted: `reveal` on an opening, or per side.
3. **Non-rectangular door frames**: the tube exit's octagon (above), the C-shaped store's funnel doorway from the
   entrance corridor (384 wide at the store, 256 at the corridor, 128 deep: faces 905, 906, 1090), the plate store's
   splayed store side. Said here by recess rooms where the doorway itself is rectangular (west porch, locked room).
4. **A floor panel beside a plate**: `objects.yml: plates[1]: the plate cannot be cut into the floor of
   room:s55_plate_room: keep it clear of that room's walls, pillars, levels, holes and other plates` for a level grate
   (rise 0, swrdk2) touching the pressure plate (the original's face 1741 beside 1742). Repro: copy the project, add
   `{id: plate:grate_south, room: room:s55_plate_room, at: [-9168, -2826], size: [128, 128], rise: 0, surface:
   swrdk2}`. And a level floor or ceiling takes texture regions only through `floor_points`/`ceiling_points`: the
   east bay's ceiling border strips (swvert3dk, faces 2025, 2026, against swrt3dk) and the meeting hall's east strip
   (swankdk, face 2061) are not said.
5. **A shut door with a gap under it**: the gate slab's 32-high slit over its sill (a leaf fills its doorway).
6. **A button's top surface** (swfloor2b, face 1751) and its travel (the original's 13, pushed to 3 short of the wall;
   the build pushes to 1 short).
7. **Picture phase on doors and walls**: door pictures start at the doorway's side, the original's run in world phase
   (east porch); wall textures run from the wall's start (the plug passage's swall2 X pattern shows its medallion where
   the original shows struts, `41-plug-passage-b-opening.png`).
8. Unchanged: a room's floor as a click source (the niche, chest 0), spawn encounter index, the shafts' rims, a
   ceiling lower over part of a room, flights' end faces.

### Tool defects (new this round)

- The edge faces of folding leaves have zero texture coordinates (above, gap 1): an export shows `texture_us [0, 0,
  0, 0]`.
- `ingame_compare.py` cannot run console lines between shots, so it cannot picture a thing before and after use;
  `r6/pairs.py` does it with the tour's per-shot `commands` and `settle_seconds` (the studio's `things_shots.py`,
  merged at 11:20, was not used).
- Pictures 20 to 22 (`tube-exit-junction-*`, camera at (-7136, -2951, 393) facing west) show a black slot at the left
  edge in the rebuild where the original shows a copper-pipe pilaster; three other poses round the same corner
  (`ingame_r6/probe_slot/`, `probe_junction/`) show nothing wrong. Not traced (a drone in front of the camera, or a face
  drawn black from that one angle).
- `oymap build --out` still writes `ids.lock.yml` into the project (expected: it did here, for the two shelf events).

### Where score and shape pulled apart

Nothing was moved away from the original's measured shape. The gate slab's doorway now stands on the sill and reaches
the ceiling (the original's slab hangs 32 over the sill): a shape the measure does not see either way, chosen because
the open slab then rises to the original's 641 and the passage floor is the original's 409. The airlock step's ceiling
went from 524 (32 above the original's frame, 32 under its coffer) to the original's two heights: no score change.
