# Prep: Q-C5 The Snakes of Asp and Q-C11 Crystals of Piezoelectricity

Scenario `q-c5_q-c11_asp_and_crystals.yml` (one run: the crystals lie behind Asp's transformer). Quest files
`source/quests/q-c5.yml`, `q-c11.yml`; generated topics in `events/common/xeen_quests.lua` (Adam 42753..., Eve,
Falagar 43051...), hooks `q-c5.*`, `q-c11.crystals`. No main-run segment plays them; routes from the L4 playtests of
X4 and XD-25. No story precondition (`after: []` for both).

## X4 (Asp; the new game starts at (-12800, -11776) in Asp)

| what | where | how |
| --- | --- | --- |
| Adam (NPC 4301) | actor 32 by the well, stand (-10752, -10750, 1056) | `interact_actor`; "Curse": first "A terrible thing..." (started 112100), then "Still snakes...", after done "The curse is over..." (rewarded 112103, 5,000 XP each, 1,500 gold once), then "Thank you for saving us!..." |
| Eve (NPC 4302) | actor 33, stand (-10752, -11250, 1056) | "Transformer": the rule (also sets started); after done "The curse is over! Thank you so much!" |
| rule stone | event 98 at (-11213, -8909) | window "A message appears in the stone: The southwest corner is where to start..." |
| pedestals 1-8 | events 90-97 round the well (-11520, -11008); 1 = SW (-12032, -11520), then clockwise 2 W, 3 NW, 4 N, 5 NE, 6 E, 7 SE, 8 S | each touch toggles blue/red (map vars 4-11), status "The pedestal is cool to the touch."; 1, 3, 5, 7 red and the rest blue: the 30-game-second timer event 176 fires the hook (pedestals 112101) and the window "The pedestals hum together..." |
| undercroft stair | event 99, hatch at (-11520, -8960) | to XD-25 (-2208, 1760, 256) |
| Snake Oil | house 4173, stand (-13380, -9856, 1056) yaw pi | shut (a plain window) until done, then the shop |
| Falagar (NPC 4304) | his hut, house 4167, stand (18304, 1044, 1408) yaw pi/2, use | a residence opens his talk; "Crystals": first (started 112220), then "You haven't brought me...", with the crystals "Thank the Gods!..." (takes 12313, done 112221, clears started, 3,000 XP each, `evt.GiveItem(3, 0)`), then "Carlawna is my sister..." |

## XD-25 (Asp Undercroft)

Stair door 21/7; cistern; east (300, 1600), (1000, 1600); brood hall (1613, 900); (1000, 320); brood stair (2304,
-300) to (2304, -1850, -608); coil passage (2304, -3584), (700, -3584), (-128, -3584); field of light event 13 /
door 3 (fail text without 112101); transformer hall: housing event 10 at (384, -2080) (fail text "shut tight while
the machine hums" until done), transformer event 25 at (384, -2980): question "Do you wish to destroy it?", No keeps
it, Yes: hook window "The transformer sparks...", done 112102, housing door 2 and cages door 8 open; again "The
transformer is scrap."; housing event 11 at (384, -1680): the crystals 12313 (crystals_found 112222), again "The
housing is empty."; drain (-384, -500, 0), bolt event 15 / door 4, the townsfolk's "Thank you for saving us!" at
(-384, 0) (townsfolk_thanked 110840); cistern door 19/6; cellar door event 2 to X4 (-11520, -9448).

## Asserts

Starting qbits clear; each talk's lines; 112100, 112220, 112101, 112102, 110840, 112222, 112103, 112221 set and
112220 cleared; exact XP per member (5,000 Adam, 3,000 Falagar), Adam's 1,500 gold (once, not per member), no gold
from Falagar, the crystals taken and one item in their place; Snake Oil opens. q-c5.started has `until: [done]` but
the hand-in does not clear it (the journal row's forbidden bit hides the line; Q-C11 clears its own started): a style
difference, not a fault. No journal or autonote assert in the runner; the qbits stand for them.

Timing note: the pedestals' timer can fire between the touches (the --reload run did): the scenario does not assume
the bit is still clear after the fourth touch, and does not close windows between touches.

No bugs found.
