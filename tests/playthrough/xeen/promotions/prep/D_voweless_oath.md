# Prep: block D, Q-D17 The Chalice of Protection on the oath route (segment 35)

Quest file: `assets_dev/worlds/xeen/source/quests/q-d17.yml` (Act V, level 50). Dark promotion `knights` in
`Xeen.Promotions`: Cavalier -> BlackKnight, Crusader -> Villain. Light alternative: the Chalice to Bosco (no promotion).

## Start

`checkpoints/31_dimitri_test.oysav` (this chain's segment 31): D1 outside Castle Kalindra's gate, party
Champion Crusader Wizard RangerLord, Q-D17 untouched (113340-113345 clear). Nothing gates D5, DD-25 or DD-08 at
that point of the main chain (the desert road and both doors open without later main-chain bits), so no later main
checkpoint is needed.

## Travel (main 69's edges)

D1 (21504, 2048) east edge -> D2 (29696, 10240) east edge -> D3 (12288, 20480) north edge -> D4 (-30208, -8192) west
edge (desert road) -> D5 arrival about (20992, -8192). Each edge: `walk_to ... expect: dialog`, OK, `follow_map_move`.

## DD-25 Bosco's Hall

- D5 door: thing:bosco_door, event 85 (`evt.MoveToMap(2048, 0, 0, 1024, ..., "xeen_dd25.blv")`), the party placed
  on the terrace at (-410, 9062, 2688) facing west; `click(85)`.
- Arrival (2048, 0, 0); the arrival line once (117680).
- Route (A8's `devdocs/xeen/briefs/dd25/L4/playtest.yml`): (1600, 0) -> (1280, 600) -> (1280, 1100) -> (128, 1100) ->
  (128, 500) -> (-800, 400) -> (-1600, 0, 64) -> (-1820, 0, 128), throne hall leaves `open_door(12, 1)` (doors 1, 2)
  -> (-2400, 0, 128) -> (-3250, 0, 224) -> (-3380, -288, 224); the King's Hall event 8 opens Bosco (5401).
- Bosco, topic "Chalice": first "Here is the key to their tower ... Chlc" (sets started 113340, key 113341, autonote
  4570); after the oath "You gave it back to those mumbling knights? ... Get out." (no pay); with the Chalice (not
  taken here) the Light hand-in (done 113343, 2 disks, 5,000 gold, 14,000 experience, award 457).
- Out: the loop back to (2150, 0), event 4 "Do you wish to leave", OK -> D5 (-512, 9216, 2688).

## D5 the Northern Tower

- thing:northern_tower, event 28: `XeenQuests.hook("q-d17.tower_door")` (needs key 113341), then
  `evt.MoveToMap(0, -1152, 0, 512, ..., "xeen_dd08.blv")`. Party placed at (2560, 11988, 3008) facing north,
  `press_interact`.

## DD-08 the Northern Tower (A8's `dd08/L4/playtest.yml`, `playtest_oath.yml`)

- Arrival (0, -1152, 0). Dark knights 11150 (33) and 11151 (12) hostile until the oath; killed by the run's rule.
- L1 -> L2: (0, -620) -> (0, -200) -> (0, 60) -> great stair (0, 900, 448) -> (-400, 960, 448), west armoury door
  `open_door(29, 7)` -> (-1100, 960, 448).
- L2 -> L3: (-1300, 32, 448) -> (-1984, 32, 448) -> west wall stair (-1984, 900, 896) -> (-1400, 960, 896) ->
  (-1100, 128, 896) -> (-300, 60, 896) -> (0, 60, 896).
- L3 -> L4: Stair of Silence (0, 900, 1344) -> (-400, 960, 1344), chapter hall double door `open_door(26, 1)` ->
  (-1200, 960, 1344) -> (-1216, 1600, 1344) -> antechamber (-256, 1700, 1344).
- The mask, event 54: "Wht d y sk?" (`answer_input`): "Chlc" or "aie" -> q-d17.voice (113342), iron door 8 opens;
  "Chalice" -> voice_wrong; anything else -> voice_other.
- Chalice room: (256, 1700) -> (256, 2300), event 20 (q-d17.chalice: item 12525, chalice_taken 113345, once).
- The plaque, event 43 (chapter hall, reached at (-1500, 1000, 1344)): without the Chalice the fail text; with it
  "Swear the Voweless oath?" Yes -> q-d17.oath: Chalice taken, 2 Energy Disks (12334), oath 113344, started
  cleared, 14,000 experience each, `promote: knights`, the four figures (group 40) shown, the tower friendly
  (relations.yml after 113344). Afterwards "Th nth s swrn." (oath_again needs a promotable member: none left).
- The books (7, +1 a statistic each, player bits 11370-11376) and the Hall of Thrones (four lows, then Euphoria,
  11377) are optional and not played.
- Out: back down the same way to (0, -1300, 0); event 37 "Exit the Knight's Tower" (OK) -> D5 (2560, 11776, 3008).

## What the segment asserts

Q-D17 started/key; voice_answered; chalice_taken; the oath's text, +14,000 each, +2 disks, Chalice gone; classes
Champion Crusader -> Champion Villain (check 2: the party's Dark promotion; check 4: the Champion, promoted on the
Light path by Dimitri, is not made a Black Knight); the plaque again pays nothing; Bosco after the oath pays nothing
and done 113343 stays clear.

## Observations

- On the way out of DD-08 the status line shows "You found something (Key)!" twice (drops of the knights the run
  kills, not a quest item; not followed up).
