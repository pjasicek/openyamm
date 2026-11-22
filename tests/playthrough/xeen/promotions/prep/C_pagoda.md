# Block C: Q-C4 The Ninja Pagoda (T1-D, Monk -> Initiate)

Segment `21_kaiwu_pagoda.yml`. Start: `checkpoints/00_main_33.oysav` (main 33: X5's east pocket at (6915, -9472)
after the Cave of Illusion; the party Cavalier Crusader Wizard Hunter, no Monk). Quest logic:
`assets_dev/worlds/xeen/source/quests/q-c4.yml`; map: `devdocs/xeen/briefs/xd22/L4/` (playtest.yml, playtest_exit.yml,
ids.lock.yml, NOTES.md, diagram.txt); X5: `devdocs/xeen/briefs/x5/L4/` (ids.lock.yml, NOTES.md, playtest.yml).

## X5

- **Kai Wu's Monastery** (house 4270, `building:monastery_training`, X5 event 35; owner Kai Wu 4521) on the crag west
  of the Frostspine. Placed at (1280, 16660, 1888) facing north (yaw 1.5708), `press_interact` opens the house: two
  lines, "Kai Wu, Master of the Monastery" (training to 40) and "Kai Wu" (his topics). Pick "Kai Wu", then:
  - **The Pagoda** (n 1): first "I am a peace loving old monk driven from my sacred home ..." sets `started` 112080;
    with `clan_master_slain` 112081: "You have destroyed the Ninja Clan ..." sets `done` 112082, clears `started`,
    `AddValue(Food, 20)`, 8,000 + 8,000 experience each, `{promote: pagoda}`; once done: "The pagoda is quiet
    again ...".
  - **Initiation** (n 2): shown with `done` and a Monk in the party (`promotable: pagoda`); promotes, unpaid.
- **The pagoda's north door** (`thing:pagoda`, X5 event 61, its panel at (320, 9472, 1120)): placed at
  (320, 9728, 992) facing south (yaw -1.5708), `press_interact` moves into `xeen_xd22.blv` at (0, -256, 0).
- **Out**: XD-22 event 21 (`evt:north_door`, "Winterkill Tundra", an OK prompt) lands at (320, 9872, 1000) facing north.
- On the first load X5 reports "Winterkill Tundra has changed since this save: it starts afresh" (X5 rebuilt since
  main 33's save; the map's state resets, party kept).

## XD-22 (storeys 0, 512, 1024, 1536, 2048; cellar -448)

| Step | Where | How |
| --- | --- | --- |
| entry hall (2 Ninja) | (0, -600, 0) | walk, clear |
| kitchen door | event 14, door 5, the leaf at (-568, -543) | `open_door(14, 5)` from (-400, -543, 0) |
| kitchen (2 Ninja) | (-1000, -500, 0) | walk, clear |
| kitchen ladder | scene ladder `kitchen`, foot (-666, -384, 0), top exit (-520, -384, 512) | `climb` up (and down on the way out) |
| dojo (5 Ninja) | (-100, -900, 512) | walk, clear 1300 |
| west stair | (-896, -450, 512) -> (-896, -800, 512) -> (-896, -1520, 990) | walk |
| Hall of Screens (maze) | (-560, -1520) -> (-560, -1240) -> (290, -1240) -> (290, -1500) -> (672, -1530), z 1024 | walk |
| crane screen | event 11: destroys destructible 1, "The paper tears ... a stair climbs into the dark." | `click(11)` |
| crane stair | (672, -1200, 1040) -> (672, -700, 1480) -> (360, -700, 1536) | walk |
| armoury (2 Shadow Ninja) | (-200, -760, 1536) | walk, clear 450 (the clan master's hall is right above) |
| door to the moon gallery | event 12, door 1 | `open_door(12, 1)` from (-680, -752) |
| moon gallery (2 Ninja) | (-1010, -752, 1536); event 16 its status line | walk, clear 450 |
| top stair | (-1010, -1184, 1536) -> (-700, -1184, 1536) -> (60, -1184, 2010) -> (60, -960, 2048) | walk |
| clan master's hall | Clan Master (actor 2, row 11123, group 21) at (200, -840, 2096); Ninja Master (actor 15) | the kill timer (event 10, every minute: `CheckMonstersKilled` actor 2, MapVar 2) runs `q-c4.clan_master`: `clan_master_slain` 112081 |

The way out is the way up in reverse (the gallery, the door, the armoury, the crane stair, the maze, the west stair,
the kitchen ladder down), then the entry hall's north door (walk to (0, -120, 0), `execute_event: {id: 21}`, OK).
The clan's rope (scene ladder `rope`, foot (986, -1568, 1024), `grab_in_air`) is not used: a party walking west from
its foot is caught by it and carried back up to the gallery (2026-11-21).

## Kill radii

The run's `clear_hostiles` counts the horizontal distance and the height separately against the radius; storeys are
512 apart, so radii of 1,200-2,000 on the ground floor also kill the second and third storeys' ninjas (as the map's
playtest). They never reach the clan master (2,048 up). In the armoury and the gallery the radius is 450.

## Found

- **ISSUE A7 XD-22** (logged in the segment): the Clan Master (actor 2) dies by himself within 4 s after the armoury's
  door to the moon gallery (event 12, door 1) opens, with nobody near him; a probe that waited 8 s in the armoury with
  the door shut kept him alive. Every clear's kills are logged and none reaches him. The kill timer then sets
  112081, so the quest goes on, but the party finds his hall empty. Suspect: his AI leaves the dais for the party
  through the open door and falls off the open gallery (or out of the map). Owner A7 (XD-22).
- The hook's text ("The clan master falls. You have dishonored the Ninjas ...") is not seen on the status line.
- Food (+20) is not asserted: `play_lua` has no food reading.

## Shinobu (T2-clan, Act IV; not in this block)

After `q-c4.done` the pagoda's hostile ninjas are hidden and Shinobu (NPC 4530, actor 24, a Clan Survivor 11124)
with four survivors stands in the cellar (the shrine hall's mat, event 18, opens the hatch; scene ladder `cellar`,
foot (0, -1626, -448), top exit (0, -1520, 0)). Her topic "The clan" promotes Initiates to Ninjas once
`m20.started` (t2-clan.yml); Kai Wu's after-line mentions her ("Someone lives in the cellar").
