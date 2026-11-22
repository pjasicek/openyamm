# Prep: the rest of tier 2 (blocks C's clan, D's burning and plaque, E, F, G, H; segments 25-99)

The party is the main chain's (Knight, Paladin, Sorcerer, Ranger line). Each quest is played from a copy of the main
chain's checkpoint around it (run.py STARTS); the class tables come from `class_table.py`. Quest logic:
`assets_dev/worlds/xeen/source/quests/<quest>.yml`; the later NPC topics: `t2-later.yml`.

| Seg. | Quest | Start | Promoter, how reached | What decides it |
| --- | --- | --- | --- | --- |
| 25 | T2-CLAN | 21 (X5, q-c4.done) | Shinobu, XD-22's cellar (actor 24): X5 event 61, shrine hall door (event 15, door 6), the hatch (door 7, open at the done stage), `climb cellar down`, (-380, -2000, -448) | `promotable clan` and `m20.started` (111400): pays 3,000 on the first promotion only |
| 47 | Q-D11 burning | main 43 (D1, peace done) | Kramer (D1 house 4464, residence list, action 4914): Bounty shows on both forts burned | DD-13 west (D2 event 49 -> (0, -64); door 9 by event 11; pit event 20 Yes) and east (D2 event 52 -> (7552, -160); door 7 by event 10; pit event 19 Yes); exits 15 and 14 |
| 51 | T2-LEAFPOINT | main 57 (D4) | Leafpoint (D4 actor 22 at (-11264, 819, 1504)) | `q-c15.done` (112302) and a Great Druid: pays 3,000 once |
| 55 | Q-D19 inner circle | main 55 (D1) | the Master Thief, DD-06's counting room (actor 29): D2 event 20, main 55's route; gong doors 4, 5, 6 stay open | `promotable southern` at the asking: sets inner_circle (113385) and promotes; nothing paid |
| 81 | Q-D22 joining, Q-D20 dragon | main 65 (D3) | the cauldron, DD-20 hall (event 39, "Drink?" Yes, at (-128, -100, 0)) | riddle (D4 event 1: "broom" -> the sump trapdoor; "witch" -> riddle_answered 113442), D4 event 49 / DD-20 event 33 the back stair; the dragon niche event 1 at (15350, 1850, -512); the Head Witch's chest event 54 (the pass 12336) |
| 85 | Q-D20 | 81 | Luna (D1 actor 32 at (-16691, 717, 1190)): Statuettes (one per state), The altar | DD-05 front door (D1 event 118, q-d6.tower_opened from main 63), L1 Pegasus event 47 at (400, 1000, 0); out by event 35 |
| 89 | Q-D23 | 85 | Morbius (D6 house 4757 door at (15156, -10496, 1664)) | Necropolis gate D6 event 127 (the pass); crypt stair event 57 at (17408, -12103); DD-21 per A8's playtest: crypt doors event 17, first entry, the fall, sluice room door event 18 (door 6), wheel 39, jar 33, the dais (-160, -3100, 32): Yes; the ritual is asked only if `can("q-d23.ritual")`; out event 26 |
| 91 | Q-D3 | main 59 (D1) | Reger (D1 event 99 at (-3328, -15892, 1023)): "What's the word?" palindrome, then the door opens house 4500 | the four cells at y 1516, x -3584/-3072/-2560/-2048 (houses 4473-4476), in order; m20.started for the promotion |
| 37 | Q-D17 oath_again | 35 (D5) | the plaque, DD-08 chapter hall (event 43 at (-1500, 1000, 1344)) | after the oath the event runs `oath_again` when `can`, else the oath's else line |

**Q-D14** (Astra, Rogue -> Spy), session 3: D3's guild gate (event 124, `xeen_d3.lua:509`) asks "Enter?" since A5's
13:05 fix and Yes lands at DD-19's `entrance:d3_guild_gate` (0, 384, 0). Block I from main 65 (D3): 95 plays the quest
(Astra at (-12800, 20756, 1519); the gate from (-10752, 22016, 1728); DD-19 by A8's playtest,
devdocs/xeen/briefs/dd19/L4/playtest.yml, and A3-side's q-d14 scenario: the mirror, the mirage, Xenoc (actor 49); the
bolt, the bridge, the ward's two lamps, Morgana (actor 30); out by DD-19 event 23), nobody a Rogue; 97 is Astra's
"The guilds' word" (class_table.py).

Suspected faults met: a monster stands in DD-21's sluice room doorway on the way back from the wheel (cleared, as a
player would fight it); none other.
