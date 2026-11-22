# Prep: Q-C4 The Ninja Pagoda (with T1-D)

Scenario `q-c4_ninja_pagoda.yml`. Quest file `source/quests/q-c4.yml`; generated `events/common/xeen_quests.lua`
(topics 42701 "The Pagoda", 42702 "Initiation"; hook `q-c4.clan_master`); promotion `Xeen.Promotions.pagoda =
{Monk = "Initiate"}` (`xeen_common.lua:80`); quest stub `tools/xeen/quest_stub/act3_cloudside.yml`. No story
precondition. Routes: X5 L4 playtest (monastery, pagoda door), XD-22 L4 playtest and NOTES.

Routes in the source: one (drive the clan out). Siding with the clan is T2-CLAN (`t2-clan.yml`: Shinobu in the cellar
after `q-c4.done`, Initiate -> Ninja once `m20.started`), a separate Act IV promotion already prepared by the
promotions chain (`tests/playthrough/xeen/promotions/prep/C_pagoda.md`); not played here.

## Getting there

| from | how | to |
| --- | --- | --- |
| X5 | stand (1280, 16660, 1888) yaw pi/2, use | Kai Wu's Monastery (house 4270, Kai Wu NPC 4521) |
| X5 | stand (320, 9728, 992) yaw -pi/2, click 61 "The Ninja Pagoda" | XD-22 porch (0, -256, 0), arrival line "The barred door gives way..." |
| XD-22 | north door event 21 from (0, -120, 0), "OK" | X5 (320, 9872, 1000) |

## Kai Wu (house 4270, line "Kai Wu", then "The Pagoda")

- first: "I am a peace loving old monk driven from my sacred home..." sets started 112080;
- with started: "There are still Ninja in my Pagoda...";
- with clan_master_slain 112081: "You have destroyed the Ninja Clan..." sets done 112082, clears started, Food +20,
  8,000 XP each, `Xeen.promote("pagoda")` (Monk -> Initiate), 8,000 XP each again (16,000 in all);
- with done: "The pagoda is quiet again. I sweep it every morning..."
- "Initiation" shows only with done and a Monk left (`Xeen.canPromote("pagoda")`): absent for a party with one Monk.

## XD-22 walk (storeys 512 apart)

Ground: porch (0, -600), shrine door event 15 / door 6 at (0, -880), shrine hall (0, -1350), east stair
(1120, -1300) -> (1120, -950) -> (1120, -300, 480) up to the sleeping loft (820, -320, 512). The loft's sliding door
event 13 / door 3 (with leaf 9) at about (448, -1400, 512) into the dojo (200, -1400). The dojo's north wing holds the
kitchen hatch, a hole x -896..-656, y -512..-256 over the kitchen ladder: pass it on its south side, (-450, -544) and
(-990, -544) straight, into the west stair (-896, -800) -> (-896, -1520, 990) -> Hall of Screens (-560, -1520, 1024).
Maze: (-560, -1240), (290, -1240), (290, -1500), (672, -1530); crane screen event 11 (destructible 1, "the crane falls
away"); crane stair (672, -1200, 1040) -> (672, -700, 1480) -> (360, -700, 1536); armoury (-200, -760); armoury door
event 12 / door 1 (leaf 8) at (-680, -752); moon gallery (-1010, -752) -> (-1010, -1184); top stair (-700, -1184) ->
(60, -1184, 2010) -> top hall (60, -960, 2048): Ninja Master actor 15 and Clan Master actor 2 (monster 11123).
The kill timer (event 10, every 2 s) on actor 2's death: hook q-c4.clan_master, 112081, message "The clan master
falls. You have dishonored the Ninjas...". Down the same way, the kitchen ladder (`climb: kitchen, down`), the kitchen
door event 14 / door 5 (leaf 10), out by the porch (via (-700, -640), (-300, -640); the planner finds no route through
the kitchen door).

## Runner traps found

- `clear_hostiles` and `walk_to`'s clearing measure 2D distance and |dz| against the same radius; with storeys 512
  apart a radius over 512 kills the floors above. `open_door()` clears 1500 while it waits, so at the armoury door it
  killed the Clan Master on the storey above (hook fired with the party a floor below). The scenario clears 480 and
  clicks doors by hand below the top storey.
- The gallery's rope ladder (`climb: rope, down`) works, but walking on west from its foot runs back into the rope and
  climbs it again: the scenario returns by the crane stair.
- A walk across the kitchen hatch drops the party into the kitchen when it is slowed there (seen in the reload run).

Rewards asserted: done 112082 and clan_master_slain set, started cleared, food 20 -> 40, +16,000 XP (member 1),
classes "Initiate Cleric Knight Sorcerer", no Initiation topic. No autonote in this quest; no journal assert form.
