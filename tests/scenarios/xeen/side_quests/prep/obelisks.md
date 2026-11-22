# OBELISKS: prep

Quest file `source/quests/obelisks.yml` (ours, no giver, level 40). Each obelisk is a bmodel whose faces carry the
event (no entity position): the spot comes from the map's `sketch.yml` `thing:obelisk` cell (x = col * 512 - 32768,
y = 32768 - row * 512); the party stands 512 south of it facing north, at the ground height found by a probe (a drop
from z 5000, `output/xeen_sidequests/helper_f/probe_obelisks.yml`). The hook shows the word in a message, sets the
bit, writes the autonote and plays `xeen_obelisk`.

| Map | Event | Bit | Autonote | Word | Stand (x, y, z) |
| --- | --- | --- | --- | --- | --- |
| X1 | 75 | 115040 | 4700 | SEEK | 5120, 14848, 897 |
| X2 | 168 | 115041 | 4701 | THE | -20480, -7424, 1505 |
| X3 | 105 | 115042 | 4702 | HOARD | -2304, 16896, 1201 |
| X4 | 139 | 115043 | 4703 | BURIED | -8192, -1792, 1345 |
| X5 | 73 | 115044 | 4704 | FOR | -2816, 10496, 1089 |
| X6 | 36 | 115045 | 4705 | THE | 5632, 6144, 1473 |
| X7 | 13 | 115046 | 4706 | SPHINX | 0, 0, 2305 |
| D1 | 190 | 115050 | 4707 | DIG | -18944, -6656, 1249 |
| D2 | 43 | 115051 | 4708 | BENEATH | -14336, 6144, 1249 |
| D3 | 134 | 115052 | 4709 | THE | -6912, 18176, 1569 |
| D4 | 78 | 115053 | 4710 | BROKEN | -3584, -9216, 1185 |
| D5 | 49 | 115054 | 4711 | TRAVEL | -9088, -4736, 1473 |
| D6 | 85 | 115055 | 4712 | PYRAMID | -17408, 512, 2049 |

- **Cloudside hoard**: X6 event 27, "A mound of sand" (entity 7dec11 at (9533, 9882, 1408)); stand (9533, 9370, 1432)
  facing north. Without all seven bits: "A mound of sand between the paws. Without knowing where to dig, you could dig
  all week."; with them: 115048, 10,000 gold, `evt.GiveItem(6, 0)` twice (random level-6 items: counted, not named);
  after: "Sand, and more sand." (`xeen_quests.lua:7206`).
- **Darkside hoard**: D5 events 4 (the broken travel pyramid's body) and 6 (the fallen capstone), the same hook; stand
  (16589, -5837, 1576) facing north (`briefs/d5/L4/playtest.yml`). Without all six: "The pyramid portal has been
  destroyed."; with them: 115057, 20,000 gold, two level-6 items; after: "... Under its capstone: rubble."
- Between maps: `travel` (2 days each, the side quests' overland journey). The x6 playtest's note that the mound "has
  no fail text" is stale (the hook has one now).
