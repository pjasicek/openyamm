# Prep: block D, segments 30-45 (Mage, Scholar, Ranger)

Research for `30_johannes_task.yml` ... `40_fenja_ranger_done.yml`. Every step was run headless from
`checkpoints/00_start.oysav` (2026-11-08/09); the scratch probes and their logs are in the session scratchpad
(`scn/p*.yml`), the scratch saves in `output/playthrough/mm9/promotions/scratch/D/`. Conventions as the main run's
prep sheets: MM9 key K = qbit 90000+K, MM9 item N = engine 10000+N (`world_common.lua` `MM9.ItemIds`; raw 347 is
global 419, Eye of the Storm), +y north, yaw 0 east. Positions in native units.

Tools written for this block (scratchpad `tools/`): `nmap.py <project> out.png x0 x1 y0 y1 [zmin zmax] [grid]`
(native-coordinate floor map of an mm9r dungeon project with DAT objects and, with `WALLZ=lo,hi`, walls),
`rails.py <project> x y x y` (shortest route on MM9's AIRail graph, printed as `via` points), `floors_in.py` (the
up-facing polygons in a box, with their heights), `actors.py <stem> [filters]` (scene actors and their indices).

## Order and segments

| Seg | What | Asserts |
| --- | --- | --- |
| 30 | travel Thjorgard, west gate; Johannes Bem (actor 0, (5079, 12452, 1); placed at (5079, 12250)) | key 4 |
| 31 | Isle of Ashes, Verhoffin Ruins walked: bolt, west rooms, crevasse, key, Door5, silver book, back out | 281, 290, 10242 |
| 32 | Thjorgard: "About that book..." / "We found a silver one." / "So did that book work for you?" / "Goodbye." | 286, 293, 288; 10242 gone, 10244 |
| 33 | Drangheim: the cottage (RotatingDoor0, event 102), floorboard, the gold book | 283, 290; 10560, 419 |
| 34 | Thjorgard: "We found a gold one." / "Did that book work out for you?" / "Goodbye." | 289, 493, 294; +5000 gold, +37 500 xp each, classes unchanged; Johannes offers "Promote our eligible characters." (nobody) |
| 35 | Tymon the Nord (actor 13, (4915, 12780, 1)): "We are seeking promotion to Scholar" / "Yes." / "We will do this." (201); docks gate; the Magreeb | 201, 202 |
| 36 | west gate, Tymon: "We studied the Magreeb." / "Alright." / "Green" / "Thank you." / "Goodbye."; Johannes's offer seen, not taken | 204, 205; member 3 Sorcerer -> Wizard; +1000 gold, +11 000 xp each |
| 37 | travel Frosgard, road gate; Fenja Tree-friend (actor 45, (4260, 4424, -5)) | 238, 239, 240 |
| 38 | travel Guberland; Dook's Castle and its caverns walked; Everstrike | 10184 |
| 39 | travel Frosgard; the Dungeon of Secrets: Chadwick's trial run clean; his reward | 243, 245, 246, 247 |
| 40 | road gate; Fenja: "We've completed the Ranger's Trial." / "Thank you."; her offer (nobody) | 241, 248, 249; +5000 gold, +37 500 xp each, classes unchanged |
| 41-45 | spare | |

## Mage (Johannes Bem, RUDE 4, `thjorgardcity.lua:107-118`)

- Rows: "We wish to become Mages." (needs 205: waived, grants 2082) -> "We have one of those." (needs 205: waived) ->
  "You want us to get it for you?" -> "We will take this quest." (key 4) -> page 997 "Goodbye.".
  Hand-ins on his first page: "About that book you were looking for." (needs 290, not 493) -> "We found a silver one."
  (281 -> 286) / "We found a gold one." (283 -> 289). Then "So did that book work for you?" (286 -> 293, close page
  "Goodbye.") and "Did that book work out for you?" (289 -> 493, "Goodbye.").
- Exit hook 51044: with 293 (once, 288): takes 10242, gives the Book Key 10244 (on the cursor). With 493 (once, 294):
  takes raw 243, `reward(294, 37500, 5000)` (each member, `MM9.giveExperience` adds to Players.All),
  `MM9.promoteParty("Mage")` (Wizard -> ArchMage only).
- **What is true in this build:** the silver book (`fakebook.scr`, `verhoffinruins.lua:150`, event 220) gives 281, 290
  and 10242; the Book Key is required for the Drangheim cottage door (`drangheim.lua:31`) and for the gold book
  (`realbook.scr`, event 330: 283, 290, items 10560 Verhoffin's Book and 419 Eye of the Storm). So the Verhoffin Ruins
  cannot be skipped. NOTE (MM9's own script): Johannes takes raw item 243, which nothing gives; the gold book 10560
  stays in the pack (as in MM9).

### Verhoffin Ruins (walked)

The ruins split in two: the southern corridor (start, cells, the bolted PrisonDoor2) and the rest. They meet only at
PrisonDoor2 (its bolt, destructible 648, is on the south side: from the north a click hits the door, not the bolt);
the crevasse can be dropped into from the start corridor but not climbed back. So: in by the bolt (as main run 57),
north through the pentagram room keeping to x -4540 (clear of the points' 90x90 boxes), the west rooms (DD3 at
(-2611, -489) is clicked by the walker), the crevasse's west ramp (-4096, -1597, -409) down, east along its floor (shallow
water, -614) to its east ramp (2273, -4485, -419), the long east corridor (x 2370..2816) south to DD14 (event 117,
leaves 37/38; they shut again: check `door_state(37)` both ways). Door5's key: world item 10559 at (3072, -5980, -236),
`pick_up` from (3072, -5880). North up the corridor (DD7 at (2662, -1362), walker click), west along y -491 (DD2 at
(829, -489)), north through DD6 ((-899, -215)) into the split room: Door5 (event 207) from (-901, 491); the book (event
220) from (-361, 189). Back the same way to PrisonDoor2 (door id 61), the cells corridor at y -5406, PrisonDoor3
(walker click), the stair's ExitTrigger0 (walk to (-850, -5900, -250), "OK").

## Drangheim Village (`drangheim.blv`, outdoors)

The cottage at x -7672..-6565, y -2650..-1175 (the guide's "east of the city across the inlet" does not match: it is
far west of the dock, next to Ragnheid (actor 34) and Hring (actor 35)). Its north door RotatingDoor0 (door id 2,
event 102) opens only while the party carries 10244. Placed at (-7120, -1000, 2220) facing south, click, walk in via
(-7120, -1420). The floorboard DestructableBrush0 (destructible 57, hp 1) at (-6769, -1420, 2191) over the book
(Capstone0, event 330, decoration sprite 400 at z 2146).

**ISSUE (suspected converter/engine bug):** the floorboard cannot be broken: `press_action: attack` at every pitch
from 25 to 75 degrees down leaves `destructible 57 state` "standing"; the crosshair's pick passes through it and hits
the book below (`press_interact` from (-6918, -1413, 2202), yaw 0, pitch -0.85: "Prop" event 330), which a player can
take through the board. Segment 33 asserts the board still stands (`expect_contains: standing`) so a fix shows up.
Repro: segment 33's steps after the door.

## Scholar (Tymon the Nord, RUDE 161, `thjorgardcity.lua:120-131`)

- "We are seeking promotion to Scholar" (grants 2081, not after 201) -> "Yes." -> "We will do this." (closes); exit:
  2081 -> 201 + quest sound. After the Magreeb: "We studied the Magreeb." (202, 201) -> "Alright." -> "Red" (203) /
  "Green" (204) -> "Thank you." -> "Goodbye."; exit: 203: 16 500 xp / 204: 11 000 xp, 1000 gold, key 205,
  `promoteParty("Scholar")`.
- The Magreeb (`thjorgard.lua:496-520`): actor 16 (monster 9277 "MM9 Magreeb B", skin MAGREEB1: olive-green chitin,
  orange claws, `worlds/mm9/models/actors.yml`) at (-16934, -20179, 3190), west of the Frosgard road's start where
  travel lands (-12830, -19987); with 201 and within 1536 it gives 202, the quest sound and is removed. The baby
  (actor 4, (-18639, -16114)) gives 202 within 4608 when the quest is not waiting (the guide's tip); travel's
  arrival point is 6970 from it, so it does not fire by accident. Walked from the road's start to (-15500, -20150).
- The colour is what a player saw: **Green** (11 000 xp). "Red" (what Tymon's texts say) pays 16 500: a user's call.

## Ranger (Fenja Tree-friend, RUDE 181, `frosgardcity.lua:141-151`)

- "We've heard you can promote Crusaders to Rangers." (grants 2079) -> "Yes." (needs 137: waived; key 240) ->
  "Tell us about the first task." (238) / "Tell us about the second task." (239) -> "We will do these tasks" ->
  "Goodbye". The second task is the Dungeon of Secrets: Chadwick's "We are here for the trial." needs 239, and
  Fenja's hand-in "We've completed the Ranger's Trial." needs 245 (Chadwick's "done") and 241.
- Her click (53593) gives 241 while Everstrike (10184) is in the packs; exit 50593 with 248: key 249, 37 500 xp,
  5000 gold, `promoteParty("Ranger")` (Hunter, WarriorMage).

### Dook's Castle and its caverns (walked)

- Gate: guberland ExitTrigger0 (-13341, 17189), placed at (-13341, 16820) facing north. Inside: StartPoint0 (0, 1393).
- **The Dook's friendly guards** stand and wander in the one-party-wide west corridor (actor 2 at (0, 4588), sleepers,
  actors 3 and 12 wander into the walk): `walk_to` past them gets stuck ("nearest actor N at 75"). Round them: the gate
  hall planned to (0, 4382), then via the east hall (doors 03 at (317, 5240), 02 at (338, 6924), walker clicks), then a
  planned walk to (0, 9093) and (700, 9093) (door 04), the north-east room. `press_action: attack` and `party_attack`
  on a friendly guard do nothing (no hostility); not used. The route may need care in the save-and-load run (wander).
- The shield (event 70, at the north wall, from (2450, 9200)): `SecretOpen`, Hostile 1, the guards hostile (killed).
  The secret door (doorslide) is at (860..900, 7520..7700); behind it the passage x 410..730, a stair north down to
  (570, 9100, -100), the loop cave. A planned walk from (500, 9600) to (6550, 4440, -2700) takes the caves down to the
  lake cavern's west mouth (21 s).
- **The rope bridges** (lake cavern, `floors_in.py`): from the mouth (-2764) down in steps to the hub platform
  (-3235, x 9308..10219) and from it up to the chest ledge: -3143, -3041, -2949, -2856, -2744, -2652, -2580 (rises of
  72-110 at each junction). The party steps 51; walked, it falls off the side into the lake (wading floor at -3988).
  Each rise is a `movement_segment` jump (0.55 s east, 0.5 s west) from a point ~150 before the next plank row
  (logged JUMP; ISSUE: MM9's player climbed such steps; the converter added invisible ramps only at the lake's rim).
  Seven hops out, six back (the western bridges rise westward: -3184, -3102, -3020, -2938, -2846, -2764).
- TreasureChest0 (event 46, trap 14, Everstrike in slot 1) at (13148, 4300, -2539): the party cannot disarm it; the
  first click sets the trap off (no chest view, no status line), the second opens it (`take_chest()`).
- Out: planned walk to (570, 9300, -100), the passage, the north-east room, door 04, the west corridor (guards dead),
  the gate hall, ExitTrigger0 at (0, 1146).

### Dungeon of Secrets (Chadwick's trial, `dungeonofsecrets.lua`)

- Entry: frosgard ExitTrigger0 (16260, 5578, 1925); placed at (15441, 5578, 2151) facing east. Chadwick (actor 0,
  (4076, -1065)) through the booth's bars from (4336, -1065): "Hello." / "We are here for the trial." / "Okay." /
  "Yes" (243). Reward later: "We'd like our reward." (245 -> 246), closed with Escape: exit 50636 gives 10 000 xp and 247.
- **Every map load resets the trial** (handlers[1] takes 243 and 244): the whole run is one segment, and a
  `reload` inside it loses the trial (the save-and-load run cannot pass 39; MM9's :Init2 kept it on a full load:
  README "Deviations"). Decision for the user.
- Trap = key 244 (any `dotrap` while 243 is held): axe traps, the 61 fire plates (`trigger01-61`), the 13 gauntlet
  triggers, the double axe's upper/lower plates (`doubleaxe_*_trigger`, polled boxes), the blade's panels. Touch boxes
  are grown by 37 in x/y and by 170 down (`crosses()`), polled 10 times a second along the path.
- Timer windows (lever open 0.9 + close): 10 3.15 s, 9 3.47, 8 5.4, 1 9.5, 2 9.9, 3 3.0, 4 5.4, 5 3.15, 6 9.9; the
  door must open (0.41 s) while the lever holds its axe locked.
- Positions (lever click pose, door click pose, events): 10 (4129, -363) 218 / (4104, -410) 208; 9 (3569, -668) 217 /
  (3305, -983) 207; 8 (2913, -402) 216 / (1536, -376) 206; 1 (-2022, 2158) 209 / (-2376, 4416) 200; 2 (-404, 4800) 210 /
  (-655, 3884, 615) 201; 3 (896, 2834, 656) 211 / (1536, 2219, 656) 202; 4 (771, 1193, 656) 213 / (-1221, 1208, 656)
  203; elevator: walk (-1761, 307, 656) -> (-1761, -461, 860); 5 (-1761, -486) 214 / (-1761, -1221) 204; 6 (-1733,
  -1848) 215 / (2532, -1720) 205; the entrance button 240 from (4442, -471); exit gate open trigger x 2944..2954.
- **Between 8 and 1: the lower double-axe plate** (x 164..492 grown 127..529, in the flooded pool room's lower corridor,
  y 1190..1330, wading: water top -41 over floor -61). Walking west through it is a trap; a jump while wading does not
  clear it (0.6-1.2 s hops all landed on it). MM9's way: the water grate (event 241, (850, 1250)) opens and locks
  open; down the east shaft under it (`fly_down` 1.5 s), west through the submerged tunnel (z about -600, 4 s at 384),
  up the west shaft (`fly_up`; surfaces with the feet at -174), a surface jump west out onto the floor. Traps 0.
- **Section 1, the fire plates:** a grid; in the lane x -2048 the rows at y 2560, 2867, 3174, 3482, 3789 leave the
  big octagons free, the rows at y 2714, 3021, 3328, 3635 are plates wall to wall (grown bands 2677..2792,
  2984..3099, 3291..3406, 3598..3713). A 0.25 s running hop goes 192 (the party stops when the key is released) and
  clears a band: from y 2620, 2940, 3250, 3560. No plate fired.
- **Section 2:** the blade's box (Trigger (BUS), x -1024..-287, y 3564..4301, z 189..271) lies under the stair; the
  planned walk up the stair does not touch it.
- **Section 3:** the real lever is lever 03 (event 211; its twin 03a 212), the ninth from the south (guide); the 21
  fake levers (219-239) move and lock nothing.
- **Section 4:** the double axe's upper plate (x 287..410, grown 250..447, feet must stay above 681) is hopped (0.35 s
  from x 520); then **the upper corridor has no floor at x -573..-163** (y 1105..1310; `floors_in.py`, and a party
  placed at (-400, 1208, 700) lands at -61): MM9's DAT has no floor there either. Jumped with a 0.8 s running jump from
  x -110 (lands at -722). The scenario_trial teleported past both.
- **Section 6, the gauntlet** (plates grown by 37): walked at y -1720 past gtrigger1/2, y -1580 past 3a/3b, y -1880
  past 4, y -1720 past 5/6/10; hops over gtrigger7 (0.25 s from x 810), 8a+8b (0.55 s from 1170), 9 (0.4 s from 1810).

## Guide errors and notes

- find-verhoffin-s-diary: "Johannes talks to Scholars only" (waived here); Drangheim Village is west, not east of the
  city; Johannes's take of item 243 leaves the gold book with the party.
- find-everstrike: the shield opens the way regardless of the Dook's business (side_b's quest not needed); the
  chest's trap goes off on the first click unless disarmed.
- pass-through-dungeon-of-secrets: the lower plate in the pool room (between sections 8 and 1) and the gap in
  section 4's corridor are not mentioned; the plates of the fire room are the small squares/octagons in every second
  row, not "the floor tiles" between "plates".

## Suspected bugs / decisions

1. Drangheim floorboard (destructible 57) cannot be broken by a blow; the book is clickable through it.
2. Dook's Castle bridges: 72-110 rises at each plank junction; the party needs a jump at each (13 jumps there and
   back). MM9's player climbed them? (converter: invisible ramps only at the lake's rim).
3. Dook's friendly guards block the castle's corridor (wander into the party's path); worked around by the east hall.
4. Dungeon of Secrets: the trial resets on every load (documented deviation): no save-and-load run for segment 39.
5. Tymon's colour: Green (seen) vs Red (texts): 11 000 vs 16 500 experience.
