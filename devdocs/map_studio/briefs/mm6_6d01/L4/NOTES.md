# Goblinwatch (MM6 `6d01.blv`) rebuilt as a Map Studio project: notes

Rebuild by [REBUILD_PROCEDURE.md](../../../REBUILD_PROCEDURE.md), 2026-11-13, one session from nothing to L4. A
held-out map: the studio was never tuned on it. Project id `cal6d01`, map row 9701 (`reference: 6d01.blv`). Scratch
data, pictures and helpers are in `output/studio_cal/mm6_6d01/`: `orig/` (the original's audit, solve, flow, things,
metrics, export and renders), `tools/` (`sect.py`, `faces.py`, `rep.py` from the Fortress's round, `cave.py`,
`replace_caves.py`), `t1/` (the first shell's fragments), `r1/` (the playtest runner `play.sh`, `play4.sh`, its logs,
`shots.yml`), `compare_r1a` to `compare_r1f` (each measure), `things_rebuild/`, `things_orig/`, `ingame/` (pictures),
`repro/` (refused features).

## Where it stands

| Stage | `oymap compare` score | shape (distances) | textures |
|---|---|---|---|
| caves only, generated from the original's faces (`t1/cmp`) | (caves 94 to 99.7 % each) | | |
| whole shell, no objects (`compare_r1a`) | 96.7 % | 97.3 % | 96.3 % |
| a cave mouth's floor fixed (`compare_r1b`) | 96.9 % | 97.4 % | 96.4 % |
| doors, movers (towers, six gates), switches, chests, spawns, lights, decorations, the fountain (`compare_r1c`) | 98.1 % | 98.6 % | 97.6 % |
| T-junction points' lines kept, bank rims lowered in pairs (`compare_r1d`) | 99.0 % | 99.2 % | 98.7 % |
| textures of the hidden rooms, quarters' doorways, the hall's trim strips (`compare_r1e`) | 99.1 % | 99.2 % | 99.2 % |
| tower interiors' panels; **end** (`compare_final`) | **99.2 %** | **99.2 %** | **99.3 %** |

- `compare.py` (against `orig/metrics.json`): `13 in, 13 near, 9 out`. Out: sector floor area minimum, first quarter
  and median (the flights, mouths and lockers are rooms of their own here: 83 rooms for the original's 58 sectors with
  a floor), sector height minimum (the original's 10-high switch-picture sector 58, not built), doorway counts, widths
  and heights (the original's closed doors have portals 1 wide; here every cave mouth and the shaft's landing count),
  unreached spawn points (2: the raised niches of the west cave's end room, 64 over its floor, as the original's).
- Rooms 83. `oymap audit --strict`: faces in one plane **0 pairs, 0 as the original, 0 new** (the original has 1: faces
  892 and 1684 of sector 36, T3C2 and T3T6 under the passage's ceiling). `oymap validate`: no issues.
- `oymap solve`: 2 sectors at the start (the landing and the hall), 40 after door 1, 60, 63 after the switches open
  the gates, 65 of 83; not reached on foot: the gatehouse top (288, as the original's), the two raised niches (64) and
  the lockers (64 over the corridor, as the original's: "12 lower than the party is tall").
- **The playtest passes four runs of four** (`r1/play_1.log` to `_4.log`; 141 steps).

## How it was made (scripted parts)

- `gen/gen_caves.py` wrote the eighteen caves (sectors 27 to 35, 37 to 44) once from the export: each cave is one room,
  its outline the plan boundary of its floor faces (points on a straight stretch become points on that wall), its
  floor and roof **the original's own vertices one for one** (`floor_points`, `ceiling_points`, 8 to 48 floor points
  and 12 to 46 roof points a room: above the procedure's 25 and 40 in rooms s27, s28, s29, s31, s35, s38 and s44),
  the creases between faces of different planes as `floor_lines`/`ceiling_lines`, banks textured by
  `steeper_than: 0.1`. Where the original does what the studio does not build, it does the nearest thing and says so
  on stderr (the list is in the script's head): cracks in a floor's edge are left out; points within 26 of another
  merged; points on the straight line between two others (T-junctions) left out, a floor's line kept; the roof kept
  16 over the floor at the rim (the original's banks meet the roof with no wall); floor triangles steeper than 2 up
  for 1 across have their rim corners lowered (by 2 to 185, most 40 to 120: an upright wall under the roof instead of
  a bank steeper than 63 degrees) and roof triangles steeper than 4 their low corner raised; four heights and five
  slivers set by hand (`FIX_FLOOR`, `DROP`, `EXTRA_ROOF_LINES`). Heights are adjusted on one table for all caves, so
  two caves keep one mouth. It also cuts the shaft's landing out of cave 44 (below).
- The keep's rooms (sectors 1 to 26, 36, 45 to 57) were written by hand from `tools/faces.py` readings (in
  `t1/keep_*.yml` first, then in rooms.yml).
- `gen/gen_objects.py` wrote objects.yml once: doors, movers, switches and chests as tables from the door records and
  faces; the 66 spawn points, 158 of 159 lights and 176 of 177 decorations record by record (the room by outline and
  height, the height over the original's floor under it). `gen/gen_wiring.py` wrote wiring.yml once, one event per
  handler of `oymap flow 6d01.blv`. The files are now the source; no generator is run again (the caves were
  regenerated twice in this round by `tools/replace_caves.py`, which keeps a room's hand-added platforms, walls and
  ambient).

## Contents

- **Spawn points: 66 of 66** at the original's places (47 monster spawns, slots 1 to 3 and four with a fixed tier;
  15 item spawns by treasure level). Two stand in the raised side niches of the west end room (64 up), as the
  original's.
- **Chests: 10 of 10 records with contents.** Records 3, 5, 6 to 9, 10 are boxes of `kind: ch1` (5 to 9 with MM6's
  carved lids, `lid: v`), at the original's places; record 3 on the west hidden room's plinth at 32. Records 1, 2 and
  4 have no box in the original (chest type 7): the picture ch2frnt on a locker's back wall opens them; here a wall
  panel with an id runs `open_chest`, and the records are `box_of: chest:c10` (the studio's box-less chest needs a
  box to name; it is never shown). Trapped (trap level 1, the row's Trap column) where the record's flags say so:
  all but record 10.
- **Decorations: 176 of 177** (85 `6torch01`, 70 of 71 `TrchB00`, 21 campfires `dec04`). Not placed: the `TrchB00`
  at (1180, 4120, 120), inside the switch hall's south wall in the original (no room holds it), with its light.
- **Lights: 158 of 159**, radius and brightness as the records'. Ambient 19, the caves 28 to 34, 39 to 43 and the
  shaft 16, as the sectors'.
- **Placed monsters and lying items: 0 of 0** (the scene has none).

## Behaviour: the original's events and the rebuild's

| Original | Rebuild | Same? |
|---|---|---|
| 1 to 18, 61 (doors) | `evt:d1` ... `evt:d23`, `action: open` | same |
| 60 (the double door, records 45/46, corridor side) and 38 (its cave side, no handler) | `evt:d60` with `side: room:s51`; nothing on the cave side | same |
| 62 (the dais switch: the button record 31 and the towers record 32) | `evt:dais`, a `kind: button` and `mover:towers` | same |
| 63 (no title: both towers' back walls rise, record 30) | `evt:d30w`, `evt:d30e`, each opening both leaves | differs: the hover name says "Door" (a door's event takes the default title; `title: ""` is ignored) |
| 19 A (fireball trap) | `evt:a`, Lua `evt.CastSpell` (the `cast` effect aims at a point, the original at the party) | same |
| 20 to 30, 32, 33 (B to L, N, O: once until P, gates by records) | `evt:b` ... `evt:o`: `condition: not map_var`, `sets`, `opens`/`closes` of the gates' movers | same |
| 31 M (teleport into the east caves) | `evt:m`, effect `teleport` | same |
| 34 P (reset) | `evt:p`: `closes` every gate, Lua sets the 13 variables to 0 and the 13 pictures back by their cogs | same; the pictures by Lua |
| 66 (on load: the pictures of used switches) | `evt:plates_load`, Lua | same, including the original's slip (E's picture follows D's variable) |
| 41 to 50 (chests) | `evt:c1` ... `evt:c10` | same; 41, 42, 44 on wall panels |
| 47 (chest 7 and, the first time, a starburst and three goblins B) | `evt:c7`, the once-part in Lua | same |
| 51 (exit) | `evt:exit` | same |
| 55 (no title: armour of level 4 once from a spot of the sewer's wall) | `evt:armour`, Lua give | same |
| 64 (no title: Wizard Eye once until the daily reset; on the fountain's rims, spout and fire, 22 faces) | `evt:fountain` on the spout alone | differs: one source |
| 65 (daily at midnight: the fountain ready again) | `evt:fountain_reset`, `trigger: timer, every: 2880` | differs: a day from entry, not at midnight |
| 54, 57, 58 (bound to floor faces of cave 31 and to chests' sides; no handlers) | not bound | same (nothing happens either way) |
| 65000, 65001 (global) | the same global events | same |

Of the original's 53 map handlers (and 4 bindings without one), **50 do the same thing under the same condition**
(eight of them with a Lua step); **3 differ**: 63's hover name, 64's single source, 65's hour.

## Playtest (`playtest.yml`, 141 steps, four runs of four pass)

From the landing down the steps, door 1, the cross passage, door 23, the goblins' hall; up the dais, the switch
(towers asserted shut before and sunk after); the west tower's back wall (both rise, asserted), the west hidden room
and its chest (item 1823 asserted), the east hidden room; door 17 to the switch hall; at the console A (the trap), D
(gate 1's band open, variable 4 asserted), P (band shut again, variable 0 asserted), then N H F B O G and all 14
gate bands asserted open, N used again moves nothing (variable 14 asserted); up the ramp and through the six gates,
the double door, the fountain (variable asserted); down the shaft (the fall to -768 asserted), the vault's ramp and
its four chests (item 220 asserted, the ambush's variable asserted), up the north ramp to the sewer passage, the
armour spot (variable asserted, a second click gives nothing), west to door 18 opened from the sewer's side; up to
door 16 opened from the east passage's side, the hall's west arm, door 2, the two ramps, door 3; the prison's twelve
locker doors asserted shut and opened, the three painted chests (item 2163 asserted); back up and through the switch
hall, M (the party asserted at (9000, 1916, -767)); the east caves to the far niche's chest; back through all the
east caves, the lower keep's cave passage, the west caves to the far end, up its stair to the niche's chest; back to
the lower keep, the back stair, the east passage, the hall, up the steps and out by the exit door to New Sorpigal
(`oute3.odm` and the arrival at (-18400, -14982) asserted).
Not by chance: every walk clears hostiles within 2,500, the party is immortal, and the packs are emptied before every
looting, so no chest fails for room.

## Pictures

- Same-camera pairs, 38 (`output/studio_cal/mm6_6d01/ingame/diff`, shots `r1/shots.yml`): edge agreement 0.91, blurred
  difference 0.019. They include the view round from every raised top the party stands on: the landing (192), the
  dais (120), the gallery (128) and the fountain's top tier (320); none looks into another room or goes black. Least
  alike: `west-cave-27` (the rims lowered for steepness, T-junction roof points left out), `quarter-table`,
  `fountain-cave-north`, `top-fountain-west` (the spout's flat top for the original's fire hollow). Most alike: the
  gates corridor, the goblins' hall, the vault.
- Interactive things: `things_rebuild/` (52 things, before, used, used again; contact.png) beside `things_orig/` (the
  original's, before). Doors (16 hall-and-keep doors, 12 lockers, the double door, the towers' backs): the
  original's leaves and pictures, folding as the records move. The dais's switch: a T3T5 block 64 square pushed
  into the wall. The towers sink whole. The console: sixteen T1swDd plates, turning T1swDu once used (A and M stay),
  on the console's raking top (since the user's walk, 2026-11-13; before, on its upright west face). Chests: MM6 ch1 boxes (carved lids where the original's are), the lockers' three
  painted chests as the picture on the back wall. The fountain: three stepped basins of orWtr32 and SWhorzA rims.
  Many pictures are half hidden by goblins (the tool does not hide monsters).

## Gaps, most harmful first

1. **A floor hole in a cave** (the shaft from cave 44 to sector 46): `in: floor` needs a level upper room, refused
   in a room with `floor_points` (`repro/hole_in_uneven_floor`). Done: a landing room `s44h` cut out of the cave round
   the shaft's mouth (level at 128 there, as the original's), joined by nine mouths; the hole 16 inside the shaft's
   walls. Field: a hole in a level part of an uneven floor.
2. **Banks steeper than 2 for 1 and rims with no wall** (every cave): the original's banks meet its roof at a rim of
   no height, some rising 3 to 16 for 1 across; the studio keeps the roof 16 over the floor and refuses floor
   steeper than 2. Done: rims lowered (2 to 185) into short upright walls, roofs raised 16 at the rim. Field:
   `steep_floor` up to near-vertical for banks nobody walks, and a rim of zero height.
3. ~~**Switches on a raking top**~~ (the console's sixteen): built since 2026-11-13 (the user's walk): `side: top` on a
   platform with `top_slope`; the console is one block (upright from 16, top 96 to 160 at 45 degrees) with the sixteen
   T1swDd plates on its top, 16 by 16 on the plan, as the original's faces 1998 to 2013.
4. **A door in a wall as wide as the door, into an uneven room** (the double door, 512 wide, into cave 44): `width:
   full` makes a mouth that takes no door, a number needs 16 each side (`repro/door_in_cave_wall`). Done: 480 wide.
5. **Cave points one for one** beyond the procedure's budgets (s27, s28, s29, s31, s35, s38, s44: up to 48 floor and
   46 roof points); T-junction roof points left out lower the roof of caves 28 and 29 by up to 184 in places.
6. **One source per event** (the fountain's 22 faces): the spout alone runs it. Field: `sources` for clicked events.
7. **No title for a door's event** (event 63, the towers' secret backs show "Door"): `title: ""` is ignored.
8. **A timer at an hour of the day indoors** (event 65, midnight): every 2880 half minutes from entry instead.
9. **A box-less chest** (records 1, 2, 4, a picture on a wall): `box_of` must name a real chest (c10, never shown).
10. Smaller: one picture for both leaves of a double door (T3D2A/B halves); the spout's fire hollow (an inverted
    pyramid) as a flat top; the towers' closet floors T3F2 (a plate needs 16 from walls); the west cave's stair as 13
    even steps (12 of 48 and one at the sill in the original); the console's raking top's pictures.

## Tool defects

1. Validation error "two openings in one wall of room:s7 overlap" did not name the openings; the cause was
   `open:s6_s7` taking another wall pair (the longest shared stretch, 256 apart) silently. Wanted: the openings' ids,
   and a warning when the pair taken is not the nearest.
2. Openings without `from_wall` take the longest shared stretch even across 128 of rock while a 16-thick pair exists
   (s4_s52, s4_s53, s54_s55: built a doorway through the wrong walls with only a warning).
3. `things_shots.py` leaves monsters in its pictures (most console and chest pictures are half goblin); `ingame_compare`
   switches them off only outdoors.
4. Scenario `mapvar()` in `play_lua` reads named variables only; numbered map variables need
   `assert: {state_dump_map_var}` between Lua steps (cost a run to find).
5. `title: ""` on a door event is accepted and ignored (default "Door").

## What I was unsure of in the original

- The steep rim triangles of the caves (bank faces rising 3 to 16 for 1 across): read as the original's way of
  meeting the roof, not as walls; here they are walls under the rim.
- The console's sixteen switches lie on its raking top in the original (45 degrees), and so here since 2026-11-13
  (rows from the high east side A-D, E-H, I-L, M-P; columns north to south).
- Door record 46/45's leaves have T3D2B/T3D2A halves; which half shows on which leaf from the cave side was not
  checked in the game.
- Chest type 7 (records 1, 2, 4) is read as a box-less chest picture on a wall (the scene holds the contents, the
  faces are ch2frnt on the lockers' back walls).

## The user's walk (2026-11-13)

"Otherwise everything good", with two faults, both fixed (code batch in `output/studio_obj8/fix/`, backup of this
project before the change in `output/studio_cal/mm6_6d01/gw2_backup/`):

- The console's switches stood on its upright face. Now on its raking top (`side: top`, `at` on the plan): rooms.yml's
  two console platforms became one with `top_slope`, objects.yml's sixteen switches `side: top` at x 2200/2184/2168/2152
  (rows A-D to M-P) and y 4888/4872/4856/4840 (columns north to south). Playtest four of four; score unchanged (99.2 %).
- A light line round the lockers' red doors: the leaves stand 2 back from the wall's faces (no flicker when they rise
  into the wall), and the 2 of reveal before them showed the theme's T1trimA. The studio now lays that strip with the
  leaf's own picture (for every map); no project change.
