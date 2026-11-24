# Prep: Q-D2 Jasper in Jail and Q-C24 Joe's Second Business

Scenario `q-d2_q-c24_jasper_and_joes_maps.yml` (one run: Joe's fake map frees Jasper, Jethro trades it for the real
map). Quest files `source/quests/q-d2.yml`, `q-c24.yml`; generated topics in `events/common/xeen_quests.lua` (Jethro
44101 "Jasper" and 43701 "Joe's map", Krupp 44102, Jasper 44103, Joe 43702, Slibo 43704), hooks `q-d2.jail_window`,
`q-c24.cairn`, `q-c24.joes_sign`. Routes from the L4 playtests of D1 and D4. `after: [m7.sigil]` is ordering only (no
topic reads it); the new game starts on D1 directly.

## D1 (Castleview)

| what | where | how / text |
| --- | --- | --- |
| jail window, event 107 | thing at (1741, 9754); stand (1741, 10100, 1152) yaw -pi/2 | before started (or after freed) "Old bars in old mortar. Someone inside is snoring."; the violent route (started, not freed) bends the bars (113043, 113041) - not played |
| Jethro's Maps, house 4469 | door: stand (-4480, 6772, 1152) yaw pi/2, use | one resident: his talk (4919). "Jasper": first (started 113040, autonote 4420), "still languishes", after freed "Thank you for freeing my brother!..." (done 113042, 4,000 XP each, 1,000 gold), then "Good to see you again". "Joe's map" (shown with 12355): "You bought one of Joe's treasure maps?!?..." (takes 12355, gives 12356, Q-C24 done 112482, autonote 4380, 2,000 XP each). After Jasper moves in: a house screen with "Jethro" and "Jasper" |
| Castleview Jail, house 4468 | door: stand (2176, 8724, 1152) yaw pi/2, use | house screen "Warden Krupp", "Jasper". Krupp "Jasper": "Bring me proof otherwise...", with 12355 "Let me see that. A map of nowhere..." (jasper_freed 113041, `evt.MoveNPC(4918, 4469)`, the map stays), then "Jasper's gone". Jasper "Joe": "Joe sold the fake maps...", after freed "Thanks for freeing me!..." |
| Joe's sign, event 167 | (1408, 12006); stand (1408, 11600) | "MAPS BY JOE! Genuine! Only one of its kind!" |
| Joe, actor 30 (NPC 4956) | (1024, 11315); stand (1024, 10957) | "Treasure map": with 1,000 gold "Friend, have I got a deal for you!..." (-1,000, 12355, 112481, 112480), with the map "You already have the only one of its kind." |
| Kramer's Caravans, house 4464 | stand (3844, 5904, 1152) yaw 0, use | the house screen's "Kramer, Caravan Master" (the service; "Kramer" alone is his NPC talk, "Ogres"); route 414 "3 days to Lakeside for 75 gold" on Mondays and Thursdays: the new game's first day is a Monday (probe: day 0 Lakeside, 1 Sandcaster, 2 none, 3 Lakeside, 4 Sandcaster, 5 Desert of the Sphinx, 6 none) |

## D4

Arrival at Lakeside's jetty (4608, -9216). Cairn event 89 at stand (13824, -10752, 1312): with 12356 "Two paces
north of the cairn, a strongbox..." (takes 12356, `evt.GiveItem(5, 0)`, 1,500 gold, cache_dug 112484), then "A hole
two paces north of the cairn. Yours."; without the map its fail text. Slibo actor 20 (NPC 5317), stand
(-18739, 6349, 2296): "Treasure map": with 12356 buys it for 4,000 (map_sold 112483; the alternative, not played),
after the dig "You dug it up yourselves? Then you have a hole and no map...".

## Asserts

Starting qbits clear; every line; autonotes 4420 and 4380 (`assert: {autonote}`); Joe takes 1,000 gold; the warden
leaves the map; Jethro's 4,000 XP and 1,000 gold, the trade's 2,000 XP and no gold; the caravan's 75 gold; the cache's
1,500 gold and one item for the map; Slibo pays nothing after the dig; final qbits (113043 and 112483 stay clear).

## Finding (not a map bug; engine/data, A1 or the orchestrator)

The cache's T5 item (`evt.GiveItem(5, 0)` in `q-c24.cairn`) is item 10075, MM9's "Imperial Star"
(`worlds/mm9/data_tables/items.txt`), every run (normal and reload). Xeen's world.yml says Xeen never borrows from MM9
(D-44), but the runs mount `worlds/mm9/*` and the random treasure draws MM9 rows. The T3 rewards of Q-C10 and Q-C11
drew MMerge items (869, 825). The scenario does not assert the item's identity.
