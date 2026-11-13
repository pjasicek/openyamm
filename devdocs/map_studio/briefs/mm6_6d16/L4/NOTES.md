# Warlord's Fortress (MM6 `6d16.blv`) rebuilt as a Map Studio project: notes

Rebuild by [REBUILD_PROCEDURE.md](../../../REBUILD_PROCEDURE.md) and [ROUND_FIVE.md](../../../rounds/ROUND_FIVE.md),
2026-11-13, one session from the designer's hand-drawn L3 shell to a playable L4. Project id `cal6d16`, map row 9708
(`reference: 6d16.blv`). Scratch data, pictures and every helper are in `output/studio_cal/mm6_6d16/`: `orig/` (the
original's audit, solve, flow, metrics, export and renders), `tools/` (`sect.py`, `faces.py`: the original's sectors
and faces read from the export; `rep.py`: loss by sector from a compare), `r1/` (the helpers below, the playtest
runner `play.sh`, its logs, the rebuild's flow and solve), `compare_*` (each measure), `ingame_final/` (pictures).

## Where it stands

| Stage | `oymap compare` score | shape (distances) | textures |
|---|---|---|---|
| L3 as drawn (its own frame: origin at the fortress's south-west corner) | 0.5 % | 28.6 % | 0 % |
| L3 moved into the original's frame (-4992, -3456), nothing else (`compare_shift`) | 85.4 % | 94.8 % | 64.1 % |
| rooms redrawn from the original's sectors (`compare_r1a`) | 88.3 % | 93.4 % | 77.1 % |
| openings pinned to their walls (`from_wall`/`to_wall`, `along`) (`compare_r1b`) | 91.6 % | 96.8 % | 79.6 % |
| doors, chests and furniture, wall strips as panels (`compare_r1c`) | 99.2 % | 99.9 % | 97.4 % |
| bunks and beds with posts and bevels, the tunnel's chamfers in rock (`compare_r1e`) | 99.6 % | 99.9 % | 99.0 % |
| **end**: full-height panels on the flights' raking walls (`compare_final`) | **99.7 %** | **99.9 %** | **99.2 %** |

- With `--step 200` (689 points off the original's grid): 99.7 % (distances 99.8 %, textures 99.3 %).
- `compare.py`: `24 in, 6 near, 5 out`. Out: the smallest sector floor and height (the original's sector 39, a 42 by 42
  floor 10 high holding the switch's `D8s2on` picture, unreachable, not built), the first quarter of sector floor
  areas (the flights and passages are rooms of their own here), doorway width minimum and first quarter (the original's
  closed doors have portals 2 wide).
- Rooms 49 (the original's 39 sectors; flights, landings and three passages are rooms of their own, the two entry
  tunnels and the junction's vaulted strip are one tunnel room, sector 39 is not built). `oymap audit --reach`: 49 of
  49. `oymap validate`: no issues. Build warnings: the 75 lights that start dark (below), nothing else.
- **The playtest passes four runs of four** (`r1/final_play_1.log` to `_4.log`; 114 steps).
- In-game pairs (`output/studio_cal/mm6_6d16/ingame_final/diff`, 20 pairs, shots `r1/shots.yml`): edge agreement 0.89,
  blurred difference 0.022.

## How it was made (scripted parts)

- `r1/translate.py` moved the L3 shell into the original's frame once. The rooms were then written again by hand,
  sector by sector, from `tools/faces.py` readings of the export: each room is a sector or a part of one (named in its
  notes), outlines on the original's corners (its 45-degree joins kept as diagonals), every flight 16 per 256 with a
  ceiling that rakes with it, the coves of the great hall, storeroom, drill hall and throne room as whole-ceiling
  levels with `top_outline`, the antechamber's L-shaped cove by `ceiling_points` and `ceiling_lines`.
- `r1/gen_objects.py` wrote objects.yml from the original's records: 19 doors (a table read from the export's door
  records: direction, travel, faces), 20 chest records with their boxes (face extents), 52 spawn points, 75 lights,
  129 decorations (room by point-in-outline, heights from the records). `r1/gen_wiring.py` wrote wiring.yml, one event
  per handler of `oymap flow 6d16.blv` / `6d16.lua`.
- `r1/add_furniture.py` (one edit over ten rooms) put the original's built-in furniture as platforms: 11 bunks
  (lower bed with a bevel, four CBEAM5 posts, upper board and mattress), the warlord's four-poster and the throne
  room's canopied seat, the officer's bed, the treasury's L-shaped shelf (two slabs 96 to 112 on the original's
  45-degree corner), the two chests of drawers, the eight other boxes of the shared footlocker and the two other
  cabinets of the shared cabinet (platforms with ids).
- `r1/add_panels.py` (one edit over 187 walls) wrote 446 wall panels: for every wall, the original's wall faces in
  its plane facing into the room, each run of a texture other than the room's wall surface as a panel at the face's
  own place (the D1wlbre1/D1wlble1, D8wlBRE/BLE, D8wlDRE/DLE strips at both ends of every wall and beside every
  doorway, d1trimRE/LE, d1wreA/leA, the flights' D1wlele/D1wlere and d1wlDLE3, skull plaques, the false doors). Whole
  height where the face is; on the flights' raking walls always whole height (a first run gave level panels there).
  Every diff was read. The files are now the source; no helper is run again.

## Contents

- **Placed monsters and lying items: 0 of 0.** The original's scene has `actors: []` and `sprite_objects: []`; all
  its soldiers come from spawn points. Both maps spawn 43 actors on entry (`indoor actors: total=43` in a headless
  run of each).
- **Spawn points: 52 of 52**, at the original's places: 43 monster spawns (index 1 to 3 as slots, 4 to 12 as a slot
  with a fixed tier: `slot`, `tier`), 9 item spawns (`kind: item`, `treasure_level` = the record's index). Spawn 50
  (on the treasury shelf's 45-degree corner, exactly on the line where the rebuild's two shelf slabs meet) moved 4
  west onto the west slab.
- **Chests: 20 of 20 records, 30 of 30 boxes.** Records 2 to 9 and 12 to 19: three rolls of levels 5, 4 and 3
  (`random_levels`), as the scene holds them. Record 10 (the bedchamber's cabinet): Banded Plate 95 and Tower Shield
  1682. Record 11 (the vault): item 2128, as the scene holds it (see unsure). Records 0 and 1 (the shared footlocker
  and the shared cabinet, empty): one box each, and their other boxes (8 and 2) are platforms with ids whose events
  `open_chest` them. Trapped (`trap_level: 6`, the map row's Trap column) where the record's flags say so: 0, 1, 10,
  11, 19. Boxes measured: 96 by 64 by 64 chests (64 wide where the original has no end strips), cabinets cb2, cb3,
  cb6 at their sizes, front, end and lid textures.
- **Decorations: 129 of 129** (42 TrchB00, 23 6torch01, 10 flamb00, 26 barrels, 28 sacks), at the records' places.
- **Lights: 75 of 75**, all `on: false`. Every light record of the original holds attributes 8, which this engine
  reads as switched off (`BlvLightDisabledAttribute`), and no event switches one on: the original is lit only by its
  ambient (22 in every sector: `defaults.ambient: 22` here) and its torches' and flambeaux' own light. With the
  lights on, the rebuild's pictures were visibly brighter, with light pools round the flambeaux the original does
  not have (great hall pair: blurred difference 0.081 lit, 0.003 dark). The build warns once for each ("starts dark
  and no event lights it ... or drop the light"); they are kept as the original's records, not dropped.

## Behaviour: the original's events and the rebuild's

| Original | Rebuild | Same? |
|---|---|---|
| 1 (secret wall, tunnel end) | `evt:d1`, door 1, `slide_up` with `fold`, `secret` | same |
| 2, 3, 5, 8, 12-16, 18 (doors) | `evt:d2` ... `evt:d18`, `action: open`, leaves that fold toward the jamb the record moves them to | same |
| 4 (sinking wall of the treasury) | `evt:d4`, `slide_down`, `secret` | same |
| 10 (east barracks door, bound to its gallery face only) | `evt:d10` with `side: room:u1` | same |
| 11, 17 (rising closet walls) | `evt:d11`, `evt:d17`, `slide_up`, `secret` | same |
| 6, 7 (storeroom doors, double locked) | `evt:d6`, `evt:d7`: `all` of both keys, `locked_text`; the first door opened sets a variable to 10, the second spends both keys | same; the spending on the second door only is a Lua step |
| 9 (vault door) | `evt:d9`: the Warlord's Key, "The door is locked.", key taken | same |
| 19 (switch) | `evt:switch`: door 19 opens, plate `D8s2on`, variable set | same |
| 48 (on load: the switch's plate) | `evt:switch_load` (`trigger: load`, `texture`) | same |
| 20-24 (false doors: one of four landings at random, never this door's own) | `evt:false_door_20` ... `_24` on the door panels (wall panels with ids) | differs: the random pick is Lua; **the same events' other bindings are missing** (ten faces: the descending tunnel's wall 1514, the gate tunnel's wall 1628, the tunnel end's floor 1507 and 2577, the gate tunnel's floor 1619 and roof 1595 and 1607, the junction tunnel's roof 1543, the tunnel end's roof 1498 and 2613) |
| 25 (shared footlocker, nine boxes) | `evt:footlocker` + eight `evt:locker_*` | same |
| 26 (shared cabinet, three boxes) | `evt:cabinet_shared` + `evt:cabinet_u5`, `evt:cabinet_u15` | same |
| 27-35, 37-44 (chests, cabinets) | `evt:c2` ... `evt:c19` | same |
| 36 (statuette chest) | `evt:statuette`: chest 11 with qbits 1076, 1211 and a variable for a party without 1076 (and again once noted here), else the shared footlocker | same |
| 45, 46 (chests of drawers, keys, once) | `evt:drawers_study`, `evt:drawers_throne` | same |
| 47 (lure door) | `evt:lure` on a wall panel | same |
| 50 (exit) | `evt:exit` on the gate's D2LgDor | same |
| 51 (hidden axe, the flambeau's secondary event) | `evt:axe`, a decoration as source, once | same; `GiveItem(6, 25)` is a Lua step |
| 65000, 65001 (Nicolai, global) | the same global events | same |

Of the original's 50 map handlers (1 to 48, 50, 51; 49 of them bound to faces or a decoration, 48 run on load),
**45 do the same thing under the same condition** (three of them with a Lua step for the part no word says: the two
double locks' spending, the axe's give); **5 differ**:
the false doors 20 to 24, whose second bindings on the tunnels' walls, floors and roofs cannot be said.

`oymap solve`, step by step (rebuild against original): 4 / 4 sectors at the start; +5 / +5 by the secret wall;
+18 / +10 by door 2 (the flights and passages are rooms of their own here); +18 / +14 by the plain doors of the
barracks, the hall and the wings; +4 / +5 by the secret walls, the vault key and the switch. The order is the
original's except that the two double-locked storeroom doors fall into the third step here (with "needs [2185]
[2191]") and into the fourth in the original's solve, which takes them with the keys there; the walk opens them
last in both.

## Playtest (`playtest.yml`, 114 steps, four runs of four pass)

From the gate hall down the gate tunnel, the junction and the descending tunnel to its end; the lure door's line; the
secret wall; the hub and one of its false doors (asserted: the status line, and the party in the cellar, any of the
four landings: the assertion does not depend on which); the cellar hall's door into the storehouse; up its stair,
door 3 into the lower barracks (a footlocker box, two chests); the treasury's sinking wall and its six chests (the
footlocker on the shelf); the guard post, door 5, the upper barracks (four boxes); the great hall and the hidden axe
(given once: the second click gives nothing, variable asserted); door 8, the antechamber, the study's drawers (the
Warlord's Key and a storage key, once), the shared cabinet; the bedchamber's cabinet (95 and 1682 asserted); the vault
door (key spent) and the statuette chest (qbits 1076, 1211, item 2128, variable asserted); the storeroom's east door
with one key (double locked, stays shut); the hall stair, the gallery, the west hall, the drill hall; door 15 to the
side room; door 16, the throne room (second key, two cabinets, the shared cabinet's box), the closet's rising wall
and its chest; the storeroom's north door with both keys (opens, keys kept, variable 10), the east door (opens, keys
spent); doors 10, 12, 13, 14 and their barracks and chests, the officer room, the closet's rising wall and its
cabinet; door 18, the back stair down, the switch (the portcullis opens, variable asserted), through the portcullis,
up the gate tunnel and out to Silver Cove (`outd1.odm` asserted).
Not by chance: every walk clears hostiles within 2,500 (the spawned soldiers), and before every looting the packs are
emptied of all the walk does not assert (`make_room` as the Forge's playtest does it), so no chest fails for room.

## Pictures

`output/studio_cal/mm6_6d16/ingame_final/diff/` (20 pairs). Looked at: the lower barracks with its bunks (0.998), the
treasury and its shelf (0.988), the bedchamber (0.987), the antechamber and its cove (0.981), the great hall (0.962,
blurred difference 0.004), the throne room with its knights (0.891), the gate hall and gate tunnel (0.76 to 0.78: the
tunnel's walls are the original's curve within some 20 units, so the stone courses fall elsewhere; the gate hall's
roof is flat at the crown, gap 2). Least alike: the hall stair (0.66) and the stair passage's flight (0.72): the same
walls, steps and plank treads, the stone courses on the raking walls lie at other offsets (no word for a texture's
offset), and the storehouse stair (0.75): its walls are one texture where the original changes from d1wlDLE2 to
d1wlDLE3 at z 0 (gap 6).

## Gaps, most harmful first

1. **Click spots on a tunnel's sides, a floor or a roof.** The false doors' second bindings (ten faces, above): the
   way into the cellar a player finds by clicking the tunnels. A tunnel takes no `walls`/`panels`, and no floor or
   roof patch is a click source. Fields: panels with an `id` on a tunnel's sides; `floor_panels`/`ceiling_panels`
   (or a plate with `click: true`).
2. **A chamfered roof meeting a tunnel's mouth.** The gate hall (the tunnel's head, the exit and the arrival) and the
   tunnel end carry the tunnel's section in the original (walls 256, chamfers 64 by 64, crown 320 over the floor);
   here their roofs are flat at the crown. A whole-ceiling level with upright ends, or ceiling points, gives the room
   the section's profile, but the mouth is refused (tool defect 1). Field: none needed; the mouth check should take
   the wall's own profile.
3. **A tunnel's side doorway keeps its chamfers.** The junction's east strip is the tunnel; its west side is open to
   the junction from y -128 to 384, and over that width the build stands the side up to the crown and runs the
   tunnel's flat roof to it, where the original keeps the chamfer from 256 to 320 over the junction's plank ceiling
   (the compare's "ceiling 64 higher" at -4608, 256). Field: a side doorway as high as the section's upright walls
   keeps the section's upper sides over it.
4. **A choice among several teleports** (events 20-24, Lua with `PickRandomOption`). Field: `teleport: {one_of: [...]}`
   beside `give_item: {one_of}`.
5. **An effect that waits on a variable** (the double lock spends the keys on the second door only: Lua). Field: an
   `if: {condition, effects, else}` step.
6. **A band at an absolute height on a raking wall**: the storehouse stair's sides change from d1wlDLE2 to d1wlDLE3
   at z 0 (30 rays, the largest texture miss); `bands` need a level floor. Field: `bands` with `absolute: true`, or a
   panel whose level edge may cross the raking foot (tool defect 2 builds exactly that, silently).
7. **A random item by level and kind** (the axe: `evt.GiveItem(6, 25)`, Lua). Field: `give_item: {level, kind}`.
8. **Two textures for a wall's two ends.** `ends` takes one surface; the original's every wall has `...RE` at its
   start and `...LE` at its end, and the same strips beside every doorway: 446 panels from a script. Field:
   `ends: {start: surface, end: surface}` and `jambs` on an opening.
9. **An opening flush with a room's corner.** The closet walls 11 and 17 stand 16 off the corner the original's
   meet (an opening keeps 16 of wall beside it); the tunnel end runs 64 farther west than the original's level floor
   so that the secret wall keeps 16 beside it.
10. A door leaf narrower than its doorway with a jamb strip (the original's leaves are 126 with a 2-unit d1trimRE or
    D1SMBW jamb; here 128); the bunks' invisible front faces (32 to 136, face 2603 and its kin) are not built (the
    party cannot stand in the 96 under the upper bed anyway); the bunks' pillows (qgzwood) are not built.

## Tool defects

1. **A tunnel's mouth into a room whose wall rises into a whole-ceiling level is refused.**
   `oymap build output/studio_cal/mm6_6d16/repro/tunnel_mouth_gable --assets assets_dev --out <scratch>`: "the
   tunnel's mouth does not lie in the wall of room:hall: it reaches ... from 0 to 320 in height, where the room's floor
   is at 0 and its ceiling at 256", though the hall's east end stands upright to 320 with exactly the section's
   chamfers (`top_outline`), and an ordinary opening may rise into such an end. The same with `ceiling_points`.
2. **A panel with `bottom`/`height` on a stepped room's raking wall builds silently with its `bottom` dropped**: the
   panel runs from the steps' foot to its level top (`repro/panel_on_stepped_wall`, faces 4 to 18 of its export),
   where the schema says such a panel is refused with the allowed heights. (Read as a word, it would say gap 6.)
3. **Dark lights warn even when the original holds them dark**: 75 warnings "starts dark and no event lights it ...
   or drop the light" for the original's own records (attributes 8). Wanted: a way to say "dark as the original's"
   (a note the warning reads, or `on: false` without the warning when `map_stats.reference` is set).
4. `compare.py`'s originals count closed-door portals as doorways 2 wide and the original's unreachable 42-by-42
   switch-picture sector as its smallest sector (both "out").
5. Not the studio's, for helper authors: the objects schema's switch keys `on` and `off` are YAML 1.1 booleans;
   PyYAML's `safe_load` turns them into `true`/`false` keys (validate then says "switches[0].false: unknown key").
   The canonical files quote nothing; a helper that loads and dumps objects.yml must restore them.

## What I was unsure of in the original

- **Chest 11's item.** The scene's chest record 11 holds item 2128, which items.txt names Discharge Papers; the
  event's string ("The Eagle Statuette!"), qbit 1076's note and the L3 brief speak of the Eagle Statuette (2073).
  The rebuild holds 2128, as the shipped scene does; if the scene's number is a conversion slip, both maps share it.
- Door speeds: the records' `open_speed` 50, passed on as 50 units a second.
- Which jamb each sliding leaf folds to: read from which edge the record moves (the moving vertices' place and the
  direction), turned into `slide_left`/`slide_right` as seen from the opening's `from` room; the playtest opens all.
- The secret flag on doors 1, 4, 11 and 17 comes from the scene's face overrides (0x2 added to their faces), not
  from the BLV; door 19's faces carry only the moved-by-door bit, so the portcullis is not secret.
- The switch's plate is cog 1 (ids.lock.yml `cogs`); the load event names that number.
