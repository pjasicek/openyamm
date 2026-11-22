# Prep: Q-D5 Rooka

Scenario `q-d5_rooka.yml` (the paid route). Quest file `source/quests/q-d5.yml` (qbits 113100-113104, autonote 4450);
Valio's topic in `events/common/xeen_quests.lua`, hooks `q-d5.rooka`, `q-d5.valio_chest`. Routes: DD-01's L4
`playtest.yml` and chain segment 45 (which also plays M16's necklace and the east drain's ladder; this run goes back
the way it came). `after: [m7.sigil]` is ordering only; a new game on D1.

| what | where | how / text |
| --- | --- | --- |
| D1 iron hatch, event 145 | stand (1024, 3328, 1160) yaw 0 | into DD-01 at (0, -1088); arrival window "THE CASTLEVIEW SEWER" |
| drain cross west door | event 11, door 2, at (-480, 0) | `open_door(11, 2)` |
| Valio's bed, event 3 | stand (-2240, -1700, 0) | `evt.SpeakNPC(4957)` unless valio_angered ("The bed is empty"). "Rats": offer (started 113100, autonote 4450); started: "still alive... No reward for you yet!"; rooka_slain: "my chest" (done 113102); done: "It's good to see you again." |
| overflow stair door | event 16, door 7, at (-2040, -1728) | to the cistern (z -512) |
| flooded culvert, event 9 | (1280, -3360, -512) | status "flooded to its roof" until the sluice is shut |
| sluice lever, event 34 | (-1280, 1900, 0) via (-1408, 200), (-1408, 800) | "The gate drops shut..."; door 10 opens (the culvert drains) after about 7 s |
| nest | via (1280, -2496), (1280, -1600, -420), (2100, -1408, -240) | Rooka actor 36 (row 11403, level 24) at (3328, -2432); timer event 30: `q-d5.rooka` (rooka_slain 113101, 3,000 XP each), her kill 816 / 4 = 204 each |
| Valio's chest, event 8 | by the bed (-2240, -1488) | OpenChest(4) then the hook's SimpleMessage: done "Valio Magnus, graduated 787 cum laude... smiles simply." (chest_opened 113103); before done the yell (valio_angered 113104, Valio actor 46 row 11193 shown hostile). Container 4: 300 gold fixed, T2 random treasure (variable gold and items) |
| hatch ladder, event 17 | (0, -1000) | "OK" prompt, to D1 (1024, 3072) |

Asserts: starting bits clear, the autonote, every line, 3,204 XP per member at Rooka's death, chest gold >= 300, no
anger, Valio's monster still hidden. Started 113100 stays set (until: done hides its journal line only).
