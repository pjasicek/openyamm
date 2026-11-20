# Block A: Gladiator labours, Mercenary, Champion (segments 01-15)

Research for `01_fridleif_labours` ... `15_champion`. Guide: `tools/mm9_site/story/side_a.yml` (kill-a-basilisk,
get-kira-s-shield, win-in-the-arena), `side_b.yml` (speak-to-atli-sigmundssen, guard-atli-sigmundssen-s-boat).
Keys are MM9 raw keys (qbit = 90000 + key). Start: `00_start.oysav` (Yorwick, Chapter II, 8:28 AM; Knight Cleric
Thief Sorcerer; gold 75 809; experience 443 965 / 413 825 / 413 825 / 420 980). No class from another block needed.

## Route

| Seg | Leg | Ends on |
| --- | --- | --- |
| 01 | travel Sturmford, land gate, Fridleif: labours taken (214) | sturmfordcity |
| 03 | north gate out, a basilisk outside Anskram Keep killed, skin from its corpse | sturmford |
| 05 | travel Thronheim, land gate, Kira's council room door, the shield picked up (216) | thronheimcity |
| 07 | travel Thjorgard, west gate, Arena; Lord fight won (217); out | thjorgardcity |
| 09 | travel Sturmford, Fridleif: three hand-ins, completion (218-220, 26, 221): rewards, nobody promoted | sturmfordcity |
| 11 | travel Thronheim, Thorfinn: the errand (124) | thronheimcity |
| 13 | travel Guberland, Atli (125), the dock watch 2:45-6:00, Atli's reward (127): Cavalier, Rogue | guberland |
| 14 | travel Thronheim, Thorfinn: "Atli's on his way", "Promote our eligible characters." finds nobody | thronheimcity |
| 15 | travel Sturmford, Fridleif: "Promote our eligible characters." Cavalier -> Champion, no pay | sturmfordcity |

## Sturmford City (sturmfordcity.blv)

- In from the region: `sturmford.blv` ExitTrigger0 at (7608, -3312, 543): placed at (8090, -3312, 252) yaw pi, walk
  west, prompt "OK". Out: ExitN (11346, 14541, 19907): placed at (11000, 14541) yaw 0, walk east, "OK" ->
  `sturmford.blv` (8090, -3312).
- **Fridleif Gjukissen**: actor 31, RUDE 61, (5775, 4603, 20565), the town hall's upper floor, facing west; the party
  is placed at (5560, 4603, 20565) yaw 0.
- His click (handler 53833, NPC61.scr): with 214 and item 380 or 591 in the packs gives key **215** (the skin row
  needs it, so the skin must be carried when the talk opens), then the talk. Close (handler 50833): with 26 and not
  221 -> key 221, 37 500 experience to every member, 5 000 gold (MM9 63 000 experience, scaled),
  `MM9.promoteParty("Gladiator")`; with 219 takes Kira's Shield (375). The skin is not taken.
- Dialogue (node 61 = first page): "We have heard that you can promote Mercenaries." (forbidden by 26) -> "Yes, we have
  members who would like to be Gladiators." (needs 127: waived, `dialogue/promotions.yml`) -> node 14: "What is the
  first/second/third labor?" (with "Where can we find the Basilisk?", "What do you want us to do?", "Where is the
  Arena?") and "We shall do all of these things." (214). Hand-ins on the first page: "We have the Basilisk Skin" (215
  -> 218), "We have Kira's Shield" (216 -> 219), "We have won in the Arena." (217 -> 220), each to node 60: "We've
  completed all the labors." (218, 219, 220 -> 26) or "Thanks.". promotions.yml adds the completion row to his first
  page too. Once 221 (done key 26 -> the service), his first page keeps "Promote our eligible characters." (event 49990):
  "<name> is now a Champion." or "No one among you can take this promotion now.".

## The basilisk (sturmford.blv)

- Basilisks (monster 9150) outside Anskram Keep's front (start point Abandonedfortfront 15135, 16677): actors 15
  (18821, 17168), 72 (19082, 17191), 17, 74 (20459-20504, 16677-16935), 16, 73 (18739-18882, 20199-20484). All six
  alive at 00_start. Placed at (18300, 17168, 1154).
- `mm9_common.lua` RegisterMonsterKilledHook 49991: a killed 9150/9151/9152 without 215/218 and with no skin in the
  packs gets item 10380 (10591 for a King) as its corpse item. `combat_loot: {actor_index: 15, expected_item_id:
  10380}` (the party's blow, then a click on the corpse) takes it.

## Kira's Shield (thronheimcity.blv)

- In from `thronheim.blv` ExitTrigger2 (1392, 6498): placed at (1392, 6100) yaw pi/2, walk north, "OK".
- The palace is part of the city map, not an interior map. Kira's council room (Kira actor 41 at -11182, 16865) has a
  double door on its south side (KiraDoor1/2, door ids 9, 10, event 232, at y 15493, x -11376..-11151); the hallway
  is south of it. At 00_start the door is open (the war council left it open); the segment clicks 232 only when it is
  shut. Clicking 232 with keys 90 and 91 and without 40 would start the war council: not in Chapter II.
- The shield is a world item (`world_items`, item 10375 at (-11981, 15443, 3277)): pickable only with 214, sets 216
  (KIRASHIELD.scr). Route: placed at (-11264, 15800) yaw -pi/2, walk through the door (via (-11264, 15350)) to
  (-11800, 15400), `pick_up` (distance about 250).
- Planner trap: a target at (-11800, 15443) or (-11981, 15530) from inside the council room routes along its south
  wall and sticks at (-11870, 15650); go through the door.

## The Arena (thjorgardcity.blv, thearena.blv)

- In from `thjorgard.blv` ExitTrigger2 (-8790, 4392): placed at (-9300, 4392) yaw 0, walk east, "OK". The Arena's
  entrance Arenaexit (9912, 11141, 205): placed at (9585, 11141, -19) yaw 0, walk east, "OK" -> thearena.blv
  (0, -3686). Out: ExitTrigger0 (0, -3891), "OK" -> thjorgardcity (9585, 11141).
- Arena Master: actor 0, RUDE 430, (-328, -3441). "We're here to fight." (forbidden by 1011, 1009, 1017, 1018) ->
  "We're the best there is!  Send us in at Lord!" (1007). Close (handler 50012): `prepareFight(4)`: 1-5 opponents
  at 1.0-2.5 x the party's mean level, map var Lord = 1 with key 214, key 1011, Waiting = 1. With 230 and without 231
  (Grehgknak's Sven crusade, block E) he holds no fights: block A must not come after 230 is set.
- Double doors RotatingDoor0/1 (door ids 1, 2, event 100) at y -1536, auto-close 5 s. The PlayerInTheHouse box
  (-118..138, -1390..-1134) starts the fight (doors locked, opponents from the pens at x +-1720). The last death
  (event 130) gives 1020, unlocks, cheers. "We won!" (needs 1020) -> close: fightWin(): Lord -> key 217, no purse.
- Walk: (-150, -3441) to the master, (0, -1800), click(100), (0, -1000), clear_hostiles 5000, click(100) back.

## Thorfinn (thronheimcity.blv)

- Actor 6, RUDE 240, (11851, 2244, 3124) in the tavern, facing north; placed at (11851, 2440) yaw -pi/2.
- "We'd like to know about promotions." (forbidden by 124) -> "We have." -> "We will do this." (124). After 127:
  "Atli's on his way to Thronheim." and the service "Promote our eligible characters." (done key 127).

## Atli Sigmundssen (guberland.blv)

- `travel` lands at the dock; Atli actor 54, RUDE 186, (11563, 11577, 121) north of the Gathering, facing north;
  placed at (11563, 11780) yaw -pi/2. "We've come to guard your boat." (needs 124) -> 125.
- The watch (guberland.lua 69-197, poll every 3 s, handler 600): the late guard actor 56 at the post (18116, 4860).
  Between 2:45 and 3:15 (key 376) a party within 1966 of the post relieves him (197), he walks off. Raid at 3:30
  (relief time + next 3:30): 3 Bandits (9101) and 3 Cutpurses (9099) at (10580, 8137) run to the dock; alive at 5:30
  -> the night fails (197 taken). All dead -> at 6:00 key 126, Atli, his daughter and the guard walk to the dock
  (17461, 4696) (AtliComing 1 -> 0 on arrival, about 40 s). The rest alarm (evt.SetRestAlarm) stops a wait near the
  dock or post at 2:45, 3:30, 5:30 and 6:00.
- Played: placed at (17900, 4700, -100), 4 s, `rest wait 1440` (stops 2:46), `rest close`, relieved; `rest wait 240`
  (stops 3:31), the raiders come in about 20 s, clear_hostiles; `rest wait 240` (stops 6:01): Atli comes.
- At the dock: "Good luck on your journey." (needs 126, not 127) -> "Yeah." closes: handler 50085: 127, 16 500
  experience each, 1 000 gold (MM9 24 000 experience), `MM9.promoteParty("Mercenary")`: Knight -> Cavalier, Thief ->
  Rogue. Atli, his daughter, the guard and the ship are gone on the next load.

## Measured in the chain from 00_start

- Labours: +5 000 gold (75 933 -> 80 933), +37 500 experience each, classes unchanged.
- Mercenary: +1 000 gold, +16 500 experience each, "Cavalier Cleric Rogue Sorcerer".
- Champion: no gold or experience, "Champion Cleric Rogue Sorcerer"; end gold 81 933, sturmfordcity, Basilisk Skin
  (10380) still in the packs.

## Guide errors (side_a.yml, side_b.yml)

- kill-a-basilisk `requires` the Mercenary promotion: waived since 2026-11-08 (promotions.yml); stale.
- get-kira-s-shield "Click it": the shield is a world item now (picked up); the hallway is reached through the
  council room's south door, or from the palace's own entrance.
- speak-to-atli-sigmundssen "he does not walk to the dock here", "go back to Atli where he stood": wrong. At 6:00 the
  watch's poll walks Atli, Hungerda and the guard to the dock (guberland.lua 181-183); he is talked to there.

## Bugs found

- **Arena save/load** (reported to the coordinator): `thearena.lua` handlers[1] (map load) runs on a save load too:
  reset() takes 1004-1019, clears Lord/Waiting/FightGroup, hides the groups, unlocks the doors. A save and load after
  the Arena Master's talk cancels the fight; after a win it loses 1011 so "We won!" pays nothing and gives no 217
  (recoverable by fighting again). The fresh start is a documented deviation (`mm9r_thearena/README.md` "Saving
  mid-bout"); the lost win is the bug. Needs an engine signal for a save load plus a converter change. MM9 used :Main / :OnPostStartWorld, not OnPostSaveLoad. `run.py --reload 07`
  fails at its assert of 91007/91011.
