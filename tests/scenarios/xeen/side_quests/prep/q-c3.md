# Prep: Q-C3 The Tiara (with T1-E)

Scenario `q-c3_the_tiara.yml`. Quest file `source/quests/q-c3.yml`, promotion `t1-e.yml`; generated
`events/common/xeen_quests.lua` (topic 42651 "Tiara", hooks `q-c3.*`). Routes from the main run's segments 13, 17, 21
and the L4 playtests of XD-07, XD-21, X4.

## Getting there

| from | how | to |
| --- | --- | --- |
| X4 | castle gate event 180: stand (-1024, 6707, 1760) yaw pi/2, use | XD-07 gatehouse (0, 384, 0) |
| XD-07 | castle door event 8 at (0, 300, 0), "OK" | X4 (-1024, 6912) |
| X4 | stand (16384, -20480, 992), walk south to (16384, -24064), "OK" | X2 north edge |
| X2 | den door event 114: stand (1280, 3950, 640) yaw 3pi/2, use | XD-21 quay cellar (-2560, 320, 0) |
| XD-21 | quay door event 17 at (-2560, 250, 0), "OK" | X2 (1280, 4172) |
| X2 | stand (1024, 21504, 1216), walk north to (1024, 24064), "OK" | X4 |

Story precondition: the portcullis (XD-07 event 40, hook `m5.crusaders_gate`) needs `m4.done` 110047 (the Crusader
title); set by the console. Roxanne's topic itself has no gate (`after: m5.audience` is ordering only).

## XD-07

- The throne room's double door (event 25, doors 13/14) must be opened from (0, 3150): the walk from the great hall
  (0, 3300) to the east tower (1100, 5376) goes through it (no route while it is shut; the main run opened it at the
  audience in segment 13).
- East tower door event 19 / door 5 at (1100, 5376); landing (4900, 5376, 640); Roxanne's door event 42, house 4204,
  NPC 4404. Topic "Tiara": first "my diamond tiara has been stolen from my room" (sets started 112060), then
  "I see that you have not recovered my tiara", with the tiara "You have recovered my tiara..." (takes 12150, sets
  done 112061, clears started, gives 12520, 3,000 + promote `tiara` + 5,000 XP each), after "It is always
  exhilarating...". "Rogues" (T1-E) only after done with a Thief left; hidden here (the Thief was promoted).
- Bedroom: (4608, 6000, 640), (4608, 7050, 1280), door event 17 / door 1, chest event 12 at (4900, 8100, 1280):
  before done "locked with a little silver lock" (hook fail text); after, a chest (T3, 1,000 gold + items).

## XD-21 (the den)

Arrival hook window "The robbers' den, under the great bridge." (arrived_once 110304). Worn block event 22 / door 5
(robbers_den_found 110302). Crawl door 14/3, dicing room, west bank (plank bridge door 8 drawn back), bunk door 8/2,
sluice door 23/6, catwalk (-400..450, 5760), east bank, winch event 30 runs the bridge out, boss stair to
(2850, 3968, 256), boss door 3/1; the Robber Boss actor 2 dies: hook window "The Robber Boss falls..."
(robber_boss_slain 110301); his body loot the Ring of Keys 12151 (`combat_loot`). Catch event 9 at (3680, 4480, 256)
stops the dart slabs. Iron door event 29 / door 7 (robbers_vault_opened 110303). Strongbox event 12: the trap first,
then the vault hook: tiara 12150, tiara_recovered 110300; the next use a plain chest.

## Asserts

qbits clear at start; 112060 after the first talk; 110300-110304 in the den; 112061 set and 112060 clear at the end;
12150 taken, 12520 given; 8,000 XP to the Knight and to the Thief; no gold; classes Knight Rogue Cleric Sorcerer;
the bedroom chest pays gold. Journal: the started bit carries the journal line (no journal assert in the runner;
the qbit stands for it). No autonote in this quest.

No bugs found.
