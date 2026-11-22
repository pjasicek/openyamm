# Prep: Q-D9 Nibbler's Melons

Scenario `q-d9_nibblers_melons.yml`. Quest file `source/quests/q-d9.yml` (qbits 113180-113182, autonote 4490);
Nibbler's topic 44451 in `events/common/xeen_quests.lua`, hooks `q-d9.melons_south`, `q-d9.melon_field`,
`q-d9.bark_door`. Routes: D2's L4 `playtest.yml` (Nibbler, the tree door, DD-09's trunk door), D1's (the patch),
chain segment 43 (the edges). Melon 12343, the Bark key 12342. A new game on D2 (the giver's map).

| what | where | how / text |
| --- | --- | --- |
| Nibbler's Hollow, house 4556 (NPC 5106) | stand (-9985, -5888, 992) yaw 0, use: his talk | "Monga melons": offer (started 113180, autonote 4490); started "You didn't bring me enough... Three!"; 3 melons: "Here's the key I promised you" (takes 3, key 12342, done 113181, 1,000 XP each); done with a melon "(He eats yours anyway.)" (takes 1); done "I'm growing my own melons now." |
| the great tree's door, D2 event 13 | stand (-11396, -6640, 992) yaw -1.3746, use | without the key the fail text "A door in the trunk of the great tree, locked..."; with it `MoveToMap` into DD-09 (0, -1920) at once (D-72; until 2026-11-21 the hook showed "Enter the Ancient Temple of Bark?", dropped by the move) |
| D2 west edge | set (-22016, 2048, 992) yaw pi, walk to x -24576 | the edge prompt, OK, to D1 |
| Pip Melonby's field, D1 event 195 | thing at grid (64, 67.4) = (0, -1741); stand (0, -1400) | map var 4 once: 1 melon, status "A Monga melon at the field's edge, ripe."; then nothing |
| wild melon patch, D1 event 194 | stand (9216, -13312, z 2500 dropping) | `q-d9.melons_south` once: 3 melons, "Monga Melons, three of them, ripe..."; else "Melon vines, picked clean." |
| D1 east edge | set (21504, 2048, 1088) yaw 0, walk to x 24064 | OK, to D2 |
| DD-09 trunk door, event 33 | at the arrival | "OK" prompt, to D2 (-11264, -6656) |

Asserts: starting bits clear, autonote, every line, 1 + 3 melons, the patch's else text, 1,000 XP per member, the key,
all four melons gone, the door refusing then letting in. Started 113180 stays set (until: done hides the journal line).

Finding: q-d9.bark_door's text is a question with no answer, and as a message box it is lost to the map move (the
q-d6.tower_rope precedent: `status: true`). Either D2 event 13 asks it (A6, like D1's rope 121) or the hook becomes a
status statement (A3 data). DECIDE.
