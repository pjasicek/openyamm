# The Lincoln (mm7 `7d23.blv`) rebuilt as a Map Studio project: notes

Project: this folder (`cal7d23`, map_stats id 9712, `reference: 7d23.blv`). Scratch data, pictures, logs and the
generator that writes the four project files (`gen/base.py`, `gen/rooms_def.py`, `gen/build.py`: the project files are
its output, formatted by `oymap fmt`; edit either) are in `output/studio_cal/mm7_7d23/`. Procedure:
`devdocs/map_studio/REBUILD_PROCEDURE.md`. Date: 2026-11-12.

## Where it stands

52 rooms, 57 openings, 28 doors, 6 lifts, 4 chests, 32 spawn points, 264 lights, 6 switches, 1 exit, 43 events,
39 placeholders. It validates without issues and builds (1,571 faces against the original's 3,985).

| Round | What changed | `oymap compare` score | distances | textures | reached, doors clear (`audit --reach`) |
|---|---|---|---|---|---|
| 1 | shell: hall gallery as rooms over solid, stairs as boxed stair rooms (79 sectors) | 76.0 % | 78.2 % | 75.5 % | 69 of 78 |
| 2 | doors, lifts, objects, wiring | 77.7 % | 79.3 % | 75.6 % | 69 of 78 |
| 3 | hall redrawn: gallery, bridge and landings as platforms, open flights | 82.5 % | 85.8 % | 76.8 % | 33 of 52 (the tools do not cross the 33-unit slit) |
| 4 | a beam as threshold at each of the six gallery doorways | 82.5 % | 85.8 % | 76.8 % | 43 of 52 |
| 5 | surfaces (door leaves, gallery fascia, stair sides, corridor bands, ceiling edges), viewport slope, bridge parapets | 85.7 % | 86.5 % | 86.1 % | 43 of 52 |
| last | lights dimmed, notes | **85.7 %** | **86.5 %** | **86.1 %** | **43 of 52** |

- `compare`: 1,113 points, 8 without a floor in the rebuild (four on the pod bays' decks, four on the cargo pit's
  rim), 40 of the rebuild's 1,207 without one in the original. Mean floor difference 6, mean ceiling difference 61.
- `calibration/compare.py`: first shell "16 in, 6 near, 13 out"; last **"24 in, 8 near, 3 out"** (out: smallest
  sector area, lowest doorway, sectors reached at the start: 6 against 2, because the hangar's bays and the cargo
  shaft are rooms of their own).
- Rooms reached: 43 of 52 with every door out of the way. The other nine (reactor room and gallery, reactor side
  lift, the six rooms of the top deck) are reached only by lift, which `audit --reach` and `solve` do not ride; the
  original reads the same way (26 of 35, the same areas missing). `solve` opens the rebuild in five steps as it does
  the original, but see the defect on power below: the order is not evidence.
- **Playtest: passes** (`playtest.yml`, 96 steps, `output/studio_cal/mm7_7d23/play_final.log`). It checks that the
  control room stays shut and the hatch asks for wetsuits without power; opens the corridor door; rides the reactor
  lift; uses the power panel; rides the reactor side lift to the reactor gallery and back; rides the cargo lift;
  loots a chest; walks the west corridor into the hall, the stairs under the hall floor down and up, the west lift
  to the gallery, the hall's stairs down and up, the gallery, the west ramp, the bridge, the viewport; takes the
  Overthruster from the console; enters the captain's cabin; returns by the east ramp; rides the upper east lift to
  the top deck and opens the junction door from the control room's panel. Not played: the lower east lift, the
  transporter pads, the stasis rooms, the exit itself (the party has no wetsuits).
- In-game pictures (`ingame_compare.py`, 11 pairs, `output/studio_cal/mm7_7d23/ingame/`, taken before the lights
  were dimmed): edge agreement 0.37, blurred difference 0.126. The hall, hangar and gallery read as the original;
  the bridge, viewport and stairwell do not.

## How the original's levels connect, and what could be said

| Connection in the original | In the rebuild |
|---|---|
| Hangar (224) to west cargo bay (1036): cargo lift, door 9, in a pit of sector 2 | Said: the pit is a room (`cargo_shaft`) with a lift, open to the hangar at the bottom and to two bay rooms at the top |
| Lower corridor (224) to hall (1036): two flights (224 to 492 to 764), a lobby under the hall floor, a flight that comes up through a hole in the hall floor | Flights and lobby said as rooms under the hall. The hole cannot be said: three stair rooms in a notch between three hall rooms, walled to the ceiling on both sides |
| Lower corridor (224) to reactor room (1036): lift, door 17, a tube through the reactor room's floor | Shaft room in a notch of the reactor room, open to the corridor at the bottom (west) and to the reactor room at the top (north only) |
| Reactor room (1036) to reactor gallery (1484), sector 32 lying on sector 33: lift door 18; a round hole with a spiral stair round the column | The lift, as a room twice as long as the original's, its two doorways side by side. Hole and spiral stair not said |
| Hall floor (1036) to hall gallery (1484): two open stairs with a landing | Said: flights and landing platforms inside the hall room |
| Hall floor to gallery by the west lift, door 37 (doorways one above the other in one wall) | Lift room; its two doorways side by side, 224 apart |
| East corridor (1036) to east landing (1484) to top deck (1868): two lift platforms in one sector, doors 50 and 47 | Two lift rooms and two landing rooms; the lower lift lets out south into the upper lift's cell instead of west |
| Gallery (1484) to bridge (1548): two ramps | Said (ramp rooms) |
| Bridge (1548) to viewport (1292): a middle stair between parapets, slopes behind them | A ramp room the full width behind two parapets with the gap in the middle |

## Gaps in the vocabulary, most harmful first

1. **Two openings one above the other in one wall are refused** ("two openings in one wall ... overlap or stand
   closer than 16 units"), though their heights do not overlap. Where: the west lift (sector 8: sectors 15 and 14,
   doorways at 1036 and 1484 in the hall's west wall at y -5024..-4832), the reactor side lift (sector 42: 1036 and
   1484 at y -1280..-896), the east lift, and every under-gallery door once the gallery is a room. Did instead:
   doorways side by side (west lift 224 apart; reactor side lift made 512 long instead of 256). Field: none; the
   check should compare the openings' height ranges as well as their spans.
2. **A platform or level may not touch a wall** (a platform must stand 33 clear; `levels` "clear of its walls"), so
   a balcony along a wall cannot be said. Where: the hall's ring gallery (256 wide at 1484 along every wall of the
   hall, x 2432..6272, y -8160..-2272, with the seven gallery doors in those walls), the bridge across the hall,
   the hangar's west walkway at 736, the rim of the cargo pit. Did instead: hanging platforms 33 short of the walls
   plus six `beams` (32 wide, top at 1484) as thresholds at the gallery doorways; without them the game crosses the
   slit when the party runs straight, but `probe`, `audit --reach`, `solve` and the playtest's route planner do not.
   The walkway and the rim are left out. Field: platforms allowed against walls (or `gallery: {along: wall, width,
   floor}`), and `levels` that reach a wall.
3. **An opening cannot lead into the side of a pit, and a hole in a floor onto the room below cannot be said.**
   Where: the stair through the hall floor (256 x 576 at x 4816..5072, y -4416..-3840, 764 up to 1036, joined at its
   foot to the lobby under the floor), the reactor lift tube (256 square at 4416..4672, -2048..-1792, through the
   reactor room's floor at 1036), the round hole (octagon 3995..4709, -1509..-795) between the reactor room and its
   gallery and on up into sector 34, the cargo pit. Did instead: the hole's footprint is cut out of the upper room
   as a notch and filled by a room of its own; for the hall that needed three hall rooms instead of one. Field: on
   a `levels` entry, `opens_to: room:x` for a sunken floor that a lower room joins, or an opening with `in:` a level.
4. **An opening may not stand in a wall the floor rises along**, and a flight can only join floors of one room.
   Where: the stair through the hall floor: its side walls should stop at the hall floor (1036) and be open above.
   Did instead: side walls to the ceiling, a box 256 x 576 standing in the hall (third worst place of `compare`).
   Field: openings in raking walls whose sill is the higher room's floor; or a flight whose `to` is a doorway.
5. **An opening cannot say which stretch of wall it means.** The build takes the pair of facing walls with the
   longest shared stretch (`core/IndoorLowering.cpp` line 1235), `along` only moves the hole inside that stretch,
   and "facing" passes through other rooms up to 512 away. Where: every room in a notch shares three stretches with
   the room round it (reactor shaft: only its north side could be opened); a stair room 256 wide and longer than
   256 would have been opened in its side wall, so the hall-floor stair is three rooms of 192; two rooms meeting
   along an L can only be opened on the longer leg. Field: `wall:` (edge number or compass side) on an opening for
   each of its two rooms.
6. **Doors that slide sideways, and doors of two leaves.** 46 of the 72 door records are doorway leaves that
   slide sideways, most of them in pairs that slide apart; doors 19/20 are a pair sliding up and down. Did instead:
   one `slide_up` leaf each. Field: `kind: slide_left | slide_right | split`.
7. **Walk-on triggers.** The original has 42 pressure plates: the two transporter pads between the cargo bays
   (events 457 and 458), floors that close doors behind the party (events 16, 18, 28, 50, 55, 56, 91, 92, 459 to
   472), lift calls. Did instead: a wall switch for each pad; the closing events are not said. Field: `triggers`
   (a floor region in a room) as an event source.
8. **Monsters placed in the map, item spawn points, items on the floor**: 17 actors (monsters 3000, 5600, 9000),
   20 spawn points of type 2, 5 sprite objects. Placeholders.
9. **Moving things that are neither a door in an opening nor a lift.** The pod bays' double lifts (doors 1 to 8:
   two decks 576 apart moving together, the lower one rising from under the floor with chest 1 on it); the stasis
   rooms' sliding partitions (doors 52, 54, 56, 58, travel 383 sideways); the two cranes (doors 14 and 44, travel
   1,408 along a rail under the ceiling); the retracting rim of the cargo pit (door 38); the three shutters of the
   engineering station (doors 77 to 79). Not built; chest 1 stands in bay 2. Field: `movers` (a block or wall with
   a direction, travel and speed), and a lift with a second deck.
10. **Ceilings and walls that slope.** The hangar's barrel vault (704 at the walls, 960 in the middle), the hall's
    vault (1791 to 2252), the bridge's and viewport's raking ceilings (the viewport's window falls from 1977 to
    1665), the six-sided section of the three service corridors (sectors 11, 19, 41: floor and ceiling skirts 96
    high). Did instead: flat ceilings with raised strips (which must stand apart from each other, so a vault has
    gaps in it) and three wall bands. Field: `ceiling: {vault: barrel, axis, spring, crown}`; `section:` for
    corridors.
11. **A switch, console or button that is not on a room's wall.** The power panel (a console beside the reactor
    pit), the star console on the bridge (event 376), the lifts' buttons, the three door panels of the top deck's
    control room. Did instead: wall switches. Field: `switches` with `on: platform` or `at:` and `facing:`.
12. **Pits and furniture that touch a wall.** The lower hold's two loading pits (floor 96, ramps, against the east
    wall), the viewport's three pilot pits, the hall's four raking buttresses at its south end (1036 to 1420).
    Not built.
13. **Scripted things with no preset**: the timers (events 476 and 477, Sparks every two and one minutes once map
    var 5 is set), `SetLight` (light groups 1 and 2 switched by events 1, 376, 475), the exit's test that every
    party member carries a wetsuit (said as: the party carries one), the teleport preset with a switch as source.
14. **Stair spiral.** The steps round the reactor column from 908 through the hole up to sector 34. Not built.

## The five worst remaining differences

1. **Viewport** (sector 38, 60 points, 71 %): no pilot pits, a full-width ramp instead of slopes behind parapets
   with a middle stair, a flat ceiling where the window rakes. Gaps 10 and 12.
2. **The stair through the hall floor** (point 4864, -4096: 39 %): a box to the ceiling in the middle of the hall.
   Gaps 3 and 4.
3. **The hall** (sectors 3 and 4, 387 points, 84 to 85 %): vault as three strips, the gallery's 33-unit slit, the
   bridge platform ending 33 short of the east gallery where the hall rooms meet, no south buttresses. Gaps 2, 10.
4. **Hangar** (141 points, 86 %; textures 79 %): pod bays as plain rooms (four points without a floor), no west
   walkway, wall panels alternate a2d and a1b in the original, vault. Gaps 2, 9, 10.
5. **Lift shafts and ramps** (sector 42: 50 %; sectors 35, 36: 60 %; sector 8): shafts enlarged or opened on other
   sides, doorways side by side, door leaves of the wrong kind. Gaps 1, 5, 6.

## Tool defects

- `oymap export assets_dev/worlds/mm7/maps/7d23.blv --pretty`: `counts.doors` is 72 but there is no door list (the
  procedure says the export has every door). Read from `7d23.scene.yml` (`initial_state.doors`).
- The same export gives all 267 lights `radius: 0` and `color: [31, 0, 0]` or `[31, 0, 128]`: the light record
  looks misread. I could not tell the lights' real radius or colour (the rebuild's are white, radius 96).
- `oymap solve 7d23.blv --world mm7 --assets assets_dev` and `oymap audit ... --reach`: lifts are not ridden, so
  sectors 22, 27 to 30, 32, 33, 42 are "never reached" in the shipped map; and the solve opens every door that
  tests map var 4 although event 475, which sets it, is bound to faces of sector 33, which it never reaches. The
  order it prints is therefore not the order the map opens up in.
- `oymap flow 7d23.blv --world mm7 --assets assets_dev --event 501`: "attempt to perform arithmetic on a nil value
  (local 'count')"; the sandbox has no party for `GetPartyMemberCount()`.
- `oymap validate`: "the block does not stand inside room:x with its whole footprint" for a platform that is
  inside but nearer than 33 to a wall; the message should give the distance. Shown by any platform whose outline
  touches its room's wall.
- `oymap validate`: "two openings in one wall of room:x overlap or stand closer than 16 units" names neither
  opening, and counts openings whose heights do not overlap (gap 1).
- `oymap probe <L4> --assets assets_dev --from 2576,-7215,1484 --to 2200,-7215,1484 --doors-open` (without the
  threshold beams): "blocked by a face", the wall under the doorway, across a 33-unit slit that the game walks
  (`walk_to` with `plan: false` crosses it both ways). Reach, solve and the route planner agree with the probe,
  not with the game.
- `oymap probe <L4> ... --from 4352,-10300,1420 --to 4352,-10800,1292` when the ramp room ended 32 above the next
  room's floor: "blocked by a face", the ramp's own floor; a 32-unit step down out of a ramp is refused.
- `wiring.yml`: `preset: teleport` with `source: switch:x` is refused ("a teleport preset cannot have the switch
  ... as its source"); the schema says a source is "a door, switch, chest or exit". Used a switch preset with a
  `lua` effect.
- `objects.yml`: `wall: north` on the hangar (its north wall is the 1,024-long edge 4) and on `cargo_e` gives
  "the object does not fit on that wall"; the edge number works. The compass side seems to pick another edge.
- `ceiling_levels` side by side are refused ("cannot be cut out ... clear of ... the room's other regions"), so a
  stepped vault cannot be drawn without gaps; a region round a pillar is refused the same way.
- `oymap build <L4>` without `--out` writes `build/` into the project folder (removed here);
  `calibration/ingame_compare.py` installs into the shared `output/studio_slice_root` unless `--root` is given,
  which agents working side by side would overwrite.
- A raised lift carries the party 8 above the floor it reaches (party z 1044, 1492, 1876 on lifts raised to 1036,
  1484, 1868).
- `play_lua`'s `mapvar("power")` does not know the project's variable names.
- The game's `walk_to` stops on a spawned monster ("nearest actor 19 at 165") with an immortal party; it needs
  `clear_hostiles` on every walk (playbook says so, the two example playtests do not need it).

## Unsure of in the original

- The lights (above). Whether events `SetLight(1, ..)` and `SetLight(2, ..)` switch groups of them.
- Faces call events 58, 80, 82, 85, 87 to 92 that have no handler, and the script moves doors 12, 13 and 80, which
  the map does not have. Handlers 180 to 195 open chests 5 to 19 and 0 but are bound to no face: only four chests
  can be clicked.
- What door 38 (the rim round the cargo pit, travel 96 down) is for, and the states event 151 keeps in map var 2.
- The east lift: which of events 155, 156, 473, 474, 34, 154 a player uses in which order; the rebuild gives each
  platform one toggle.
- The partition and small doors 19/20 in the engineering station (sector 9), left out.
- The window between the top deck's corridor and its control room (a portal 384 wide, 96 high, at 1964): it could
  have been said as an opening with a sill; not done.
- Whether sector 32 (the reactor gallery) is reached by the spiral steps as well as by lift 18.

## Round two (2026-11-12, the vocabulary added after round one)

Everything above is round one and stands as written then; where this section says otherwise, this section is current.
The project files were edited by hand in this round: the generator in `output/studio_cal/mm7_7d23/gen/` no longer
matches them and must not be run over them. Scratch data of this round: `output/studio_cal/mm7_7d23/` (`r2.sh` the
loop, `compare_r2/`, `ingame_r2/`, `play_r2.log`, `repro/`).

### Scores

| | `oymap compare` | distances | textures | points without a floor | mean ceiling difference |
|---|---|---|---|---|---|
| Start of round two (round one's project, today's `compare`: 1,060 points) | 86.3 % | 86.5 % | 87.0 % | 4 | 57 |
| Hall as one room: stairwell, gallery against the walls, vault as one leaning ceiling level | 88.7 % | 89.6 % | 87.6 % | 4 | 38 |
| Lift doorways one above another (west, reactor side, lower east) | 89.0 % | 89.8 % | 88.1 % | 4 | 37 |
| Sloping ceilings over stairs and ramps, hipped bridge ceiling, viewport window and pits, hangar vault | 90.6 % | 91.3 % | 89.8 % | 4 | 31 |
| Cargo bay as one room round its pit, shafts open on three sides, reactor hole, hold trenches and vault, door leaves a2c | 91.3 % | 92.1 % | 89.5 % | 0 | 27 |
| Hall stairs as the original's solid blocks (parapets 124 high, landing rails, piers under the gallery) | 92.5 % | 93.3 % | 90.7 % | 0 | 27 |
| Viewport canopy bands, hangar control room and top deck windows, reactor rings, pit steps | **93.1 %** | **93.6 %** | **92.1 %** | **0** | **26** |

- 47 rooms (were 52), 57 openings, 1,729 faces. `calibration/compare.py`: "25 in, 6 near, 4 out" (was 24, 8, 3).
- `audit --reach`: 6 of 47 rooms with the doors as they start, 47 with every door out of the way; nothing unreached.
- `solve`: seven waves against the original's five, and the same order of areas. The differences are how the two
  maps are cut into sectors, not the order a player meets things in: the original's sector 2 holds the cargo pit
  and the bay above it (so the bay and what its door and pad lead to come one wave earlier there); its sector 21
  holds both east lifts and the top landing (so the top corridor comes one wave earlier); and its event 40 is also
  bound to two faces of the lower hold's doorway, which opens the control room's door from there. The rebuild's
  door leaves belong to the room on their `from` side, so `solve` lists that room one wave early (engineering, crew
  room, east corridor, west lift: wave 1 instead of 2); `bridge_w` moved between waves 1 and 2 from one build to the
  next without its wiring changing.
- **Playtest: passes**, 115 steps (`play_r2.log`). New in it: the hall stairwell down and up, the cargo lift out of
  the pit into the one-room bay, the reactor side lift and the lower east lift through doorways one above another,
  the middle pilot pit in and out, under the viewport window. Fixed where the map moved: the side lift's place, the
  west lift's doorway, the route round the reactor ring.
- In-game pairs: `ingame_compare.py ... shots_r2.yml ... --root output/studio_cal/mm7_7d23/root`, 12 pairs at the
  changed places, edge agreement 0.78, blurred difference 0.031 (`ingame_r2/diff/`). Looked at: the stairwell reads
  as the original's from the hall floor and from the lobby; the window's raking glass matches; the bridge seen
  from the viewport shows a wall hanging between the two rooms where the original is open, and no dome; the cargo
  pit lacks its rim; the vault's ribs are curved in the original and straight here.

### What changed

- **Hall**: `room:hall` replaces `hall_n`, `hall_s`, `hall_me` and the three `trench` rooms. The stairs from the lobby
  are `room:hall_well` under an `in: floor` opening with neither `at` nor `outline`. The gallery and the bridge are
  three platforms flush with the walls (the six threshold beams are gone). The vault is one whole-ceiling level
  with `top_outline` (1740 at the walls, 2252 over x 3584..5120). The two stairs are flights with sides 124 high
  and 48 thick, landings 320 long with rail blocks, and a pier under the gallery beside each.
- **Lifts**: the west lift is 256 x 448 with both doorways at `along` 0.5 (the upper with `sill: 448`); the reactor
  side lift is the original's 256 square with both doorways in its west wall; the lower east lift lets out west
  onto the landing above the corridor's doorway. The two lower doors slide down (see defects).
- **Ceilings**: `ceiling_slope` over both corridor flights (480 to 748, 748 to 1020) and both bridge ramps; the
  bridge is a hipped whole-ceiling level (1804 to 2048); the hangar's vault a ceiling level with `top_outline`
  inside the room (the room is not convex); the lower hold and the cargo pit likewise.
- **Viewport**: cut at y -11200 into `viewport` (flat) and `window` (ceiling 1932 falling to 1420 at the glass, the
  original's plane exactly); three pilot pits as sunken levels with a flight each; wall bands for the canopy.
- **Cargo bay**: one C-shaped room round the pit (was three rooms), the pit open to it on three sides with
  `from_wall`/`to_wall`; the pit ends at y -1792 and the hangar's mouth is a doorway 128 thick, as in the original.
- **Reactor**: the lift shaft opens west, north and east; an octagonal hole joins the two decks; the pit under it
  is a sunken level (908) with the column as a block; two half rings of parapet stand for the console ring on each
  deck.
- Lower hold: three trenches (floor 96) with steps out, two tapering machine blocks. Windows: the hangar control
  room's slit and the top deck control room's. The two transporter events are `preset: teleport` with a switch.

### New features: what worked as described

- `in: floor` with neither `at` nor `outline` (stairwell): built first time; the game walks it both ways, `probe`,
  `audit --reach` and `solve` cross it. With `outline` (the reactor's octagon): built; the two decks see each other.
- Two openings one above another in one wall: three lift shafts, built first time, ridden in the playtest.
- `ceiling_slope`: four rooms, as described, including `height: full` openings at the low and high ends.
- `ceiling_levels` with `top_outline`, with and without `outline`; points on the outline and repeated points work.
- `from_wall` / `to_wall` with compass sides and edge numbers: three openings between one pair of rooms, twice.
- Platforms against walls, with doorways of other rooms opening onto them.
- `preset: teleport` with a switch as source. `export --world --assets` door records. `solve` and `audit --reach`
  riding lifts (the original now solves with nothing unreached).
- Not used: raking beams (`bottom_end`), `top_scale`, `script` preset with a switch: nothing here asked for them.

### New features: defects (repros in `output/studio_cal/mm7_7d23/repro/`)

1. **A lift cannot rise through a hole in a floor.** `repro/lift_through_floor_hole`: `oymap validate` says
   "objects.yml: lifts[0].travel: the lift would raise the party into the ceiling of room:shaft (leave 200 units
   above its top)" and then "wiring.yml: events[0].toggles[0]: there is no door lift:shaft in objects.yml". So a
   shaft or pit under a deck (the cargo pit, the reactor lift tube: both exactly this in the original) is still a
   room in a notch of the upper room. The second message is misleading: the lift exists.
2. **A door that slides up under another opening stands in the upper doorway when open**, and nothing warns.
   `repro/stacked_door_slide_up` validates with no issues; with 192 of wall between the two doorways a leaf 256
   high rises 64 into the upper one (the game's party stuck at 2291, -4928, 1484 on the way out of the west lift).
   Did instead: `slide_down` for the lower door. A check should compare the leaf's travel with the wall above.
3. **A floor hole exactly 16 from a wall is refused** though the message asks for "at least 16":
   `repro/hole_16_from_wall`: "the hole must lie inside room:deck with every corner at least 16 units from its
   walls ...". A pit flush with a wall of the upper room (the cargo pit's west side) cannot be a floor hole at all.
4. **A hole cannot go round a pillar of the lower room** (documented): "the hole of open:reactor_hole cannot be cut
   out of the ceiling of room:reactor_low: keep it clear of that room's walls, pillars, ceiling levels and other
   holes". The reactor column inside the round hole became a platform that stops at the lower ceiling.
5. **An opening cannot reach into a whole-ceiling level** (`height: full` stops at the room's `ceiling`), so rooms
   in a row under one hipped ceiling (bridge, slope, viewport) get a wall hanging at each joint, and a room whose
   walls are low under a canopy (the viewport: 128 of wall, then glass) cannot use the feature on the side it opens.
6. **A room with a whole-ceiling level can have no other ceiling level**: the bridge lost its dome (octagon, 2048 to
   2320) to gain the hipped ceiling.

### Other defects met in round two

- `repro/platform_24_corners`: a platform outline of 24 points: "a face of PLATFORM_hall_0 has 24 corners (at most
  20): the room has too many openings in its walls". The cause named is wrong, and `validate` should refuse the
  outline itself. Cut into three platforms.
- `repro/flight_to_stacked_platforms`: a flight whose `to` point has two platforms one above the other (a pier
  under a gallery) climbs to the lower one's top: four steps of 12 to 1420 instead of 28 to 1484, no message.
  `probe` shows the wall. Kept the pier 16 short of the gallery's edge.
- A flight's `to` on the edge of its platform: "a flight runs from a point on the lower floor (`from`) to a point
  on the higher one (`to`: here 1036 to 1036), in steps of at most 40": the point must be inside; the message
  should say that it found the same floor at both ends because the point is on an edge.
- `repro/parapet_closed_ring`: a parapet path that returns to its first point: "the widened path crosses itself:
  its bends are too close together for its width". Two half rings instead.
- `oymap schema objects` and `validate` of this binary do not know `plates`, `floors` or an event's `trigger`,
  which `examples/shapes_gallery` uses ("objects.yml: plates: unknown key"): the example does not validate with
  the built tool, and the walk-on pads stay wall switches.
- `oymap compare`'s report holds the 40 worst points only; a per-point list would let a rebuild see every loss of a
  sector. The eye of a point stands 160 above each map's own floor, so a sunken level with a sharp edge where the
  original has a bank scores worse than no level (the hold's trenches: 82 % flat, 79 % with trenches as wide as
  the banks, 86 % with them cut back to where the machines end).
- The game's `walk_to` reports "arrived" by plan distance alone: a target under the floor it stands on (the lobby
  under the hall) is reached at once, and an assert straight after a descent catches the party in the air.

### Gaps still open, most harmful first

1. **A block whose top slopes** (a wedge): the hall's four raking buttresses on the south wall (512 deep, 1036 to
   1420), the banks of the hold's trenches, the pilot pits' ramps, the consoles' sloped tops. Field: `top_slope` on
   a platform, or a level with `slope`.
2. **Curved or many-sided vaults**: one leaning level gives two planes where the hall has three and the hangar
   four. Field: `ceiling_levels` standing on one another, or `vault: {spring, crown, segments}`.
3. **Openings into a whole-ceiling level, and a level on top of one** (defects 5 and 6): bridge, viewport, dome.
4. **A lift through a floor hole** (defect 1) and a hole round a column (defect 4): cargo pit, reactor tube,
   reactor hole. The spiral stair round the column is still not built: the pit at 908 is fenced, not reached.
5. **Moving things that are not a door or a lift** (round one's gap 9, unchanged): the pod bays' double decks, the
   cargo pit's retracting rim (left out: a fixed rim would shut the lift in), cranes, stasis partitions.
6. **Doors that slide sideways or in two leaves** (round one's gap 6, unchanged); with doorways one above another
   it now also decides whether the lower door can open at all (defect 2).
7. **Walk-on triggers** (round one's gap 7): `plates` exist in the example but not in the built tool.
8. Levels and pillars still may not touch a wall: the hold's trenches end 32 short of the east wall; the hangar's
   west walkway is a platform's job now but was not built (the pod bays behind it are still plain rooms).
9. Corridors' six-sided section, switches not on a wall, placed monsters and items: as in round one.

## Round three (2026-11-12, movers, panels, thresholds and the fix batch)

Everything above stands as written then; where this section says otherwise, this section is current. Edited by hand
again (no generator). Scratch: `output/studio_cal/mm7_7d23/` (`r3.sh` the loop, `compare_r3/`, `ingame_r3/`,
`shots_r3.yml`, `play_r3.log`, `r3/` with the start copy of the project, measurements and the repro writer
`r3/mkrepro.py`, `repro/` for the repros named below).

### Scores

| | `oymap compare` | shape (distances) | textures | rooms | faces |
|---|---|---|---|---|---|
| Start of round three (round two's project) | 93.1 % | 93.6 % | 92.1 % | 47 | 1,680 |
| Doors as the original's leaves (sideways, pairs as `leaves: 2`), flipped `from` | 93.3 % | 93.6 % | 92.4 % | 47 | 1,869 |
| Cargo bay one room with the pit as a floor hole, lift through it, rim mover, rail channel, pad dais | 93.7 % | 94.2 % | 92.5 % | 47 | 1,943 |
| Reactor tube as a floor hole, upper east lift merged with the top landing, thin east lifts | 93.8 % | 94.4 % | 92.6 % | 46 | 1,948 |
| Pod bays as shafts with two decks, stasis beds, engineering vestibule and lockers | 93.9 % | 94.5 % | 92.6 % | 50 | 2,162 |
| Hold trenches the original's full length (honest, scores lower), west lift mouths | 93.8 % | 94.3 % | 92.5 % | 51 | 2,183 |
| Station, locker and bay-wall textures; walkway; reveals a3b; thresholds sfw7a; piers flush (`to_height`) | 94.2 % | 94.3 % | 93.7 % | 52 | 2,197 |
| Bridge dome on the hipped ceiling; console ring sfw3 | **94.3 %** | **94.4 %** | **93.9 %** | **52** | **2,240** |

- Points without a floor: 0 (was 0). Mean ceiling difference 25.8 to 23.8. Deck ceiling, measured by
  `r3/ceilmeas.py` on a 64 grid against the original's faces: mean difference 55 without the dome, 35 with it.
- `calibration/compare.py`: "19 in, 11 near, 5 out" (round two 25, 6, 4). The losses are counts and minima: the
  lockers are 64-high sectors of 18,432, and the extra rooms (vestibule, mouths, walkway, lockers) raise the sector
  count; the original packs them into its sectors 1, 8 and 9.
- Rooms reached: `audit --reach` 6 of 52 with the doors as they start, 48 with every door out of the way; the other
  four are the three wall lockers (niches 64 high) and the walkway, which in the game is reached only from a pod deck
  raised while someone works its panel in the control room (the original's walkway is in the hangar's sector, so its
  solve counts it reached).
- `solve`: **six waves** (0 to 5) against the original's five (was seven). Order of areas as the original's. The one
  wave left is the top deck control room: the original's event 40 (open door 60, the control room's) is also bound to
  the lower hold's door faces (738, 740), so the original opens the control room from wave 2; the rebuild does not
  copy that cross-binding (nor event 30's: the hold door opened by stepping on the west lift's lower doorway floor).
  The upper east lift now shares one room with the top landing, as the original's sector 21 does, which removed a
  wave. Other differences are sector cutting: the pit and the bay above it are one sector in the original (cargo
  bays and west corridor one wave earlier there).
- **Playtest: passes, 149 steps** (`play_r3.log`, was 115). New: pod bay 2's panel in the control room moves both
  decks and the party stands on the lower deck at the hangar's level; the cargo lift sinks the rim round the pit;
  both transporter pads by walking onto them (`walk_to` with `via` on the pad); the engineering vestibule, its
  partition door (two halves up and down) by its panel, a wall locker's shutter by its panel; down the lower east
  lift into the corridor, stasis room 1's beds come out when the party steps in and go back when it steps onto the
  plate in the corridor. Still passing over changed parts: the reactor lift through the hole, the hall stairs ending
  on the gallery over a pier flush with it (`to_height`), the west lift through its mouths, the thin east lifts.
- In-game pairs (`ingame_compare.py ... shots_r3.yml ingame_r3 --root output/studio_cal/mm7_7d23/root`): 11 pairs
  (the bridge-dome camera has no floor under it in the original and was skipped), edge agreement 0.62, blurred
  difference 0.049. Looked at: pit rim 0.88 and pod bays 0.85 read as the original; the vestibule with its partition
  door and panel reads right (0.65); the stasis room shows the beds' 16-unit stubs where the original's beds fold to
  nothing; the hold's machines read as blocks with upright sides where the original's slope down to the banks; the
  top landing's walls show the texture's phase 128 off (the room's walls start at 1484 under the landing, the
  original's at 1868); the hall's door pair and the west lift's mouth match in place, the wall bands sit higher.

### What changed

- **Doors**: every door is what the original's leaves are: pairs `kind: slide_left, leaves: 2`, singles
  `slide_left`/`slide_right` toward the side the original's leaf folds to, 32 thick as the original's, single leaves
  with the original's surface on each side (`back_surface`: d23 a2b/a3b, d27 a2c/a2b, d28 a2b/a2c, d60 a2c/a2b). The
  two lift doors that slid down in round two (d28 under the west lift's gallery doorway, d51) slide sideways now.
  Two exceptions (see gaps): d51 is two halves and d55 slides south.
- Openings flipped so `from` is the side the party comes from (bridge_w_gallery, corr_cargo_e, corr_w_hall,
  crew_hall, hall_corr_e, both west lift doorways; `along` mirrored), because of the solve defect below.
- **Cargo bay**: one room; the pit is `open:cargo_pit` (`in: floor`) over `room:cargo_shaft`, and `lift:cargo` rises
  through it. `mover:cargo_rim` (door 38: a U of 64 x 96 round the pit) stands while the lift is down and sinks
  98 when it rises; `evt:lift_cargo` toggles both, as event 151 does. The rail channel is a leaning ceiling level
  (1420 to 1468) with two rails at 1548 standing on its top. The transporter pad is a dais 32 high
  (`platform:pad_w`) and the event's step source (event 457), with the lowered ceiling over it as a hanging block.
  The same channel and pad in the east bay (event 458).
- **Reactor**: the lift tube is a floor hole of the reactor room with `lift:reactor` rising through it; the three
  side openings of round two are gone. The console ring is sfw3 like the original's outer faces.
- **East lifts**: `lift_e2` holds the upper lift and the top landing round its head (an L-shaped platform 384 high);
  both east lifts are plates 9 thick (`thickness: 9`), as doors 47 and 50 are.
- **Pod bays**: shafts from -384 to 992 with two movers each (upper deck 196..260, lower deck -348..-316, travel 576
  together, events 451 to 454 from four panels in the control room); back walls a1b. A walkway room at 736 over the
  bay mouths (x -720..-464), open to the four bays.
- **Stasis rooms**: two beds each as stretching movers (doors 52, 54, 56, 58) that come 384 out of the wall when the
  party steps onto the room's floor (events 459, 463, 467, 471: `trigger: step`, `source: room:cellN`) and go back
  when it steps onto a plate in the corridor in front of the door (460, 464, 468, 472).
- **Engineering**: `room:vest` (the vestibule behind the hall's door pair) with a partition door of two halves
  up and down (d19/d20, event 10 from its panel) and a window into the station; three wall lockers (`room:locker1`
  to 3, 64 high, 144 deep) behind shutters that drop (d77 to d79, events 157 to 159 from their panels); station walls
  a2d with the alcoves' walls a2i, as the original's.
- **West lift**: `room:lift_w_mouth`, the two funnel mouths between the shaft and the hall (384 wide at the shaft,
  192 at the doors, a slab from 1292 to 1484 between them), as the original's sector 8.
- **Hall**: the piers under the gallery are flush with its edge, and the side flights end on the gallery by
  `to_height: 1484` (round two kept the piers 16 short).
- **Bridge**: the hipped whole ceiling's top is a rectangle reaching over the dome (3838..4866, -10048..-8862) and the
  dome stands on it in four stacked levels (2080 upright, 2208, 2272, a point at 2320), all a3bs.
- **Lower hold**: the trenches run the original's full length (3472 to 4720) and the machines stand in them
  (rise 192 from the trench floor to 288). This scores lower than round two's shortened trenches (sector 5 from
  85.6 % to 79.5 %, total -0.2): the original's trench floor is at 96 from 3472 to 3696 and from 4176/4352 to 4752,
  and round two had cut the trenches back to where the machines end because that measured better. Kept the honest
  shape.
- Surfaces: reveals a3b in every theme (the original's doorway sides), `threshold` sfw7a on every door opening (the
  original's doorway floors). The reveal's top is then a3b where the original's is sfw7a (158 rays): one surface
  covers sides and top.

### New features: what worked as described

- `kind: slide_left|slide_right`, `leaves: 2` (sideways pairs and the up-and-down pair), `back_surface`, thickness 32.
- A lift under a floor hole rising through it (cargo pit, reactor tube; ridden in the playtest). Round two's repro
  `repro/lift_through_floor_hole` validates and builds now.
- Lifts with `thickness` (the east lifts, ridden).
- `movers`: vertical (decks, rim), stretching sideways (stasis beds), with `outline` (the rim's U against a wall),
  driven by switches and step events; `door_state` follows them.
- `trigger: step` with a room's floor, a platform with an `id`, and a plate as source; teleport preset on a step.
- A ceiling level on another's flat top, any depth (rails, the dome's four tiers).
- `to_height` on a flight ending where a pier stands under a gallery.
- `threshold`, per-wall surfaces. Not used: `panels` and `ends` (the original's walls here change texture by whole
  wall or by room, not in panels), `tread` and `top_surface` on flights (treads and side tops are the defaults'
  textures already), a climbing `path` room (no climbing tunnel in this map).
- Round two's defect "a `slide_up` leaf of a lower doorway blocks the doorway above" is fixed: the build refuses it
  and names both openings and heights (`repro/stacked_door_slide_up`).

### Refused or not sayable (repros in `output/studio_cal/mm7_7d23/repro/`)

1. **A mover under a raised ceiling level** is measured against the room's ceiling: "objects.yml: movers[0]: the
   mover's top at its start is at 432, above the ceiling of room:bay there (384): shorten `travel` or `height`, or
   lower `bottom`" (`repro/mover_under_ceiling_level`). The two cranes (doors 14 and 44: a slab at 1404..1436 with
   hangers into the rails, 1,408 along the channel) run in the bays' raised channel and are placeholders.
2. **A chest cannot ride a mover**: "objects.yml: chests[0].floor_height: there is no floor at 32 at [640, 640] in
   room:a: the floors there are at 0" (`repro/chest_on_mover`). Chest 1 stands on pod bay 2's lower deck in the
   original and comes up with it; it is a placeholder here (the map has three chests, the original four).
3. **A lift cannot fill its shaft and rise through a hole**: the hole must stand 16 inside the lower room's walls as
   well as the upper room's, so the lift (which must lie under the hole) is 16 short of the shaft on every side, and
   a pit flush with the upper room's wall cannot be a hole at all: "the hole must lie inside room:shaft with every
   corner at least 16 units from its walls" (`repro/lift_fills_shaft`). The cargo pit room is 16 wider than the hole
   on three sides and the lift 1040 wide (original 1056); the reactor tube's room 16 wider all round.
4. **A whole-ceiling level's top has one point per room corner**, so a hipped ceiling whose top has more corners than
   the room (the bridge: a seven-cornered top over a four-cornered room) cannot be said; an `outline` along the
   room's walls with extra points is refused: "the region cannot be cut out of room:a: keep it inside the room and
   clear of its walls" (`repro/hipped_top_more_corners`). Did: a rectangle top reaching over the dome (the north hip
   steeper than the original's).
5. **A ceiling level against the room's walls** is refused the same way (`repro/ceiling_level_against_wall`). The
   bays' rail channels run wall to wall in the original; here they stop 16 short of both end walls.
6. **A level on a level's top cannot share the top's edge**: "its outline is that top's own points (the whole top,
   once), or lies inside the top at least 1 unit from its edges" (`repro/level_on_top_shares_edge`). The rails start
   at the channel's slope edge in the original; here 1 unit inside (and 2 for the dome, where 1 was still refused).
7. **A sliding leaf needs room in the wall beside its doorway**; the original's leaves fold into the jamb (their far
   edge moves, their faces stretch), so two doorways 160 apart each with a 191 leaf are fine there: "the open leaf of
   door:lift would stand inside room:cell (slid left by 192 into the wall beside the doorway): the wall has no room
   for it there" (`repro/leaf_needs_wall_room`). d51 is two halves here, d55 slides south instead of north. Field: a
   leaf `kind: fold` (or `slide_*` with `stretch: true`).
8. **A plate exactly 16 from a wall** is refused though the message asks for at least 16
   (`repro/plate_16_from_wall`: "the plate does not lie inside room:a with every corner at least 16 from its walls");
   the same off-by-one round two found for holes, fixed there, not for plates. 17 passes.
9. **A plate under a hanging block** is refused as lying on a platform ("the plate lies on a level, platform or flight
   of room:a: a plate is cut into the room's own floor", `repro/plate_under_hanging_block`). Not harmful here: the
   pad's dais as a platform with an `id` is the better word (the original's trigger is the dais top).

### Round two's defects, checked again

- Lift through a floor hole refused: **fixed** (item 3 above is what remains).
- `slide_up` leaf blocking the doorway above: **fixed** (refused with a clear message).
- "24 corners ... too many openings" names the wrong cause: **stands** (`repro/platform_24_corners`, same message).
- A closed parapet ring refused as a path crossing itself: **stands** (`repro/parapet_closed_ring`).
- An opening cannot reach into a whole-ceiling level: **stands**: the built portal between the bridge and the slope
  to the viewport is 1548 to 1804 (the bridge's room ceiling), though the bridge's ceiling rises to 2048 and the
  slope's is 1960 (`oymap export output/studio_cal/mm7_7d23/build/cal7d23.blv`, portal face between sectors 23
  and 42).
- `oymap flow 7d23.blv --world mm7 --assets assets_dev --event 501`: **stands** ("GetPartyMemberCount(); (stopped: map
  script:2727: attempt to perform arithmetic on a nil value (local 'count'))").
- A hole exactly 16 from a wall: fixed (round two's repro validates).

### Gaps still open, most harmful first

1. **Blocks whose tops slope (wedges) and floors that slope inside a room**: the hall's two raking buttresses on the
   south wall (x 3456..3968 and 4736..5248, y -8160..-7648, 1036 rising to 1420: the worst points of the hall,
   "floor 216 lower" at -7936), the hold's trench banks, the pilot pits' ramps (1132 to 1260 over 192), the pad
   ramps, the console ring's sloped top. Field: `top_slope` on a platform or a `slope` on a level.
2. **Moving things the movers cannot say**: the cranes (mover under a ceiling level), a chest on a moving deck,
   folding leaves (refused items 1, 2, 7).
3. **Openings into a whole-ceiling level** (bridge to slope to viewport; round two's defect 5).
4. **Ceiling shapes**: the hall's faceted vault (a 1740/2028/2252 shape with notches in its top) as one leaning level;
   the bridge's seven-cornered top (item 4); levels against walls (item 5).
5. **Invisible walls**: the reactor drum (eight faces round the hole from 1132 to 1420, flagged invisible) keeps the
   party off the pit; here the console ring (80 high) does it. Field: a `barrier` (an unseen wall) on a path.
6. **Walk-on events the original has and the rebuild leaves out**: the close-behind floors (events 16, 18, 28, 50, 55,
   56: the vocabulary can now say them with `trigger: step`; left out because most are bound to floors far from the
   doors they close, which looks like the original's numbering slip, and closing doors behind the party would only
   make the playtest longer). The lift call events (155/156, 154/34 on panels at each stop).
7. Switches not on a wall (the consoles of the bays, the cranes, the power panel, the bridge's star console), placed
   monsters and items, the corridors' six-sided section, pilot pits' consoles: as in rounds one and two.

### Tool defects (this round)

- `oymap solve <L4>`: a door 32 thick is never opened from its `to` side, so a room behind it is "never reached";
  16 thick is ("repro/solve_two_leaf_from_side": `oymap solve output/studio_cal/mm7_7d23/repro/solve_two_leaf_from_side
  --assets assets_dev` gives "never reached: 1 sectors"; `repro/solve_door_thickness_16`, the same with one leaf 16
  thick, reaches both). Worked round by putting `from` on the side the party comes from.
- Follow-on errors after a refused object still appear: a refused hole gives "the lift would raise the party into the
  ceiling" and "there is no door lift:shaft" (`repro/lift_fills_shaft`); a refused mover gives "there is no door
  mover:crane" (a mover called a door); a refused plate gives "plate:p is a plate, which is clicked: a step event's
  source is ... a plate" (contradicts itself).
- `oymap solve` needs `map_stats` with `reference` or `slots` even on a test project, which `validate` passes
  without: "oymap solve: invalid node; first invalid key: \"map_stats\"", then "project.yml map_stats needs `id`,
  and either `reference` ... or `slots`".
- `oymap build`: a mover warning "rises to within 200 of the ceiling" is given for two of four identical movers
  (bay3_upper and bay4_upper, not bay1/bay2_upper).
- A beam `path` with bends is built as one concave underside face (`oymap export` of a build with the reactor drum as
  a five-point beam: face of 10 corners round the hole); not used in the end.
- An opening's `sill` counts from the higher of its two rooms' floors (a doorway from the lift room at 1484 to the top
  corridor at 1868 with `sill: 384` reached 2508). The schema does not say which floor.
- `compare`: a face flagged invisible (the reactor drum) is see-through for the rays, which is right, but nothing in
  `oymap export` or `metrics` says a face is invisible, so a rebuild reads it as a wall to build (cost one wrong turn).

### Unsure of in the original

- Whether the walkway at 736 over the pod bays is meant to be reached (only from a raised upper deck, whose panel is in
  the control room).
- The original's stasis beds start folded into the wall and come out only when the party steps into the room; what
  they are for in the story (nothing lies on them).
- Why events 16, 18, 28, 30, 40, 50, 52, 55, 56 are bound to floors and doors far from what they move (see gap 6).

## Round four (2026-11-12, night: tunnels, uneven roofs, wedges, banks, floor events)

Everything above stands as written then; where this section says otherwise, this section is current. Edited by hand
and by one-off scripts (below). Scratch: `output/studio_cal/mm7_7d23/` (`r4.sh` the loop, `r4_backup/` the project as
the round found it, `compare_r4_start/` and `compare_r4/`, `r4/` the scripts, trials and exports, `shots_r4.yml`,
`ingame_r4/`, `play_r4.log`, `repro/` for the repros named below).

### Scores (the merged measure)

| | `oymap compare` | shape (distances) | textures | rooms | faces |
|---|---|---|---|---|---|
| Start of round four (round three's project) | 94.4 % | 94.7 % | 94.1 % | 52 | 2,240 |
| Two hall buttresses; hold trenches at full length with banks; pilot pits with ramps; pad ramps; console rings as sloping blocks | 95.5 % | 96.0 % | 94.6 % | 52 | 2,175 |
| Hall stairs' treads 64 as the original's; the two corner buttresses | 95.8 % | 96.3 % | 94.8 % | 52 | 2,183 |
| West and east corridors, north and south spines as tunnels | 95.9 % | 96.4 % | 95.0 % | 60 | 2,414 |
| Hall vault as `ceiling_points` | 96.4 % | 97.1 % | 95.0 % | 60 | 2,437 |
| Bridge roof and dome as `ceiling_points` | 96.5 % | 97.3 % | 94.8 % | 60 | 2,460 |
| The two cranes as movers; floor events (no shape change) | 96.5 % | 97.4 % | 94.8 % | 60 | 2,499 |
| The top landing's strip over the lower east lift | 96.6 % | 97.4 % | 94.8 % | 61 | 2,514 |
| Captain's cabin: door vestibule and hipped roof | 96.7 % | 97.6 % | 94.9 % | 61 | 2,528 |
| The bridge's two horseshoe desks | **96.8 %** | **97.6 %** | **94.9 %** | **61** | **2,602** |

- Points without a floor in the rebuild: 0 (was 1). Mean ceiling difference 23.9 to 10.9.
- `calibration/compare.py`: "15 in, 11 near, 9 out" (round three 19, 11, 5): the losses are counts and minima again; the
  spines' alcoves and ends, the lockers and the strip are small sectors of their own where the original packs them.
- Rooms reached (`audit --reach`): 6 of 61 with the doors as they start, 57 with every door out of the way; the other
  four are, as in round three, the three wall lockers (64 high) and the walkway over the pod bays.
- `solve`: seven waves (0 to 6), the same as round three's project gives with today's tool (the original six); order of
  areas as the original's; never reached: the walkway, and three niches (the lockers).
- **Playtest: passes, 157 steps** (`play_r4.log`, was 149). New in it: the west crane from its console; the reactor
  gallery's east floor calling the west lift up to the gallery (event 18, far from the lift, as in the original), and
  the lift's panel bringing it down before the party rides it; the ramp's floor shutting the ramps' gallery doors
  behind the party (event 55); the captain's door shut behind the party by the cabin's floor (event 50) and opened from
  inside. Still passing over changed parts: the corridors as tunnels (both doors of the west corridor, the stasis room,
  the beds going back when the party steps into the corridor), the spines' junction door, the east lifts round the new
  strip, the hall stairs with the original's treads, the middle pilot pit's ramp.
- In-game pairs (`ingame_compare.py ... shots_r4.yml ingame_r4 --root output/studio_cal/mm7_7d23/root`): 13 pairs at
  the changed places, edge agreement 0.75, blurred difference 0.041 (`ingame_r4/diff/`). Looked at: the buttresses and
  the west crane read as the original's; the corridors have the original's narrow floor and leaning sides, but the
  band textures sit at another height (gap 4); the bridge now shows its desks; the trenches read right, the machines
  lack their nozzles and green lamps; the vault pair (0.46) shows the right facets with the texture grid running
  differently across them; the pilot pit pair (0.53) is dominated by the canopy's lightmap and the console in front of
  the pit, which is not built.

### What changed (target by target)

1. **Wedges and sloping floors.** The hall's four raking buttresses (two on the south wall, two in its corners under
   the gallery: x 2432..2688, 3456..3968, 4736..5248, 6016..6272, y -8160..-7648, 1036 rising to 1420) are platforms
   with `top_slope: {to: 384, toward: south}`. The lower hold's three trenches run the original's full length (3472 to
   4736, 16 short of the east wall) with the flat floor 128 wide at 96 and `bank: [144, 0, 144, 0]`: **sector 5 went
   from 85.5 % to 95.1 %**: with banks the full-length trenches stop costing. The original's bank is two slopes (80 out
   and 64 up, walkable, then a lip 16 out and 64 up); one bank of the original's whole run (96, 128 up) is steeper than
   the floor rule, its faces become walls and 14 stand points on the banks lose their floor (sector 5 at 56.2 %); 144
   (0.89) keeps the walkable slope's height within 7 at the original's 80 and puts the top edge 48 wider. The round-two
   steps out of the trenches (not in the original) are gone. The three pilot pits are levels at 1132 with the ramp as a
   wedge inside (`rise: 0, top_slope: {to: 128, toward: north}`), ending in the original's 32 lip at 1260/1292 (a bank
   would have run to 1292 without the lip). The transporter pads have their two ramps each as `top_heights` blocks
   (the trapezoids of faces 167/895 and 755/881). The console ring round the reactor pit is eight blocks with sloping
   tops (outer 1100, inner 1132; the two south-west and south-east pieces low rails at 1068), the gallery's ring eight
   more (1548 outer, 1580 inner); the parapets they replace are gone. The hall stairs' treads are 64 as the original's
   (`to` 64 further, so the twelfth riser lands on the landing): the hall's worst point of round three, a step 28 off,
   is gone. The hall's sectors went from 95.0/95.3 % to 99.3 %.
2. **Corridors as tunnels.** Checked myself first: sectors 41 and 11 are eight-sided,
   `[[-128,0],[128,0],[192,96],[192,160],[128,256],[-128,256],[-192,160],[-192,96]]`, as the code agent measured; the
   top deck's spines (sectors 29, 30) are eight-sided too but wider, `[[-128,0],[128,0],[224,96],[224,160],[128,256],
   [-128,256],[-224,160],[-224,96]]` (45-degree bevels). `room:corr_w`, `room:corr_e`, `room:cross_n`, `room:cross_s`
   are path rooms with `section` (surfaces lower/wall/upper from the original: a3b/a1b/sfw2, sfw3/a1b/sfw1a,
   sfw1b/a1b/sfw1b). Their doors stand in plain side doorways: the leaning sides run from the section at the
   neighbouring path points to a side doorway's jambs, so each doorway has path points 32 to 33 beyond its jambs and the
   section is whole everywhere else (the original turns abruptly at its jambs). The east corridor's south end is a
   square end (`start: {width: 192, length: 16}`) holding stasis room 4's door, the spines' ends square ends into the
   junction door (256) and into their narrow ends (192, now rooms of their own). The spines' six alcoves are rooms of
   their own behind side doorways 8 from the tunnel, where the original has its energy fields (see gaps). Sector 41
   93.3 to 97.8 %, 11 95.2 to 96.5 %, 29 92.2 to 96.5 %. Doors are not refused here: a door in a tunnel's side doorway
   validates and builds whichever room is `from` (the brief says doors are refused inside a tunnel). What does not fit:
   the stasis rooms' "beds back" plates (gap 6) and the lower corridor (sector 19, gap 3), left a plain room.
3. **Ceilings.** The hall's faceted vault is `ceiling_points` (24 heights: the vault's facet corners at 2252 and 2028,
   the walls at 1740) with `ceiling_lines` along the original's facet edges, in place of the leaning whole-ceiling
   level. The bridge's roof is `ceiling_points` (37: the hipped roof with its seven-cornered top at 2048, two points on
   the south wall at 2048, the dome's rings at 2048, 2080, 2208, 2272 and its point at 2320; the dome's upright ring
   2048 to 2080 is drawn as a lean of 10, the steepest the roof rule takes), in place of the hipped level with the
   rectangle top and the stacked dome. The captain's cabin has its door vestibule (the original's trapezoid,
   6368..6464) and its hipped roof (walls 1804, ring 1932, top 1996: 10 points). These three rooms took the original's
   own corner points one for one: in each, every point given is a corner where the roof changes slope. The bridge-to-
   slope portal still stops at 1804 (gap 1).
4. **The hold's machine blocks.** Confirmed against the original: the machine's top is at 288 (face 2548, x 3616..4128,
   y -704..-576), its flanks come down onto the banks at 160 and its underside reaches the trench floor (96) at x 4176:
   standing from 96 to 288 is right. They are now 512 x 288 at the foot (the original's footprint at 160) tapering to
   512 x 128, with the sloping nose (hive1, 288 to 192 over 4128..4352) as a wedge. The build still warns ("stands in a
   sunken level: it is now measured from that level's floor (96) ... add 128 to its `base`"); nothing in the schema
   lets an author answer it (no field acknowledges the new rule; `notes` does not silence it).
5. **Events.** The floors the original's handlers really run (`oymap flow --event N`): 15 (reactor room's floor by the
   lift tube: opens the gallery's door to the east landing), 16 (reactor gallery's west floor: closes it), 18 (gallery's
   east floor: the west lift up to the hall gallery, its upper door open, its lower door shut), 28 (the west lift's
   upper mouth: shuts the hangar's corridor door), 30 (its lower mouth: opens the lower hold's door), 50 (the bridge
   floor before the captain's door and the cabin's floor inside it: shut that door), 52 (the top landing round the
   upper east lift: opens the west ramp's door to the bridge), 55 (the ramps: shut the ramps' doors to the gallery), 56
   (the east landing: shuts the ramps' doors to the bridge). Sources: five plates, `platform:mouth_slab`,
   `platform:top_landing`, the rooms `lift_w_mouth`, `ramp_w`, `ramp_e`, `east_landing`. Events 58, 85, 91, 92 are bound
   to floors but have no handler: nothing. Also new: the Sparks timers 476/477 (`trigger: timer`, every 4 and 2, `cast`
   spell 15, level 20, master, from the original's points toward 0, 0, 0, once the console has raised the alarm), and
   the two cranes (doors 14 and 44) as movers under the bays' raised rail channels with their four consoles (events
   455, 456) as wall switches placed by `at`: round three's refusal is gone (`repro/mover_under_ceiling_level_r4`
   builds; the round-three repro itself is refused for its channel touching the walls).
6. **`points.json`.** At the start one point had "a wall through this place" (7168, -4864, 1868: the top landing's
   strip over the lower east lift, faces 909 of sector 21). The wall was wrong: the upper lift's room had a notch there
   to keep clear of the lower lift's room. The strip is now split: its part beside the upper lift's shaft belongs to that
   room (its landing block wraps the shaft on three sides), its part over the lower lift is `room:landing_strip` (1868)
   standing over the lower lift's room (ceiling 1740), open to the upper lift's room on two sides. Sector 21 72.2 to
   93.6 %. No point is without a floor now.

Scripted (one-off edits, numbers from `r4/` exports of the original, each diff checked): `r4/ring_pads.py` (rings,
pad ramps), `r4/corr_e.py`, `r4/corr_e_plates.py`, `r4/corr_e_events.py` (east corridor), `r4/cross.py` (spines),
`r4/hall_vault.py`, `r4/deck_roof.py`, `r4/cranes.py`, `r4/floor_events.py`, `r4/strip.py`, `r4/captain.py`,
`r4/desks.py`, `r4/sparks.py`; the rest by hand. Other changes: the reactor hole is 1 unit smaller (defect below);
the captain's door is 224 wide (254: the vestibule is 256 at the door, and an opening needs 16 of wall each side);
stasis room 4's doorway is the east corridor's square end (192 wide, was 190); the hall's west corridor door and the
cargo door's `along` are on the tunnel's walls by number.

### New features: what worked as described

- `platforms[].top_slope` (buttresses, pit ramps, machine nose) and `top_heights` (pad ramps, console rings, outlines
  of four corners, concave not needed); a wedge inside a sunken level; platforms that touch each other.
- `levels[].bank` with a list of runs (trenches); `section` on path rooms with side doorways, doors in them, square
  ends with a door and into a room as wide; `ceiling_points` with `ceiling_lines` (three rooms, up to 37 points);
  a mover under a raised ceiling level; switches by `at`; `trigger: step` with a plate, a platform with an `id`, a room;
  `trigger: timer` with `cast`; `opens`/`closes` with doors and lifts on a switch preset.
- Not used: `floor_points` (no room here has a cave floor), `section` mouths (`shape: section`: every tunnel end here is
  a doorway or closed), climbing tunnels, `flights[].from_height|open_below`, arches into upright ends (gap 1 explains
  why the bridge cannot use them now that its roof is `ceiling_points`).

### Refused or not sayable (repros in `output/studio_cal/mm7_7d23/repro/`)

1. **A sloping block beside a floor hole**: a platform with `top_slope` or `top_heights` whose edge lies on the hole's
   edge makes the hole refused, "rooms.yml: openings[0]: the hole lies under a level, a platform or a flight of room:a:
   it must be cut in the room's own floor ..."; a flat block on the same edge, or the sloping one 1 unit away, passes
   (`repro/platform_edging_floor_hole`). The reactor gallery's console ring lines the hole: the hole is 1 unit smaller.
2. **A platform cannot rise through a floor hole into the room above**: "the platform reaches 640 but the ceiling of
   room:a at that place is at 384 ... it stands 256 into whatever lies above" (`repro/platform_through_floor_hole`). The
   reactor's column runs from the pit (908) to the shaft's top (2316) in the original, with the core's bulge (radius
   256, 1484 to 1804) on the upper deck; here it ends at the lower room's ceiling (1420), and the bulge is not built.
3. **An opening stops at the lowest ceiling point over it**: two rooms with matching ridges keep a wall in the joint
   above the eaves (`repro/opening_under_ceiling_points`: portal to 256, triangles up to 512). As documented, but it is
   what keeps the bridge, the slope and the viewport (one roof in the original) apart: the bridge-to-slope portal is
   1548 to 1804 under a roof that rises to 2048 on both sides, and the slope and viewport keep flat 1960 ceilings
   (`ceiling_points` there would add a wall 1843 to 2048 at each joint).
4. **A plate in a tunnel stretch with a side doorway**: "objects.yml: plates[0]: In a tunnel ... a plate is the floor's
   whole width ... and that stretch has a doorway in its side, where the floor reaches out to the doorway: put the plate
   in another stretch" (`repro/plate_in_tunnel_doorway_stretch`). The original's "beds back" plates (events 460, 464,
   468, 472) are the floor strips in front of the stasis rooms' doorways; one room's floor runs one event ("room:corr_e
   already has an event; one object runs one event in v0"), so all eight beds go back by one event on the corridor's
   floor.
5. **A level (or its bank) against a wall** (`repro/level_bank_against_wall`: "the region cannot be cut out of
   room:a: keep it inside the room and clear of its walls"): the trenches end 16 short of the hold's east wall, where
   the original's run into it.
6. Still refused from round three: `chest_on_mover`, `leaf_needs_wall_room`, `ceiling_level_against_wall`,
   `level_on_top_shares_edge`, `lift_fills_shaft` (same messages); `hipped_top_more_corners` too, but `ceiling_points`
   now says the bridge's seven-cornered top.

### Round three's defects, checked again

- Fixed: the bay movers' "within 200 of the ceiling" warning comes for all four identical movers; a plate exactly 16
  from a wall passes; `repro/platform_24_corners` and `repro/parapet_closed_ring` validate; `oymap flow 7d23.blv
  --event 501` runs every party member's branch; `repro/solve_two_leaf_from_side` reaches both rooms; a mover under a
  raised ceiling level builds.

### Gaps still open, most harmful first

1. **One roof over several rooms** (bridge, slope, viewport, window: sectors 37, 38): an opening's top is level at the
   lowest ceiling over it, so rooms under one sloping roof keep walls at their joints, and one room cannot hold them
   all (the slope's floor and the viewport's need two floor surfaces; the window rakes to the glass). The viewport is
   still the worst sector (86.6 %, ceiling 59 off). Field: an opening whose top follows the two rooms' ceilings
   (`height: ceiling`), or `floor_points`/`ceiling_points` with a surface per region.
2. **Things in a floor hole**: the reactor column and core through the hole (refusal 2), the invisible drum round the
   hole on the upper deck (faces 1507 to 1514, invisible, 1580 to 1996), the spiral steps. Sector 32 93.8 %. Fields: a
   platform that may rise through `in: floor` holes; `barrier` (an unseen wall) on a path.
3. **The lower corridor as a tunnel** (sector 19, 92.6 %): it branches (a T to the reactor lift tube, a Y from the
   hangar), and its two side branches meet the main way at overlapping places (the hangar branch on the west side at
   y -1792..-1392, the reactor branch on the east side at -2112..-1728), so no path points can keep the leaning sides
   whole there; its two diagonals are sheared, not mitred (384 wide measured along x, 329 across the way) and cut on x
   planes at their ends. Fields: tunnels joined at a side (a square end into another tunnel's side doorway, with the
   triangles the original has), a section per stretch or `shear`, an end cut on a given plane.
4. **Texture phase on bands and tunnel sides**: the original sets each band's texture so that its top row starts at the
   band's top (A1b band: v 0 at 1196 by `texture_delta_v`; sfw2 at 1292); the rebuild's surfaces tile from a common
   origin, so the corridors' green lamps sit 84 lower than the original's. Field: `offset` (or `align: top`) on a surface.
5. **`ceiling_points` take one surface**: the bridge's dome is a3bs in the original and sfw7a here (sector 37's textures
   95.4 % before, 92.2 % now, though its shape rose 93.3 to 97.1 %). Field: a surface per region or per facet line.
6. **Walk-on plates where the floor is not plain**: in a tunnel stretch with a doorway (refusal 4) or on a sloping floor
   (events 55 and 56 split one ramp between its upper and lower part in the original; here the ramp's whole floor runs
   55 and 56 runs only from the east landing). Fields: plates in doorway stretches and on slopes, or two events on one
   floor.
7. **Banks of more than one slope, levels against walls**: the trenches' lip (refusal 5; target 1 above).
8. **Moving things** (round three's gap 2, less): a chest on a moving deck, folding leaves, the cranes' frames and
   hangers (each crane is one slab).
9. **Switches not on a wall** (the power panel is the consoles' tops, the bridge's star console, the bays' crane
   consoles stand out from the wall), the spines' energy fields (HIVE1 slabs 8 thick, invisible and blocking, attr
   0x2000, in front of the six alcoves and the narrow ends), placed monsters and items, the lift call events (473/474,
   20 are bound to nothing; 154, 155, 156, 34 to lift panels), `SetLight`.

### Tool defects (this round)

- `oymap build <repro> --assets assets_dev --out <scratch>` still writes `ids.lock.yml` into the project folder
  (`repro/mover_under_ceiling_level_r4` and `repro/opening_under_ceiling_points` got one; removed): the brief says
  `--out` keeps it out.
- The wall numbers of a path room (`from_wall`/`to_wall`) are not documented and had to be probed: right sides 0 to
  n-1 by stretch, the end wall n, the left sides n+1 to 2n from the last stretch back, the start wall 2n+1, and a square
  end adds a stretch of its own (`r4/trial` history; east corridor: cell doors on walls 2, 4, 6, 8, the hall door on
  18, the cargo door on 15). Without them the "longest shared stretch" picks the wrong stretch once a path has points
  beside its doorways ("in the side of the tunnel room:corr_w: the doorway reaches from 1010 to 1264 along a side 1280
  long").
- A tunnel's side doorway in a long stretch twists the whole stretch's sides (the leaning sides run from the section at
  the far path point to the jambs: faces 1300 long, `r4/trial.json` of the first west-corridor trial); nothing warns.
  The original's sides stay whole and close at the jambs with small upright triangles.
- `oymap validate` refuses a sloping block next to a floor hole but not a flat one (refusal 1): the two should agree.
- The sunken-level warning on the hold's machines cannot be answered (target 4).
- The brief says doors are refused in a sectioned tunnel; a door in a tunnel's side doorway validates and builds.

### Unsure of in the original

- What events 15 and 16 (door 26 open/shut) are meant for on the reactor room's and gallery's floors, far from door 26;
  likewise 18, 28, 30, 52: wired as the handlers run them.
- Whether the Sparks' target 0, 0, 0 means "toward the party" in the game; the rebuild passes it through unchanged.
- Whether the spines' alcoves (behind invisible energy fields) are meant to be reached; here they are open.

## Round five (2026-11-13: contents, behaviour, one roof, the lower corridor)

Everything above stands as written then; where this section says otherwise, this section is current. Briefed by
`devdocs/map_studio/rounds/ROUND_FIVE.md`. Scratch: `output/studio_cal/mm7_7d23/` (`r5_backup/` the project as the
round found it, `compare_r5_start/` to `compare_r5_d/`, `r5/` the scripts and trials, `shots_r5.yml`, `ingame_r5/`,
`play5.sh` and `play_r5_*.log`, `repro/step_off_slope*`).

### Scores

| | `oymap compare` | shape (distances) | textures | rooms | faces |
|---|---|---|---|---|---|
| Start of round five | 96.9 % | 97.7 % | 95.0 % | 61 | 2,609 |
| Contents, lights, drums, fields, lift panels (no shape change) | 96.9 % | 97.7 % | 95.0 % | 61 | 2,748 |
| One roof: slope, viewport and window by `ceiling_points`, mouths following it, dome surfaces | 97.2 % | 98.1 % | 95.1 % | 61 | 2,765 |
| The slope's trapezoid (the original's floor outline) ending 32 above the viewport | 97.4 % | 98.4 % | 95.2 % | 61 | 2,760 |
| The lower corridor's main way as a tunnel | 97.5 % | 98.4 % | 95.2 % | 64 | 2,796 |
| The side glass over the viewport (`ceiling_surfaces`) | **97.5 %** | **98.4 %** | **95.3 %** | **64** | **2,796** |

- Sectors: 38 (slope, viewport, window) 87.8 to 95.7 % (shape 87.2 to 97.9); 37 (bridge) 95.7 to 98.8 % (textures
  92.4 to 96.6); 19 (lower corridor) 92.6 to 93.0 %. No point without a floor.
- `calibration/compare.py`: "14 in, 12 near, 9 out" (round four 15, 11, 9; the three corridor rooms add sectors).
- `audit --reach`: 6 of 64 sectors with the doors as they start, 50 with every door out of the way. Not reached: the
  eight rooms behind the spines' energy fields (as in the original, where they are part of the spines' sectors), the
  three lockers and the walkway (as before), and the viewport and window: `probe`, `reach` and `solve` stop at the
  32 step at the slope's foot, which the game walks both ways (playtest; tool defect 1 below).
- `solve`: seven waves (0 to 6) as in round four, the order of areas as the original's (round four's); never reached: the viewport
  and window (the step), the walkway, the alcoves and ends behind the fields, three niches (the lockers).

### Contents

- **Monsters: 17 of 17 placed** (objects.yml `monsters`, `monster:droid00` to `droid16`): actors 0 to 16 of
  `7d23.scene.yml` at their places and floors, by monster_data row (389 Sentinel Droid, 388 Seeker Droid, 390
  Assassin Droid), group 56, `hostile: false`. In the original they start invisible and peaceful (attributes 0x10000,
  the Invisible bit; the map's MMMerge supplement, event 65023, clears the group's Hostile bit and sets Invisible on
  every load) and nothing in the map's script ever shows them: the game never shows them. Said by `hostile: false`
  and `evt:droids_hidden` (`trigger: load`, `lua: evt.SetMonGroupBit(56, MonsterBits.Invisible, 1)`); there is no
  `visible`/`invisible` word on a monster (gap 3). Not said: the actors' `ally` 67.
- **Lying items: 5 of 5 placed** (`items`): sprite objects 0 to 4, three in the wall lockers (Blaster Rifle 867 in
  lockers 3 and 1, Blaster 866 in locker 2, on the lockers' floor at 1580) and two Blasters on the engineering
  station's floor (1484). Item numbers decoded from `raw_containing_item_hex`.
- **Item spawn points: 0 of 20.** The 20 type-2 spawn records (treasure index 5) stay placeholders (`item02` to
  `item47`, among them `placeholder:item47`, spawn record 46 in stasis room 3): `spawns` takes encounter slots only
  and `items` a fixed item; no word says "a random item of level 5 here". The build lists them.
- **Chests: 4 of 4 with the original's contents and trap.** `chest:bay` (chest 1) now rides pod bay 2's lower deck
  (`rides: mover:bay2_lower`) and comes up with it; contents from `initial_state.chests` (36-byte records): chest 1
  three Blaster Rifles and two random items, chests 2 and 3 one Blaster Rifle and two random, chest 4 a Blaster
  Rifle, two Blasters and three random; random items at level 6 (the map's treasure level); every one trapped (flag 1)
  as `trap_level: 1` (the damage is the map row's, 10d20). No quest item lies in a chest here. Chests 0 and 5 to 19
  of the original have handlers (180 to 195) bound to no face and are not built, as before.
- Lights: the original's 82 light records with attribute bit 8 (records 57-64, 84, 85, 123, 124, 150-157, 193-266)
  start disabled and no event enables them (`SetLight` is called for lights 1 and 2 only; MM7 maps switch lights by
  record number), so the game never lights them; they are dropped (the build warns for a dark light that no event
  lights, and suggests that). 182 lights remain.

### Behaviour: the events table brought up to date

73 handlers run in the original (69 bound to faces, the load events 1 and 65023, the timers 476 and 477). **61 do
the same thing under the same condition**, 12 differ, none is missing that the map can run (events 58, 80, 82, 85,
87 to 92 have no handler; event 7 moves doors 12 and 13, which the map does not have).

| Event | Here | Same? |
|---|---|---|
| 1 (load) | `evt:entered`: lights 1 and 2 off (`lights_off`) on every entry | differs: map vars 2 and 3 are not kept (nothing here reads them) |
| 65023 (load) | the build's group event (Hostile off) and `evt:droids_hidden` (Invisible on) | same |
| 475 | `evt:power`: var, text, the panel's texture, and now `lights_on: light:l001` | same |
| 376 | `evt:console`: item, qbits, alarm var, and now light 1 off, light 2 on | differs: works once; the original switches the two lights again on later clicks |
| 34, 154, 155, 156 | the east lifts' four panels (`switch:lift_e1_low/top`, `lift_e2_low/top`), and 34 also on the top corridor's door | same (new this round; the lifts are no longer clicked) |
| 473, 474, 20 | bound to nothing, as in the original | same |
| 29, 151 | the west and cargo lifts toggled by clicking the lift | differs: the original's panel (a console on the deck, a panel on the shaft wall) is not a wall switch |
| 8 | the cargo corridor door | same since this round (`action: toggle` as the original's) |
| 40 | the control room door's panel | differs: the original also binds it to the hold door's faces |
| 56 | the east landing's floor | differs: not on the ramps' lower parts (one floor runs one event) |
| 460, 464, 468, 472 | one event on the east corridor's floor sends all eight beds back | differs (refused plate, round four) |
| 501 | the exit asks the party for a wetsuit | differs: the original asks every member |
| 476, 477 | the Sparks timers | same |
| all the rest (doors, step floors 15 to 56, lockers, cranes, pods, pads, stasis 459 to 471, chests 176 to 179) | as round four | same |

### Playtest

**Passes four runs of four** (`play_r5_final1.log` to `final4.log`; 185 steps, was 157). An earlier batch of four (`play_r5_run1` to `run4`) failed once: a spawned Sentinel Droid stood between the party and the locker's rifle and took the use key; the two pick-ups now kill the party's enemies near it first (`clear_hostiles(1500)`), as a player would. New in it: the 17 droids
counted by kind (all peaceful) and three at their own places; lights 1 and 2 dark after entering, light 1 on after
the power panel, light 1 off and 2 on after the console; chest 1 looted on pod bay 2's raised lower deck and chest 2,
each after making room (the walk drops every pack item but the quest items first) and each checked for its Blaster
Rifles; the Blaster Rifle behind locker 3's shutter and a Blaster on the station floor picked up; the slope ending in
the original's 32 step down to the viewport and back; the lower east lift taken as the original's is (it starts down
and nothing calls it from the landing: the party drops onto it), its panel at the lower stop raises it and shuts the
corridor's door, its upper panel sends it down; the upper east lift's lower panel raises it and opens the top door,
its upper panel sends it back down and shuts the door; the lower corridor walked as a tunnel.

### What changed

1. **One roof over the bridge, slope, viewport and window** (sector 38: 87.8 to 95.7 %). The slope (`view_steps`),
   the viewport and the window take `ceiling_points` from the original's ceiling faces 1802 and 1892 to 1906, 1966,
   1967, 2180: the flat top at 2048, the hips down to 1804 at the bridge's corners and to 1932 at the canopy's front,
   the side glass down to 1420. Heights at the rebuild's own wall corners are the original's planes there. The three
   mouths (`deck_steps`, `steps_viewport`, `viewport_window`) are `height: full` and now follow both rooms' roofs
   point by point: the bridge-to-slope portal reaches 2048 (was 1804), the slope-to-viewport one 2048, the window's
   1932; no wall hangs at a joint. The window's `ceiling_slope` became `ceiling_points` (its side glass reaches 1420 at
   2944/5760 as the original's). The side glass that reaches over the viewport (faces 1905/1906 north of y -11200) is
   lightmap by `ceiling_surfaces`. Rooms that took the original's points one for one: view_steps (10 points),
   viewport (14), window (8), all of them corners where the roof changes slope.
2. **The slope's floor outline is the original's trapezoid** (2432..6272 at the bridge, 2656..6048 at the foot): the
   original's slope region is as wide as the bridge and narrows along its two diagonal side stairs. Its floor is the
   original's plane (1548 to 1324, faces 2119/2120 and the stair fronts), ending 32 above the viewport (riser faces 1715,
   2117). The side stairs themselves (sheared treads 64 deep) and the middle console are not built.
3. **The dome's own texture**: `ceiling_surfaces` on the bridge's roof: the upright ring a1b and the dome a3bs, as the
   original's sector 39 (sector 37's textures 92.4 to 96.6 %).
4. **The lower corridor's main way as a tunnel** (`room:corr_low`: path x 3088, y -1024 to -3840, the original's
   eight-sided section with lower a3b, wall a1b, upper sfw3): the two branches open in its sides by side doorways in
   one stretch (-1360..-2144), the hold's door in a square start 254 wide (the original's leaves at x 2961..3215),
   a square end of 16 into the south part. The hangar branch, the reactor branch and the diagonal south part stay plain
   rooms (`corr_low_hb`, `corr_low_rb`, `corr_low_s`); see "what stops it". The main way's points score 1.00 on
   distances; the junction stretch loses textures where the tool's side doorways stand upright (a1b) and the
   original's bevels cut into each other.
5. **Invisible solids**: the reactor's two drums (`visible: false` slabs 8 thick standing on the console rings: eight
   on the upper deck from 1580 to 1996, faces 1507 to 1514; seven on the lower deck from 1132, the diagonals from
   1068, to 1420, faces 1500 to 1506, none on the south side where the power console is) and the spines' eight energy
   fields (HIVE1 slabs 8 thick, 1868 to 2124, faces 1349/1350 ... 2318/2319). The fields in the ends stand where the
   original's do; those of the six alcoves stand in the alcove rooms against their mouths, 8 further in than the
   original's (which fill the 8-thick wall between spine and alcove). The alcoves are now shut as in the original.
6. **The east lifts' call events** (34, 154, 155, 156) as panels at the original's places (one on the top landing's
   side facing the shaft by `block`/`side`), the lifts no longer clicked.
7. Contents, lights and chests as above; warnings: `open:corr_stairs_a`, `deck_captain`, `landing_lift_e2` and
   `locker1` pinned with `from_wall`/`to_wall` (each the pair the build had taken, checked against the original);
   `project.yml` `migrated: [platform_in_sunken_level]` (the hold's machines stand from 96 to 288, right).

Scripted (each diff checked; numbers from the scene file and the export): `r5/contents.py` (monsters, items, chest 1,
chest contents), `r5/lights.py` and `r5/lights_drop.py` (the 82 disabled lights), `r5/drums.py` and
`r5/drums_apply.py` (drums and fields), `r5/roof.py` (the roof's points; the glass region and the trapezoid by hand
after it). The tunnel was tried in `r5/tunnel_trial/` and taken over whole; the rest by hand.

### New words: worked and refused

- Worked as described: `monsters` (row number, `floor_height`, `group`, `hostile: false`), `items`, `chests[].rides`
  on a mover, `trap_level`, `lights_on`/`lights_off` with `trigger: load`, `on: false` (and its warning), a `lua`
  effect on a load event, platforms with `visible: false` (with `base`, outlines touching, standing over sloping
  blocks), switches with `block`/`side` on a platform with an `id`, `ceiling_points` on rooms joined by `height: full`
  mouths (the portal follows both roofs exactly), `ceiling_surfaces` by `at` (four dome bands, two glass regions),
  `from_wall`/`to_wall` to answer the warning, `migrated`.
- A tunnel's two side doorways on opposite sides of one stretch, overlapping along the way, validate and build
  (round four thought this was refused).
- Not used: `kills` (no monster's death runs anything here), `doors[].secret`, ladders, sounds, `solid: false`,
  `thickness` on sloping slabs, `floor_surfaces`, `trim_to_wall`, `movers[].parts`.

### What stops the lower corridor's branches and diagonal (sector 19), exactly

- The reactor branch as a tunnel (`r5/tunnel_trial2`): its east end must be a square end narrower than the section
  (the shaft room is 288 wide) and "the square end of the tunnel room:corr_low_rb is all doorway: it is 224 wide and
  stands from 224 to 480, and the opening must be exactly that ... Here the opening reaches from 0 to 224 along the end
  and from 228 to 480 in height". The shaft's floor is the lift's top (228, 4 above the corridor) because a lift is a
  block from its room's floor; the original's mouth is the full section into a sector that holds the lift. Field: a
  square end whose doorway may be lower than the room behind it rises (a sill), or a lift 4 high on a lower floor.
- The hangar branch and the diagonal to the stairs are sheared (cut on x planes, 384 measured along x, 329 across the
  way); a path's section stands square to the way and its ends square too. Field: `shear` or an end cut on a given
  plane.
- Where a branch meets the main way the original's two sections cut into each other (bevel triangles, faces
  3817 to 3819); a side doorway is an upright wall with the doorway in it. Field: a tunnel joined into another's side.
- `section` square ends: `end: {}` without `length` tapers the section over the whole last stretch (1,700 long here:
  faces from the section at -2144 to the rectangle at -3840); the schema does not say so (tool defect 3).

### Compromises

- Undone: the bridge-to-slope wall (the mouth now reaches the roof), the flat slope and viewport ceilings, the
  slope's rectangle, the dome's sfw7a, the lower corridor's main way as a plain room, the console ring standing in for
  the drum (the drum is there now, the ring stays, as in the original), the lifts clicked instead of their panels.
- **Kept, waiting for the tool:** the trench banks in the lower hold are 144 wide where the original's are 96: a bank
  that steep (96 out, 128 up) is built as walls and its stand points lose their floor; 144 keeps the walkable slope's
  height within 7 of the original's. Not changed this round.

### Gaps still open, most harmful first

1. **Leaning walls** (the slope's and viewport's sides lean in from 1420 to 1932, faces 1898 to 1906, 3975, 3977):
   upright walls here, the roof's points at the walls extended from its planes. The viewport's worst points
   ("open 125 farther east") are these. Field: a wall that leans (`walls[].lean` or a top outline).
2. **Texture offsets** (the original's `texture_delta_v` sets each band's phase: 224, 384, 480 in the lower corridor):
   most of what sector 19 still loses (textures 84.5 %). Field: `offset` or `align: top` on a surface.
3. **A monster that starts invisible**: said by a Lua line on load. Field: `visible: false` on a monster.
4. **Item spawn points** (20, random item of level 5): placeholders. Field: `items[]` with `random: level`, or item
   spawns in `spawns`.
5. **Things in the floor hole** (the reactor column and core through the hole, refusal 2 of round four), the spiral
   steps, the pilot pits' and slope's consoles, the slope's side stairs (sheared treads), folding leaves, the cranes'
   frames, switches not on a wall (the power console, the star console, the west lift's deck console, the cargo
   shaft's panel): as before.
6. The lower corridor's branches and diagonal (above).
7. One event per floor (the stasis "beds back" strips, event 56 on the ramps).

### Tool defects (this round)

1. **A 32 step at a slope's foot blocks `probe`, `audit --reach` and `solve` both ways**, though the game walks it:
   `oymap probe output/studio_cal/mm7_7d23/repro/step_off_slope --assets assets_dev --from 256,-256,0 --to 256,300,182`
   "blocked by a face" (and back); the same step without the slope (`repro/step_off_slope_flat`) and the slope without
   the step pass. Round one's "32-unit step down out of a ramp is refused" still stands; here it leaves the viewport and
   window "never reached".
2. `oymap compare` from a pilot pit (eye at exactly the viewport's floor height, 1292) sends rays through the joint
   between the viewport's floor and the slope's riser once the joint carries extra points ("the rebuild has nothing
   within 4096 to the north-west", `compare_r5_a`, points (3328, -11008) and (5376, -11008)); gone again once the
   riser stood 32 high. A ray exactly in a floor's plane should not decide a point.
3. `section: {end: {}}` (a square end without `length`) tapers the tunnel over its whole last stretch; nothing warns
   and the schema does not say what the default length is.
4. A light switched by `evt.SetLight` is asserted in a playtest by its index in the built map (`light: {key: 1}`), not
   by its number in ids.lock.yml (83); `light: {key: 83}` reports "unset". The lock's numbers for the 82 dropped lights
   stay in ids.lock.yml.
5. Still standing: the "wall without thickness" warnings for openings whose two rooms' walls lie in one plane
   (`hangar_bay1` to 4, `lobby_trench`, `corr_stairs_a`) ask to move rooms 16 apart, which would move the original's
   walls (its portals have no thickness); and "rises to within 200 of the ceiling" for the four upper pod decks, as the
   original's do. Neither can be answered without a wrong shape.

### Where score and the original pulled apart

- The slope ending 32 above the viewport (the original's riser) makes `solve` and `reach` lose the viewport and the
  window (tool defect 1); kept, since the game walks it and the original has the step.
- The alcoves and spine ends behind the energy fields are now unreached by `reach` and `solve`: true to the original.
- The tunnel's junction stretch scores lower in textures than the plain room did; kept, the main way's section is the
  original's and the stretch is what the tool's side doorways make.
- The compare points in the pilot pits (defect 2) dropped and came back without a change aimed at them.
