# Prep: Q-D8 Vespar's Staff

Scenario `q-d8_vespars_staff.yml`. Quest file `source/quests/q-d8.yml`; generated `events/common/xeen_quests.lua`
(topic 44401 "Emerald handle" at :2651, hooks `q-d8.handle` :10039 and `q-d8.sandcaster_gate` :10049); D3 map Lua
`events/maps/xeen_d3.lua` (event 135 the rubble, 188/189 south gate outer leaves, 192/193 east gate outer leaves,
190/191 inner leaves without a check). `after: [m7.sigil]` is ordering only; no qbit set. D1 <-> D3 by `travel`
(3 days).

## Places (outdoors: placed)

| what | map | event | stand at |
| --- | --- | --- | --- |
| Vespar's House (house 4499) | D1 | door | (13828, 14664, 1344) yaw 0, use: Vespar (NPC 4949) talks at the door |
| Sandcaster's south gate, outside | D3 | 188 | (-14080, 11520, 1328) yaw pi/2; inside the gate (-14080, 14336, 1504) |
| the roadside ruin | D3 | 135 "Rubble" | (-9728, 9216, 1248) |

## Vespar, "Emerald handle"

- first: "...It must have come off on my journey back from visiting Sandcaster..." sets started 113160, autonote 4480;
- with started: "You haven't found my staff's emerald handle yet...";
- with the handle 12345: takes it, gives the Sandcaster Pass 12335 and Vespar's Staff 12528, sets done 113162,
  5,000 XP each (started stays set: `until` hides its journal line);
- with done: "Retirement suits me. I sit, I read, I do not look for handles."

## D3

- Rubble 135: once on 113161, gives the handle 12345, "You found an emerald handle."; again "Rubble, and nothing green
  in it.".
- South gate 188 without the pass: "The gate guards want a pass. Wizards' orders..."; with it: the leaf faces go
  invisible/untouchable and "The gate swings open." (status line); the party walks in to (-14080, 14336).

No issues found.
