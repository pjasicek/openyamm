# Block C: Healer and Priest (segments 20-26)

Research for `20_tjolnir_hag_hair` ... `26_slemnir_priest`. Guide: `tools/mm9_site/story/side_b.yml`
(heal-nutty-nurtigan, find-a-new-priest-for-the-new-temple, find-a-new-tree-of-life, learn-the-ritual-of-consecration).
Keys are MM9 raw keys (qbit = 90000 + key). Start: `00_start.oysav` (Yorwick, Chapter II, 8:28 AM; Knight Cleric
Thief Sorcerer; gold 75 809; experience 443 965 / 413 825 / 413 825 / 420 980; key 73 set, the Frosgard boats run).
No class from another block needed: the Cleric is member 1.

## Route

| Seg | Leg | Ends on |
| --- | --- | --- |
| 20 | travel Guberland (5 days, a draft value), gate, Tjolnir (2083 -> 206), Skarphedinn (478), out to the Hag's stool, the Lock of Hair picked up, back: handed in (207, 208) | guberlandcity |
| 21 | the rest screen's Wait 130 min (209), the potion (210, 373, item 558), the sickroom door, Nurtigan (211), Tjolnir (212, 213): Cleric -> Priest, +16 500 each, +1 000 gold | guberlandcity |
| 22 | Tjolnir's "Promote our eligible characters." (nobody now); Gray Slemnir's three tasks (2084, 259, 250-252) | guberlandcity |
| 23 | travel Lindisfarne (The Flying Bird, Monday, 3 days), the monastery walked to Abbot Leffery (253), the rest screen's Wait 24 h (254 at the first 5:00), Robert Aefgil in the yard (255), out | lindisfarne |
| 24 | travel Frosgard City's docks (7 days: The Dragon to Thjorgard, the Sea's Fang on), Nath'i A'Mor (257, 258, item 430, +5 000 each) | frosgardcity |
| 25 | the city gate, the Ruined Temple walked: the Tree of Life (256, item 241) and out | frosgard |
| 26 | travel Guberland (The Racing Fire, 6 days), gate, Gray Slemnir (260, 261): Priest -> PriestLight, +37 500 each, +5 000 gold, items 241 and 430 taken; his "Promote our eligible characters." (nobody now) | guberlandcity |

Promotions are checked with `play_lua` `remember`/`recall`: the classes, every member's experience and the gold before
the talk; after it each member must hold `MM9.Promotions`' target of its class before (or that class), the Cleric
(member 1) must be the target, every member must have gained the reward exactly, and the gold must have risen by the
reward. Nothing is hard-coded to members 0, 2, 3.

## Guberland City (guberlandcity.blv)

- In: `guberland.blv` ExitTriggerGuberland (6131, -9194, 1651): placed at (6131, -9700, 1651) yaw pi/2, walk north,
  "OK" -> (-655, -287, -9). Out: ExitTrigger0 (-655, -41, 307): placed at (-655, -287, -9) yaw pi/2, walk north, "OK"
  -> `guberland.blv` (6151, -10359, 1411). (The guide's "north gate" is this one gate.)
- **Tjolnir the Super-neat**: actor 11, RUDE 128, (-4751, -6717, 62), the temple (west side; its door TempleL/R 125).
  Placed at (-4751, -6950, 62) yaw pi/2. Click 53813 opens RUDE 128; close 50813 (`guberlandcity.lua:136-139`): with
  2083 gives 206; with 212 and not 213: key 213, 16 500 experience to every member (MM9 24 500, the XP profile), 1 000
  gold, `MM9.promoteParty("Healer")`.
  Lines: "We are seeking promotion from Initiate to Healer." (grants 2083, forbidden 211) / "We have worthy
  Initiates." / "What do you want us to do?" / "We will take this quest." (closes). Report: "We've healed Nurtigan."
  (needs 211, grants 212) / "Thank you." / "Goodbye.".
  After 213 his first page shows "Can we ask you some questions?", "Promote our eligible characters.", "Sorry to bother
  you."; with nobody eligible the topic answers "No one among you can take this promotion now." and stays.
- **Skarphedinn Njalssen** (Eye of Newt): actor 19, RUDE 142, (2499, -12575, 1); placed at (2499, -12800, 1) yaw pi/2.
  Click 53821: with item 240 in the packs and 206, key 207. Lines: "We've come to speak to you about Nutty Nurtigan."
  (needs 206, forbidden 207) / "We need a way to cure him. Tjolnir told us you might help." / "It will be done.  Where
  can we find the Old Hag?" (478) / "Goodbye.". With the hair: "We've got a lock of the hag's hair." (207 -> 208) /
  "Thank you." / "Goodbye."; close 50821 takes item 240 and sets map var PotionReadyAt = now + 120 min; the map's poll
  (timer 260, every second) gives 209 once that passes (the city must be loaded). Then "We've returned for the
  potion." (209 -> 210) / "Thanks." / "Goodbye."; close: item 558 (the potion, 10558), key 373.
  His wares close 20:00-06:00 (key 5017); his Nurtigan rows do not care.
- **Nurtigan's sickroom**: RotatingDoor3 (door 68) at x -420, y -8008..-7916 (Markel's palace, the Idiot's Box); click
  event 231: locked ("The door is locked.") until 373 or 211. Placed at (-250, -7962, 11) yaw pi, `click(231)`.
- **Nutty Nurtigan**: actor 44, RUDE 131, (-471, -8090, 11). "Here, Nurtigan.  Drink this." (needs 210, forbidden
  211) / "Feeling any better?" (211) / "Promise us you'll not try to woo every girl you meet." / "Goodbye."; close
  50871 takes item 558 and opens the door.
- **Gray Slemnir**: actor 9, RUDE 129, (-6226, -6226, 1), same temple; placed at (-6226, -6450, 1) yaw pi/2. Lines:
  "We are seeking promotion." (2084) / "We would like to be promoted." (needs 213 in MM9: waived by
  `dialogue/promotions.yml`; grants 259) / "What is the first thing?" (250) / "Where are we to find a new priest?" /
  "What is the second thing?" (251) / "What is the final thing?" (252) / "Where can we find him?" / "We will do these
  things." (closes). Close 50811 (`guberlandcity.lua:145-153`): with 2084 gives 250-252; with 260 and not 261: key
  261, 37 500 experience each (MM9 63 000), 5 000 gold, items 241 and 430 taken, `MM9.promoteParty("Priest")`.
  Report on his first page: "We've completed all your tasks." (needs 256, 258, 255; grants 260) / "Thank you." /
  "Goodbye.". Afterwards his first page keeps "Promote our eligible characters.".

## Guberland (guberland.blv): the Old Hag's hair

- Hjordisa the Hag: actor 40, RUDE 132, (13693, -21027, 103), on the south-east shore (not north-west as the guide
  says). The Lock of Hair is world item `obj_Prop1` (item 10240) at (14066, -21412, 160), no qbit conditions. Placed
  at (13850, -21200, 160) yaw -0.785, `pick_up: {item_id: 10240}` (distance 289). No talk needed; nothing hostile near.

## Lindisfarne Monastery (lindisfarnemonastery.blv)

- In from `lindisfarne.blv` ExitTrigger0 (-11749, -21240, 2734): placed at (-11250, -21240, 2734) yaw pi, walk west.
  Out: ExitTrigger0 (-328, -1393): walk south from (-328, -1000).
- **Monks**: all friendly (`MonksHostile` 0 in the start save, checked on entry and after Robert). Hurting one makes
  all hostile and stops every talk (`lindisfarnemonastery.lua:49-71`); Robert has no hostility. **No
  `clear_hostiles` in the monastery**: nothing hostile lives there; walk_to's monk bumps do not hurt them.
- Doors: nave doors 101 (doors 1, 2, y 1290), crossing doors 102 (3, 4, y 5918), both double, auto-close 10 s;
  nave's east door 103 (door 35, x 635, y 1638-1884) into the yard. Clicked only when both leaves are shut (a click
  toggles each leaf; the start save had the nave doors open, a blind click shut them).
- **Abbot Leffery Caid**: actor 0, RUDE 283, (-425, 11366, 103), the main altar at the north end on the choir platform.
  The platform's front is not climbable in the middle (the walk sticks at (-375, 10354)); its 41-unit side steps are at
  x -831 and x 175 (y 10350). Route: crossing (-100, 6900) -> (175, 10150) -> (175, 10700) -> (-300, 11100).
  Lines: "Actually we're looking for a priest." (needs 250, forbidden 253) / "We need to take a priest to Guberland."
  / "Sounds great!" (253) / "Thank you." / "Not right now." (his page then has no "Goodbye."). Close 50408 sets
  PriestAskedAt; timer 262 gives **254** at the first 5:00 after it and shows Robert (group 3).
- **Robert Aefgil**: actor 2, RUDE 284, (1475, 2458, -40), the yard east of the nave (hidden until 254). Route back:
  the choir's side step, the crossing doors, the nave to (400, 1761), door 103, (1000, 1761), (1475, 2250). Lines:
  "Yes, we are ready to take you if you are ready to leave." / "To a new temple we're helping to build in Guberland." /
  "Alright.  Perhaps we'll see you there.  Farewell." (255; he is then hidden). The abbot's "We've returned for the
  priest." (needs 254, grants 255) is the other way to 255.

## Frosgard City (frosgardcity.blv)

- `travel: {map: frosgardcity.blv}` lands at the docks (4260, -10486, -81). City gate out: ExitTrigger0 (11983, 8146,
  428): placed at (11983, 7700, 0) yaw pi/2, walk north -> `frosgard.blv` (2733, 4536, 1261).
- **Nath'i A'Mor**: actor 15, RUDE 188, (9339, 492, 1), by the corral; placed at (9339, 250, 1) yaw pi/2. Lines:
  "We're looking for a priest." (needs 252, forbidden 257) / "We need to learn the Ritual of Consecration." / "Yes,
  please teach us." / "Great!" (257) / "Thank you." / "Goodbye.". Close 50561: key 258, 5 000 experience each, item
  430 (10430).

## The Ruined Temple (ruinedtemple.blv)

- In: `frosgard.blv` ExitTrigger3 (17960, 20733, 2099): placed at (17550, 20733, 1936) yaw 0 (the temple's own arrival
  point), walk east, "OK" (two hostiles there die) -> (0, -858, -1719), the hall's upper floor. Out: ExitTrigger0
  (0, -512, -1597) in the stub north of the arrival: walk from (0, -858) north.
- Levels: hall upper floor and gallery -1719 (not joined: a wall at y -328), hall floor -2416, main temple -2293
  (sunken middle -2416), east rooms -2273, lift foot / prison / crypt hall -2866, shaft foot -4628.
- Doors (event, door id): AltarDoor 101 (1, 2; y -290); hidden door 201 SunButton (32; y 4200, x -2212; 10 s); Star
  Button 1 210 (west wall x -2580, y 4556), Diamond Button 2 213 (east wall x -1926, y 4628), Main Button 216 (on the
  lift, (-2193, 4580)); PrisonEntrance 102 (44; x -676, y ~4628, 5 s); PrisonButton2 220 (451, 5645); plugs
  38339-38344 (centre (225, 5243), z -3031 ... -4055); PrisonButton3 221 ((0, 6028), the tunnel); PrisonEntrance2 103
  (45; the chest room's south door, x 410-655, y ~4400, 5 s); HiddenButton2 206 ((1631, 3195), opens HiddenDoor3 34 for
  10 s); SunButton3 203 / SunButton4 204 (HiddenDoor2 33, (1802, ~1680), -1719); LeftDoor 207 (35; x ~1014,
  y ~1126-1372; the scene's door vertices are the open pose); UpDoor 104 (54; x -686, y ~-1720, the hall's west wall).
- Route (segment 25): skylight (walk to (0, -1500): FloorFallen, drop to -2416) -> (0, -800) -> (0, -500, -2293),
  click 101 -> (0, 200) -> planned (-2212, 3900) -> (-2212, 4060) click 201 -> (-2212, 4420) -> (-2400, 4556) click
  210 -> (-2100, 4628) click 213 -> (-2193, 4580) click 216 (LiftDown 1; party at -2866) -> planned (-780, 4628)
  click 102 -> (-500, 4628) -> planned (451, 5517) click 220 (CryptOpen) -> (155, 5243) into the crypt, click
  38339..38344 2 s apart (the party drops through each) -> (256, 5888, -4585) -> landing (563, 6323) -> (880, 6050)
  [hop] -> (880, 6656) -> (25, 6676, -3768) -> (-80, 6676) [hop] -> (-80, 6021, -3564) -> (-80, 5940) -> (300, 5940)
  -> (880, 5940, -3359) -> (880, 6676, -3154) -> (300, 6676, -2949) -> (0, 6156) click 221 (slab, cell door, bars)
  -> (246, 6150) -> (246, 6000, -2867) `pick_up 10241` -> (246, 5550) [hop over the slab's sill] -> `climb: Ladder`
  -> (530, 4530) click 103 -> (530, 4250) -> planned (1515, 3260) click 206 -> (1515, 2950) -> planned (1874, 1946)
  (TriggerCaveIn1) -> planned (1802, 1800, -1719) click 203 -> (1802, 1450) -> (1120, 1240) click 207 -> (850, 1240)
  -> planned (0, 200, -2293) -> click 101 if shut -> (0, -800, -2416) -> planned (-560, -1720) click 104 -> (-850,
  -1720) -> planned (0, -858, -1719) -> exit.
- The spiral ramps (from the DAT's polygons, `tools/probe.py`): east strip x 799-963 north (-4237 -> -4014), north
  strip y 6594-6758 west (-> -3768), **west strip x -164..0** south (-> -3564; walking at x 25 falls to the bottom),
  south strip y 5857-6021 east (-> -3359), east strip north (-> -3154), north strip west (-> -2949, the tunnel).
- Hostiles: skeletons, Dagrells, Spectre Dagrells (about 15) die by `clear_hostiles` and the walks' `clear_hostiles`.
- The genie's lamp (241) is not used; the chests are not looted (the packs stay clear).

## Bugs found and fixed

1. **Ruined Temple soft-lock (fixed 2026-11-08, coordinator approved)**: SunButton2 (202) and SunButton3 (203), the
   inner buttons of HiddenDoor and HiddenDoor2, were converted as decoys that do nothing
   (`level_generation/projects/mm9r_ruinedtemple/convert.py`, the hidden doors' Lua). A party that rode the lift down
   (HiddenDoor shuts after 10 s) could only leave by the lift (back to HiddenDoor's inner side) or the ladder and the
   spiral (to HiddenDoor2's inner side): shut in for good with the Tree of Life. In the DAT each inner button is the
   outer one's `DoubleDoorName` pair, and a double door's press moves both (as the converter does for every other
   pair), so each now opens its door like its pair (SunButton3 also unlocks LeftDoor). Converter, scratch build (the
   Lua differs by the fix alone; the scratch scene also differs by a `pickup_qbits: []` line from someone else's
   pending converter change, not installed), installed into `assets_dev` and `output/mm9_rework/assets_dev`,
   `check_mm9_map_lua.py` 0 of 44 before and after. Project README "Deviations" note, `make_scenarios.py` (its
   `scenario_scripted.yml` now checks SunButton2 opening the door; passes), regression
   `tests/scenarios/mm9/ruinedtemple_inner_sun_buttons.yml` (passes).

## Notes and suspected issues (not fixed)

- **Walk hops** (logged as `JUMP` lines in segment 25): the walk needs its stuck-jump at the east ramp's foot
  (762, 6050, -4260; a 23-unit lip), at the north-west landing (-23, 6715, -3768), and from the tunnel (-2929) over
  the escape slab's sill into the cell (-2867, a 62-unit rise). A player can hop these; whether the ramp lips should
  be smoothed is the converter owner's call.
- The rocks of TriggerCaveIn1 fall behind the party in the spiral-room corridor; nothing blocks the way on.
- Waits use the debug console's `rest wait <minutes>` (the rest screen's Wait as its buttons do) and `rest close`:
  130 minutes for the potion, 1 440 for Robert (the party rested from 10:59 to 10:59 the next day; the first 5:00 is
  enough).
- Guide errors: Hjordisa is on the south-east shore, and the city has one gate; "We've completed all your tasks." is on
  Gray Slemnir's first page; the abbot's talk ends with "Not right now." (no "Goodbye."); the way out of the Ruined
  Temple is the spiral, Hidden Door 2, Left Door, the gallery, the main temple, the hall's Up Door and the stair to
  the upper floor (the guide's "out through the spiral room and the main temple" was blocked before the fix above).
- Travel days are the boat tables' (`worlds/mm9/data_tables/transport_routes.txt`); the first `travel` (from Yorwick)
  uses a draft 5 days, for the coordinator to set when linking.
