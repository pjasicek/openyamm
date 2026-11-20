# Prep: segments 20-34 (Chapter I: Thjorgard's and Guberland's tasks)

> **Directions (corrected 2026-11-09):** compass words in this note were taken from raw coordinates as if +y were
> north. On MM9's outdoor maps (regions and cities, `flip_u` in `worlds/mm9/ui/maps/catalog.yml`) the map a player
> sees has +y at the bottom and +x at the left, so those directions are turned 180 degrees; the guide's directions,
> which follow the maps and agree with the original walkthroughs, are right. Indoor maps are not affected.

Research for Sven Forkbeard's two tasks (Thjorad from Lindisfarne; the Thjorad Mine's hard rock, cave-in and refinery)
and Markel the Great's two tasks (the Book of Rules from the Ta'Sar Academy; Ivan the Smart's trivia). Every step
below ran headless (`build/game/openyamm`, 2026-11-08 21:00-22:10) from `load_map` with the missing keys set by
console, chained through scratch saves. Scenarios and logs:
`/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/71103dcf-46f6-4f99-97fd-0c82879b3192/scratchpad/early2/runs/`
(`a_sven` Sven's tasks, `b_mine1` Ketil and the hard rock, `c_mine2` Gudrek and the cave-in, `d_mine3` the cavern
and the climb out, `e_mine4` barricade, refinery, Njal, the broken part, `f_city` out of the mine, Hjarrand, Gunnar,
`g_mine5` back in, the new part, `h_monastery` bells and Thjorad, `i_ladder` ladder timing, `j_tasar` / `k_books` /
`l_books` the academy, `m_guber` Markel and Ivan, `n_sven` Sven joins, `o_lind` the island exits). All passed.
Plan crops and floor renders (`*.png`) and the helpers `floors.py` (BLV floors coloured by height, walls white),
`faces_near.py` and `plan.py` are one folder up.

Conventions as in the other prep sheets: MM9 key K = qbit 90000+K (keys >= 9000: 9510 -> 99510); MM9 item N =
engine 10000+N; +y north, yaw 0 east; an actor's click event is 53000 + its DAT index, its dialogue-exit event 50000 +
that index (Sven 54098/51098, Gudrek 54396/51396, Hjarrand in the mine 54399/51399). `click()` runs the event
directly (no range check), so each segment walks next to the prop first. Dialogue rows below were read from
`assets_dev/worlds/mm9/dialogue/rude/NPC<n>.rude` and every line was picked in a run.

**Rewards fire when the dialogue closes** (the exit events): Sven's and Markel's last lines lead to a "Goodbye."
node; pick "Goodbye." before asserting their keys.

## Proposed segments

**As written (2026-11-08, from `19_drangheim_pledge.oysav` in Drangheim City):** 20 Markel's tasks (Black Hammer,
1 day), 21 Ivan, 22 Sven's tasks (Flying Bird, 4), 23 hard rock, 24 cave-in to the broken part, 25 Hjarrand and
Gunnar, 26 the new part, 27 the monastery (Sea's Fang, 4), 28 Ta'Sar (the Book of Rules is now a world item:
`pick_up: {item_id: 10391}`), 29 Sven joins (Raider, 2), 30 Markel joins (Sea's Fang, 4). 31-34 unused. The table
below is the first plan (Thjorgard first); its per-step notes still apply.

The order depends on where the previous agent's checkpoint ends; both clans are independent. Days are the boats in
`worlds/mm9/data_tables/transport_routes.txt`.

| # | Segment | Checks |
| --- | --- | --- |
| 20 | Thjorgard City: Sven's two tasks | keys 2, 3, 30 |
| 21 | Thjorad Mine: Ketil, the hard rock (Ebora's cinematic) | keys 9509, 36 |
| 22 | Mine: Gudrek's lead, the cave-in, the cavern, the cave wall, the climb to the loop, BarWall1's spikes, the refinery, Njal, the broken part; out | keys 9510, 9511, 35, 5, 9512; item 10398 |
| 23 | Thjorgard City: Hjarrand paid (1 000 gold), Gunnar's swap | keys 362, 9513, 9514; 10399 in, 10398 out |
| 24 | Mine again: Hjarrand at the machine, the new part installed; out | key 37; 10399 gone |
| 25 | Sea's Fang to Lindisfarne (Fri, 4 days); the monastery walked: ladders, bells, Thjorad | keys 9507, 31; item 10197 |
| 26 | The Raider to Thjorgard (Tue, 2 days); Sven: Thjorad, the mine, he joins | keys 32, 33, 34, 163, 177; 10197 gone; +9 000 gold |
| 27 | Sea's Fang to Guberland (Thu, 4 days); Guberland City: Markel's two tasks | keys 56, 57, 58 |
| 28 | The Gathering: Ivan's trivia | keys 60, 164; item 10400 |
| 29 | Flying Bird to Lindisfarne (Mon, 3 days); Ta'Sar Academy walked: books, scroll, bookcase, Book of Rules | keys 9501-9504, 9516, 59; item 10391 |
| 30 | The Raider to Guberland (Fri, 5 days); Markel: book, Ivan, he joins | keys 61, 62, 63, 165, 167; 10391 and 10400 gone |
| 31-34 | spare | |

## Maps, exits and arrivals (all tested in `o_lind`, `f_city`, `g_mine5`)

| From | Exit (walk into it, then "OK") | Arrives |
| --- | --- | --- |
| thjorgard.blv | City gate ExitTrigger2 (-8790, 4392, 1951): `set_pose (-9300, 4392, 1951) yaw 0`, walk east | thjorgardcity (655, 164, -19) |
| thjorgardcity | Docks gate (655, -819, 225): `set_pose (655, -400, -19) yaw -1.5708`, walk south | thjorgard (-9336, 4386) |
| thjorgard.blv | Mine ExitTrigger5 (-16534, 12292, 4598): `set_pose (-16893, 12425, 4449) yaw -0.35` (the mine's own arrival point), walk east. From (-16900, 12000) the walk sticks on rock | thjoradmine (2785, -2785, -900) facing north |
| thjoradmine | ExitTrigger0 (2785, -3195, -789): walk south from (2785, -2785) | thjorgard (-16893, 12425, 4449) |
| lindisfarne.blv | Monastery ExitTrigger0 (-11749, -21240, 2734): `set_pose (-11250, -21240, 2734) yaw 3.1416`, walk west | monastery (-327, -935, 3) facing north |
| lindisfarnemonastery | ExitTrigger0 (-328, -1393): walk south from (-328, -1000) | lindisfarne (-10909, -21059, 2535) |
| lindisfarne.blv | Ta'Sar ExitTrigger1 (12889, 21932, 3932): `set_pose (12400, 21932, 3736) yaw 0`, walk east | tasaracademy (2621, 655, 0) facing south |
| tasaracademy | ExitTrigger0 (2621, 1065): walk north from the start | lindisfarne (12541, 21932, 3736) |
| guberland.blv | City ExitTriggerGuberland (6131, -9194, 1651): `set_pose (6131, -9700, 1651) yaw 1.5708`, walk north | guberlandcity (-655, -287, -9) |
| guberlandcity | ExitTrigger0 (-655, -41, 307): walk north from the start | guberland (6151, -10359, 1411) |

`travel` lands at the docks: Lindisfarne (-23123, -333, 425), Guberland (22003, 4558, -123), Thjorgard
(-12830, -19987, 3195) (the Frosgard road's start point, not the dock).

## 20: Sven's tasks (`thjorgardcity.blv`, `a_sven`)

Sven Forkbeard, actor 50, (82, 20736, 3608), the castle at the north end. Placed at **(82, 20480, 3608) yaw 1.5708**.

`interact_actor: 50`, then in order: "We've come to speak to you about Tamur Leng." / "He is a Beldonian Warlord on
his way to conquer the Chedian." / "We are trying to unite the six Clans of the Chedian." / "Yes.  We need to unite
ALL the Clans." (key 30) / "What is the first thing you need done?" / "You want us to retrieve it?" / "We will
retrieve it." (key 2) / "What is the second thing you need done?" / "We will do this for you." (key 3) / "Thanks for
your time." Assert keys 2, 3, 30. (The guide skips "He is a Beldonian Warlord...", the only line offered after the
first one.)

## 21: Ketil and the hard rock (`thjoradmine.blv`, `b_mine1`)

People: Ketil Strongpick actor 44 (4745, -2415, -982); Gudrek actor 42 (2683, 123, -982); Njal actor 43
(676, -123, -654); Hjarrand actor 45 (-2468, 10, 1, hidden until key 362); miner Peasant actor 13 (3113, 1802),
actor 12 (2621, 1802).

- To Ketil: the planner's route into his room runs into the wall by Sign1. Use
  `walk_to {via: [[2785,-2300,-900],[3000,-1950,-900],[3350,-1950,-900],[4300,-2230,-982]], x: 4600, y: -2415,
  z: -982, plan: false}` (3 s).
- `interact_actor: 44`: "Sven Forkbeard sent us to find out why you are not working." / "I don't think he'll
  accept that answer." / "We'll give it a try." / "Where is this section?" (key 9509) / "Goodbye."
- The hard rock: planned `walk_to {x: 24000, y: -1250, z: -1395, z_tolerance: 250, timeout 600, clear_hostiles:
  1500}` walks the long east tunnel (32 s, 4 troglodytes killed) and stops facing the twelve blocks (db12-db23) that
  seal Ebora's chamber (room 32, x 24400-26800). Each block's click is event **38000-38011** (a killing blow; a
  weapon works too). A player breaks blocks until the quest sound: `for i = 0, 11 do if qbit(90036) then break end
  click(38000 + i); wait(0.3) end`, then `wait(14)` for the `ebora_free` cinematic (EboraFree 4: she is gone).
  Key 36 after the tenth. The status line shows nothing per block.
- TriggerHardRock (the gnolls' cages, box (26327..26839, -5048..-4536)) is in room 21 to the south-east, off this
  route; the guide's "gnolls break out as you walk past" happens only if the party goes there. Not needed.

## 22: Gudrek's lead, the cave-in, the way back (`c_mine2`, `d_mine3`, `e_mine4`)

**Gudrek** (from the rock, planned `walk_to (2683, -200, -982)`, 36 s): `interact_actor: 42`: "Sven Svenssen sent
us to inspect the mines." / "Why do you say that?" / "Why is that?" / "Maybe we should go have a look." / "Where is
it?" (key 9510) / "OK." His lead (`thjoradmine.lua` gudrekLead): he walks to (6001, 1987, -1352) only while the
party is within 655 of him, else stops and faces it; he is slow (about 50 a second). The party must pace him:

```
walk_to (2683, 900, -982) plan false;  wait 8
walk_to (2900, 1600, -982) plan false; wait 8
walk_to (3700, 1650, -982) plan false; wait 8      # corridor centre y 1650: the miner (actor 13) stands in the
walk_to (4600, 1650, -1100) plan false; wait 8     # corridor mouth at (3113, 1802); y 1725 and 1880 both stick
walk_to (5000, 1650, -1352) plan false; wait 8
walk_to (5450, 1650, -1352) plan false
play_lua: wait until qbit(99511)                    # arrived within 8 s here
```

Then `interact_actor: 42`: "Is this it?" / "Alright." **The crack**: Gudrek stands in the cave-in room's mouth, so
pass south of him: `walk_to {via: [[6000,1650,-1352],[6700,1900,-1352]], x: 7300, y: 2500, z: -1352, z_tolerance:
2000, plan: false}` enters Trigger7's box (6948..7716, 2115..2883): CaveIn breaks, the party falls to the cavern's
wading floor (7260, 2461, -3263), key 35 (+5 000).

**Out of the cavern** (`d_mine3`; the planner gives only partial routes here): the tunnel climbs from the cavern's
north side to room 58. Via points along its centre line, `plan: false`, `clear_hostiles: 1500` (18 troglodytes and
gnolls killed): (7472, 4865), (7753, 5876), (7472, 6551), (7079, 7169), (6685, 6888), (6124, 6213), (5674, 5989),
(5112, 6551), (4663, 7112), (3764, 7674), (2753, 8011), (1742, 7730), (618, 7506), (-506, 7449), (-955, 7787),
(-955, 8910), (-1629, 9135), (-2978, 9022), (-3750, 8450), (-4157, 8011) to (-4326, 7225, z 573). (-3876, 8573)
lies in the bend's wall; do not use it.

**The cave wall** (CaveWall0-4, "Rock", event **102**, a click breaks all five) closes the tunnel's end at about
(-5263, 6749, 655). The walk clicked it itself; the segment should walk to (-5263, 6700) and `click(102)`, then
check `mapvar("CaveWall") == 1`. The guide's "pull the six spikes of any boarded doorway" is this rock, then
BarWall1 below.

**Room 58 does not join the loop** (room 55 is behind a wall at x -4400). The way round, `plan: false`:
(-4900, 7250), (-5300, 6800), (-5200, 6300), (-5500, 5250), (-6500, 5150), (-7200, 4500), (-7550, 3600),
(-7550, 2800), (-7550, 2450), (-8700, 2450), (-8800, 1800); then **planned** `walk_to (-8800, 0, 655)` (room 30;
a plain via at (-8800, 1100) sticks); then `plan: false`: (-7000, 0), (-5200, 700) (not (-5100, 0): a post),
(-5050, 1300), (-4900, 2000), (-4600, 2800), (-4300, 3400), (-3500, 4200), (-2900, 4700), (-2100, 5000),
(-1000, 5420), (0, 5520) to **(0, 4700)**, north of BarWall1 (pivot (0, 3932)).

**BarWall1** (SpikeDoorA): its six spikes are events **76-81** (Spike6-11); the sixth opens it (BarWall1Open 1;
the barricade swings toward the party, which stands back at (0, 4750)). `for e = 76, 81 do click(e); wait(0.3) end;
wait(3)`. A click on the barricade itself (65) before that only jiggles (doorlock02.wav, no status).

**The refinery**: `walk_to (0, 1900, 1) plan false` (one jump over the fallen boards), `click(61)` (the handle:
the north door slides open for 2.75 s, works again after 10 s), then `walk_to {via: [[0, 900, 0]], x: 300,
y: -123, z: -654}` planned (6 s) down the spiral to the tank floor.

**Njal** (`interact_actor: 43`): "Sven Forkbeard sent us to find out why you've stopped working." / "What is wrong
with it?" / "What does that mean?" / "So this has happened before?" / "Someone had to fix it then, right?" / "Where
can we find Hjarrand Fixer?" / "We will find him, and bring him back to fix the machine." (key 5) / "Goodbye."

**The machine room** (west, through the lift gate Door0): from Njal, planned `walk_to (-1200, 0, 1)` (4 s, worked
from here); `click(62)` (Switch2/3: Door0 rises, auto-closes after 2 s; `wait(4)` then walk at once worked);
`walk_to {via: [[-2000,0,1],[-2700,0,1]], x: -2593, y: 978, z: 1, plan: false}`; `click(69)` (the hatch swings,
`wait(2)`), `click(130)`: item 10398 (Broken Slag Extractor) and key 9512.

**Out of the mine** (`f_city`): `walk_to (-2000, 0)` via (-2700, 0); `click(62)`, wait 4; planned
`walk_to (500, -123, -654)`; `walk_to {via: [[500,100,-654],[800,110,-654],[1000,0,-654]], x: 1350, y: -150,
z: -691, plan: false}` (the tank floor is a channel y about -130..130 and Njal stands in it: pass north of him);
`click(63)` (Door1, the east gate), wait 4; `walk_to (2683, 0, -982) plan false`; planned `walk_to (2785, -2785)`;
`walk_to (2785, -3195) expect: dialog`, "OK".

## 23: Hjarrand and Gunnar (`thjorgardcity.blv`, `f_city`)

- Hjarrand Fixer, actor 21 (-6390, 1475, 1); placed at **(-6390, 1250, 1) yaw 1.5708**. "One of the machines in the
  Refinery is broken." (needs key 5) / "They say you're the only one who could fix it." / "We'll pay you 1,000 gold"
  (key 360) / "Alright!  Let's go." / "Goodbye." The exit takes 1 000 gold (key 362; without the gold key 363, then
  "We have the money." later). 500 or less: "Hm..er..ahh..I guess..not." (back to the offer). He is hidden from the
  city once paid.
- Gunnar Thjorsmith, actor 32 (-2048, 11469, 1), placed at **(-2048, 11250, 1) yaw 1.5708**. "We were wondering if
  you could help us." (needs key 9512) / "We need a replacement Slag Extractor." / "Sounds like a deal!" (key 9513) /
  "Goodbye." The exit swaps 10398 for **10399** and sets 9514. (Shop hours 20:00-06:00 do not hide this row.)

## 24: The new part (`g_mine5`)

Mine entrance as in the exits table, then planned `walk_to (2683, 0, -982)`; `walk_to (2000, -150, -691) plan false`;
`click(63)`, wait 4; `walk_to {via: [[1318,-136,-655],[1000,0,-654],[800,110,-654],[500,100,-654]], x: 300, y: 0,
z: -654, plan: false}`; `walk_to (243, -116, -654) plan false`.

**The spiral up to the west gate** (the planner's route from here failed in two runs out of three, stuck at
(-617, 0, -246) against the tank's inner wall): `walk_to {via: [[400,350,-655],[100,560,-655],[-250,500,-600],
[-480,300,-450],[-560,0,-280],[-530,-250,-150],[-450,-480,-30],[-350,-650,0],[-550,-950,0],[-900,-700,0],
[-1100,-250,0]], x: -1200, y: 0, z: 1, plan: false}` (the ramp runs north, west, south between the tank walls and
leaves at its south-west end; round the pillar at (-650, -650)). `click(62)`, wait 4.

Hjarrand now stands at (-2468, 10) in the corridor west of Door0: talk from **(-2250, 20)** (via (-2000, 0)):
"Is the machine fixed yet?" / "Alright." His walk then starts (MMarker1, 2, 1, 2, the machine: key 364 at stop 5).
To the machine pass north of him: `walk_to {via: [[-2300,110,1],[-2550,260,1],[-2600,600,1]], x: -2593, y: 978,
plan: false}`; `click(131)`: key 37 (+5 000), 10399 gone. Hjarrand's mark (key 364, about 30 s after "Alright.")
is optional (the base takes the part without it), but it comes: suspected bug 1, fixed.

## 25: Lindisfarne Monastery (`h_monastery`, `i_ladder`)

Thjorad (event **75**) at (7127, 5996, 62), the east end of the east wing, guarded by Brothers Kennet, Ricar, Ren,
Rober (actors 23-26). Before the bells a click does nothing; after them the four stand at the prayer markers
(61..-553, 10394-10404) and the click gives item **10197**, key **31** (with key 2), +1 000.

Monks are friends; **never let a step hurt one** (the alarm makes all 26 hostile, the abbot's and Grehgknak's quests
are lost). The walk needs no `clear_hostiles` here.

Route, from the start (-327, -935, 3):
1. `walk_to (-330, 1000) plan false`; `click(101)` (nave doors), wait 2; `walk_to {via: [[-100,1700,1]], x: -100,
   y: 5600, plan: false}` (lane x -100: monks 7, 13, 14 stand on x -350..-500, monk 13 blocks the centre line);
   `click(102)` (crossing doors), wait 2; `walk_to {via: [[-100,6300,1]], x: -330, y: 6900, plan: false}`; planned
   `walk_to (-2278, 7680, 1)` (west transept, north-west corner).
2. **Ladders: `walk_to` cannot climb them** (no route on the monsters' path map; walking north into Ladder4 from its
   foot climbs, but walking on at the top walks back into the hole). A `movement_segment` with the Forward key that
   **turns from the ladder's facing to the way on** over the climb is repeatable: the party climbs, steps off at the
   top exit and walks on, away from the hole, until a wall stops it:
   - Ladder4: `start (-2278, 7700, 1) yaw 90`, `expect_stop (-1838, 7786, 983) yaw 0`, 11 s (10.5, 11 and 12 s all
     ended at (-1838, 7786, 983)). A fixed-yaw climb is not repeatable: from the same start, 9 s ended on the
     ladder at 1053 and 10 s fell back through the hole.
   - Ladder1 (gallery to attic): `walk_to {via: [[-1800,7300,983],[-1800,6700,983],[-2094,6700,983]], x: -2094,
     y: 6800, plan: false}` (from the north the ladder's back stops the party at y 6952); `start (-2094, 6837, 983)
     yaw 90`, end yaw 0, 11 s: ended (-1582, 7639, 2294).
   - Ladder3 (attic to bell floor): its foot (-880, 6025) is reached only along x -880 (the attic roof slopes to the
     floor at y < 6123 west of x -942, and to y > 7660): `walk_to {via: [[-1300,7000,2294],[-860,7000,2294],
     [-860,6400,2294]], x: -880, y: 6025, plan: false}`; `start (-880, 6025, 2294) yaw 270`, end yaw 0, 10 s: ended
     (250, 5976, 3236), the bell floor's south-east corner.
3. Bell floor: `walk_to (-330, 6090, 3241) plan false`. **Ropes** (hanging at y 5944): Rope1 x -251 (east) ... Rope5
   x -415 (west); events Rope1 **91** (bell 1), Rope2 **92** (bell 3), Rope3 **93** (bell 5), Rope4 **94** (bell 4),
   Rope5 **95** (bell 2). A player pulls 1, 5, 2, 4, 3: `click(91, 95, 92, 94, 93)` 1 s apart, `wait(4)`. Key 9507,
   +2 000, AtPrayer 1. No status line; the bells are heard only. (The bells themselves are events 81-85 in note
   order; they hang high over the well, out of reach.)
4. **Down: the ladders have no `grab_at_top`, so the party drops through the holes beside them** (immortal):
   - bell floor hole x -940..-824, y 5940..6103: `walk_to {via: [[-882,6150,3236]], x: -882, y: 6000, z: 2294,
     z_tolerance: 2000, radius: 10, plan: false}`, `advance_runtime 2`. (At (-905, 6030) the party stays on the edge
     at 3221.)
   - attic hole x -2150..-2007, y 6717..6922: `walk_to {via: [[-880,7000,2294],[-1300,7000,2294],
     [-2078,7000,2294]], x: -2078, y: 6780, radius: 10, plan: false}`, `advance_runtime 2`: lands (-2078, 6785, 986).
     **Then walk east first**: heading north from there grabs Ladder1 and climbs back up.
   - gallery hole x -2335..-2191, y 7639..7821: `walk_to {via: [[-1750,6785,986],[-1750,7690,986]], x: -2263,
     y: 7720, radius: 10, plan: false}`, `advance_runtime 2`: ground (-2260, 7720, 0).
5. East wing: planned `walk_to (2350, 6390, 1)`; `click(105)` (RotatingDoor2), wait 2.5; `walk_to (3000, 6390)
   plan false`; planned `walk_to (6950, 6150, 1)`; `click(75)`.
6. Out: planned `walk_to (3000, 6390)`; `walk_to {via: [[2350,6390,1],[600,6700,1],[-100,6700,1],[-100,6300,1],
   [-100,5600,1],[-100,1700,1],[-330,1000,1]], x: -328, y: -1000, plan: false}` (y 6700 between the crossing's
   pillars; y 6900 sticks on one at x 245; the walk clicked the shut nave doors itself, 3 clicks: make them explicit
   `click(102)`/`click(101)` before each); exit south.

## 26: Sven joins (`n_sven`)

Placed as in 20. "We've retrieved Thjorad." (needs 31) / "Here you are." (keys 31, 32) / "Thank you." / "Your mine is
once again producing Thjorad" (needs 35, 36, 37) / "That is working also." (key 33) / "We've completed both your
quests.  Will you join us now?" / "Great!" (key 34) / "Certainly, but we have much work to do before then." /
"Goodbye." The close: key 163 (+12 000 exp, +6 000 gold, item 10197 taken), key 177 (+22 500, +3 000). Gold 10 000 ->
19 000 in the run.

## 27/30: Markel the Great (`guberlandcity.blv`, `m_guber`)

Actor 13 (-2978, -9175, 23), seated, facing east; placed at **(-2722, -9175, 23) yaw 3.1416**. Tasks: "We need your
help." / "We need to unite the clans against Tamur Leng." (key 56) / "What is the first thing you need done?" / "We
will do this for you." (key 57) / "What is the second thing you need done?" / "We will do this for you." (key 58) /
"Thanks for your time."

Report: "We've got the Book of Rules." (needs 59) / "Here." (key 61) / "Thank you." / "We've beaten Ivan the Smart."
(needs 60) / "We did.  He gave us this letter to prove it." (key 62) / "Now that we've done these things for you,
will you join us?" (key 63) / "The leader has yet to be decided." / "We shall.  We'll be in touch." / **"Goodbye."**
(the close: 167 and 165, items 10391 and 10400 taken, +3 000 gold each). If the book was taken before his task (key
166 instead of 59) the line is "We've already got that book." under "What is the first thing..." (not run).

## 28: Ivan the Smart (`guberland.blv`, `m_guber`)

Actor 42 (11563, 18131, 121), at the Gathering south of the dock on the player's map (the guide is right,
as segment 56 found). Placed at **(11563, 17880, 121) yaw 1.5708** (`clear_hostiles` first: the fair is outdoors).
Needs key 58. "Is that so?  Perhaps you would like to have a contest?" / "Yes." / "If you wish." / "Alright, ask your
questions." / "Sturmford and Drangheim" / "Verhoffin." / "Hallenhalt." / "Hubris." / "Making Magic Items." / "He was
murdered by his personal guards." / "Alright, let's have it." / "Ivan the Smart" (key 60) / "As a token of good faith,
we'll let you live." / "See you around." The close: key 164, +5 000, item **10400** (Victory Certificate). A wrong
answer goes to "We lost?" / "Gee, thanks." and ends the contest.

## 29: Ta'Sar Academy (`j_tasar`, `k_books`, `l_books`)

**The academy is hostile** (all 16 guards and students, the teacher, Dook's two captains: the user's decision of
2026-11-08, README "can the party reach"). `clear_hostiles: 2000` on the walks killed 17 on the way in; none
afterwards. The guide's "friendly" is out of date.

**In** (doors are pairs that slide; a click toggles them, and `walk_to`'s own stuck-click clicked door 109 open and
then shut again: click doors explicitly):
planned `walk_to (3400, -60)`; `click(109)`, wait 2; `walk_to (4300, -60) plan false` (the trophy room); planned
`walk_to (4950, -800)`; `click(106)`, wait 2; `walk_to (4950, -1300) plan false`; planned `walk_to (3600, -6550)`
(10 s, 11 killed); `click(105)`, wait 2; `walk_to (4300, -6550) plan false` (east hall); planned
`walk_to (4250, -7450)`; `click(110)`, wait 2; `walk_to (3500, -7450)`, `(2550, -7450)` plan false; `click(112)`,
wait 2; `walk_to (1800, -7450)` plan false; `walk_to (1500, -7950, radius 80)` (beside the Start table (1230, -7828)).

**The library** (round tower, ground z 0, first gallery 533, top gallery 1065; galleries are rings with railings
round the open middle; a central column holds the ladders, reached at ground level only from its east or west side,
y -7578..-7332):

| Table | Event | Where (stand) | Book (take event at the Start table) | Keys |
| --- | --- | --- | --- | --- |
| Offense | 220 | first gallery, north (1281, -6500) | 230: item 10435 "Weapons of the Ursanian Empire" | 9501, 9517 |
| Strategy | 221 | top gallery, west (480, -7650) | 231: 10436 (needs 9517) | 9502, 9518 |
| Defense | 222 | first gallery, south (1312, -8400) | 232: 10437 (needs 9518) | 9503, 9519 |
| Intelligence | 224 | top gallery, east (2216, -7650) | 233: 10438 (needs 9519) | 9504, 9520; with all four 9516, LibraryDoor opens |

- Up to the first gallery: `walk_to {via: [[1600,-7700,0],[1600,-7450,0],[1300,-7450,0]], x: 1269, y: -7330,
  plan: false}`; Ladder0 `start (1269, -7330, 0) yaw 90`, end yaw 180, 8 s: ends on the first gallery's west side
  (324, -7134, 532) after crossing the west bridge.
- Up to the top: `walk_to (1269, -7540, 553) plan false` (the column's south half); Ladder1 `start (1269, -7540, 553)
  yaw 270`, end yaw 0, 8 s: ends on the top ring's east side (2216, -7776, 1065).
- Down: top column hole (1270, -7590) -> first gallery column; first column hole (1270, -7320) -> ground; each
  `walk_to ... radius 20, plan: false` then `advance_runtime 2`. On the ground leave the column eastward:
  via (1300, -7450), (1600, -7450), (1600, -7750).
- Ring paths used: first gallery north `via (1150,-7450),(850,-7450),(650,-6900),(900,-6450)` to (1281, -6500);
  south `via (450,-7800),(700,-8300)` to (1312, -8400); top ring clockwise `via (2100,-8100),(1700,-8450),
  (900,-8450),(500,-8100)` to (480, -7650) (anticlockwise sticks on the Intelligence table at (2073, -7443)).
- A book is taken only if the one before it lies on its table; a table takes every textbook carried.
- With 9516, LibraryDoor (south of the top ring) stands open: `walk_to {via: [[2100,-8100,1065],[1700,-8450,1065],
  [1270,-8450,1065],[1270,-8800,1065]], x: 1250, y: -9150}`; the scroll is event **269** (a SimpleMessage: "Blf xzm
  urmw gsv Yllp lu Ifovh yvsrmw gsv ilgzgrmt yllphsvou rm gsv mvcg illn."; reversed alphabet: "You can find the Book
  of Rules behind the rotating bookshelf in the next room."); `press_action: escape` closes it.
- Down again, then the stairs south: `walk_to {via: [[1300,-7450,0],[1600,-7450,0],[1600,-8100,0],[1270,-8450,0],
  [1270,-8700,100]], x: 1270, y: -9350, z: 329}`; `walk_to (245, -9354, 329)`; **the bookcase's book: event 201**
  (BookButtonFront1; the bookcase turns 180 degrees, buttons back after 5.5 s); `wait(6)`; `walk_to {via:
  [[0,-9450,329]], x: -1017, y: -9474}`; **the Book of Rules: event 270**: item **10391**, key **59** (with 57),
  +5 000.
- Out: not run end to end; the reverse of the way in (doors 112, 110, 105, 106, 109) to the exit at (2621, 1065).

## Keys and items for asserts

| Key | Meaning |
| --- | --- |
| 2, 3, 30 | Sven's Thjorad task, mine task, the clans line |
| 9509 / 36 | Ketil's directions / the hard rock (+5 000) |
| 9510, 9511 / 35 | Gudrek's lead started / arrived / the cave-in (+5 000) |
| 5 / 360-363 / 362 | Njal sends for Hjarrand / Hjarrand's offers / paid |
| 9512 / 9513, 9514 / 364 / 37 | broken part taken / Gunnar's swap / Hjarrand's mark / part installed (+5 000) |
| 9507 / 31 (162 if taken before Sven asked) | bells / Thjorad taken |
| 32, 33, 34, 163, 177 | Sven: Thjorad handed over, mine reported, joined, the two rewards |
| 56, 57, 58 | Markel: the clans, task 1, task 2 |
| 60, 164 | Ivan beaten, his reward (item 10400) |
| 9501-9504, 9516-9520, 59 (166 without 57) | library tables, the door, the Book of Rules |
| 61, 62, 63, 165, 167 | Markel: book, Ivan, joined, the two rewards |

Items: 10197 Thjorad, 10398 Broken Slag Extractor, 10399 Slag Extractor, 10435-10438 textbooks, 10391 Book of
Rules, 10400 Victory Certificate. Clans counted for the council (key 178): 82, 38, 51, 63 (Markel), 74 at Sven; 82,
38, 51, 34 (Sven), 74 at Markel.

## Risks

1. **Ladders** (monastery x3 up, Ta'Sar x2 up, twice each): only `movement_segment` climbs; fixed-yaw climbs are not
   repeatable (the party walks on into the hole); the turning climbs above were. Descents are falls through holes;
   the hole rectangles above leave about 35 units of play for the party's radius 37.
2. **Paced NPC**: Gudrek stops whenever the party is 655 away; walk 400-800 at a time with 8 s waits.
3. **Actors in narrow places**: the miner at the cave-in corridor's mouth, Gudrek in the cave-in room's mouth, Njal
   in the tank's floor channel, Hjarrand in the corridor west of Door0, monk 13 on the nave's centre line. All
   handled by the via points above; NPCs may move after map loads.
4. **The refinery spiral** (both directions) and the cavern tunnel: the planner's routes are partial or wrong; keep
   the via lists.
5. **`walk_to` clicking doors**: a stuck walk clicks what is ahead, which toggles a door pair shut again (Ta'Sar 109)
   or opens nave doors unasked. Click every door explicitly.
6. During this research another session rebuilt the binary twice: for a few minutes every scenario segfaulted at
   `load_game`/`load_map`, then `mm9_common.lua:126` called `SetGlobalVar` before the binary that registers it was
   linked (`click(131)` failed: "attempt to call a nil value (global 'SetGlobalVar')", MM9.takeItem). Both cleared
   after the rebuild finished; rerun anything that fails that way.

## Suspected bugs

1. **Hjarrand's pacing stalls** (fixed 2026-11-08: the monsters' walk map left out the faces of every `ai_open` door,
   open ones too, so his route back to MMarker1 ran into the slag extractor's hatch, RotatingDoor0, which the party
   leaves open across the corridor; an open `ai_open` door now stands in the walk map,
   `IndoorPathfindingBuilder::buildPathMap`; `tests/scenarios/mm9/hjarrand_walks_past_open_hatch.yml`). After "Is the
   machine fixed yet?" he walked MMarker1 -> MMarker2 and then stood at (-2663, 1083) short of MMarker1 (-2570, 1085)
   with HjarrandStop 3 for 150 s; key 364 never came (`g_mine5` with a 150 s wait). No wall there (faces_near shows
   only floor); maybe the arrival test never fires. Clicking him after that opened no dialogue at all
   (`interact_actor: 45` hit him, then "the dialogue offers:" was empty), so "Thanks for your help." could not be
   picked. The quest itself does not need him (key 37 comes from the base).
2. **Journal labels on MM9 keys look wrong**: the assert lines print `qbit_set[90002] "Search for anyone living on
   this island. The Isle of Ashes..."`, `90030 "Slay the Dragon. The first step..."`, `90031 "Slay the Dragon. The old
   man put you on the path..."` for Sven's task keys (cosmetic, label lookup only).
3. Not a bug but worth knowing: the planner's route to Ketil runs into a wall (a waypoint at (3232, -2197) by Sign1),
   and its route into room 47/30 from room 49 needs the planned leg; the monsters' path map has gaps in this mine.

## Guide errors (`tools/mm9_site/story/ch1b.yml`)

- Mine: the obstacle out of the cavern is the **cave wall** ("Rock", event 102) at the tunnel's top, then **BarWall1's
  six spikes** (76-81) on the stub from the loop to the refinery's north door; the long tunnel does not reach the loop
  directly (room 58 -> 54 -> 49 -> 47 -> 30 -> 43 -> 55 -> the loop 56).
- Lindisfarne's compass is mirrored in our build: the dock is in the west (-23123, -333), the **monastery in the far
  south** (-11749, -21240), **Ta'Sar in the north-east** (12889, 21932); the guide says north and south-west.
- The Gathering is north-west of Guberland's dock, not south.
- The academy is hostile now, not friendly.
- Sven's and Markel's rewards come when the talk closes ("Goodbye."), not on the joining line.
