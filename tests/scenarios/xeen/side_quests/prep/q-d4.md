# Prep: Q-D4 Public Storage

Scenario `q-d4_public_storage.yml`. Quest file `source/quests/q-d4.yml`; generated `events/common/xeen_quests.lua`
(topic 44201 "The chests" at :2484, hooks `q-d4.number_chests` / `letter_chests` at :9825-9841); D1 map Lua
`events/maps/xeen_d1.lua` (events 79, 225-242). `after: [m7.sigil]` is ordering only: Dyson's topic has no gate, so
no qbit is set; the scenario starts on D1 (as Q-D6 does).

## Places (D1, Castleview: placed; world x = (tile x - 64) * 512, y = (64 - tile y) * 512, sketch.yml grid 512)

| what | event | stand at | notes |
| --- | --- | --- | --- |
| Public Storage (house 4470) | 79 | (128, 1516, 1152) yaw -pi/2, use | Dyson (NPC 4920) talks at the door |
| numbered chests, west to east | 225-233 | (x, 650, 1152) yaw -pi/2 pitch -0.3, use | x = -1715, -1546, -1377, -1208, -1039, -870, -701, -532, -363 |
| lettered chests, west to east | 234-242 | (x, 650, 1152), same | x = 589, 758, 927, 1096, 1265, 1434, 1603, 1772, 1940 |

The chests' lids (y 282, z ~1190) are hit at about 430 by the use key from there.

Numbers (title "A chest with a N on its lid"), west to east: 3 7 1 9 5 2 8 4 6 (events 225-233). Map var
`d1_numbers` starts 1; the right chest: "Chest N: the lid drops shut." (+1); a later one: "Chest N is shut."; an early
one: "Chest N will not shut. All nine lids spring open again." (back to 1); the ninth (var 10): the hook, "The ninth
lid drops shut with a satisfying clunk..." (numbers_closed 113081).

Letters (status "A letter on the lid reads: X" on every use), west to east: F T K P O C R I H (events 234-242). Map
var `d1_letters` starts 0; the right letter +1 ("A letter on the lid reads: P. The lid drops shut."); one already shut:
"The P chest is shut."; a letter whose turn has not come resets to 0 ("A letter on the lid reads: F. It will not shut.
All nine lids spring open again."); the ninth: the hook, "P, I, T, C, H, F, O, R, K. The last lid drops..."
(letters_closed 113082). Reading the row west to east leaves nothing shut (P advances, O resets), so a player can read
first and then close in order. The scenario asserts these lines.

## Dyson, "The chests"

- first: "...The letters spell something you'd find in a barn: PITCHFORK." sets started 113080, autonote 4440;
- with one row: "Half the chests. Half an accomplishment. I don't pay in halves.";
- with both: "Every lid down, in order..." sets done 113083, 2,000 XP each, 500 gold (once, though under
  `evt.ForPlayer(Players.All)`), `evt.GiveItem(3, 0)` twice (two random items);
- with done: "...but to open them requires intellect most uncommon. Don't try. I just got them shut."
- started is not cleared (`until: [done]` hides its journal line only).

## Notes for the map lane (D1, A6)

Fixed (A6, 2026-11-21 14:31-14:35): the lettered chests used to give only the letter and reset silently; they now
speak like the numbered row (the lines above).
