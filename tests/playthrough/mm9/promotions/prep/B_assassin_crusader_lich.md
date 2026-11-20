# Prep: block B (segments 50-65): Assassin, Crusader, Lich

Research for `50_*.yml` to `63_*.yml` (2026-11-08/09). Sources: the map scripts
(`assets_dev/worlds/mm9/events/maps/{drangheimcity,klusoshouse,drangheim,chasmofthedead,lichlab}.lua`), the scenes'
`world_items` and `initial_state.actors`, the RUDE files, `data_tables/map_transitions.txt`, the converters' `work/`
(`doors.json`, `content.json`, `plan_*.png`, `rooms_*.png`) and headless probes (scratchpad). Conventions as in the
main run's prep sheets: MM9 key K = qbit 90000+K, item N = 10000+N, an actor's click event 53000 + its DAT object
index, its talk-exit event 50000 + that index; RUDE c7/c9/c11/c13/c15 required, c16-c20 granted, c21-c25 forbidden.

Drafting start: `output/playthrough/mm9/promotions/scratch/B_start.oysav` (00_start with Champion, PriestLight,
Rogue, Wizard and key 294, the Mage quest that block D does; scenario in the session scratchpad, `B_start.yml`).

## The party's state (all segments)

00_start's party stands at 1 HP, Weak and Insane (the main run's immortal party). **In that state `press_action:
attack` swings nobody and `press_action: char_cycle` never changes the active member** (a new-game Knight on the same
spot attacks; `hp full` or a temple heal fixes both). Segment 50 heals at Drangheim's temple first: Louhi Fresdotir,
actor 36 (15401, -7291, 544), RUDE 102, "We are in need of healing." opens the house dialog "Fre's Touch" whose
"Heal N gold" heals the active member; char_cycle selects the next (78 gold for all four from the start save).

## Drangheim City (segments 50, 52, 54, 56)

Gate from the region: stand at (11458, -4164, 757) yaw 0, walk to (12032, -4164) (ExitTrigger0's prompt); out by
the west gate: stand at (10000, -4178, 1010) yaw pi, walk to (9667, -4178).

| Who / what | Where | Notes |
| --- | --- | --- |
| Atli the Quick, actor 33, RUDE 88 | (16220, -3154, 431), The Dancing Bard; stand at (16000, -3000, 431) yaw -0.6 | click 53347, exit 50347 |
| Guaire A'Velsi, actor 38, RUDE 95 | (17695, -2867, 348), hidden until key 222 (poll every 1 s); stand at (17590, -2867) yaw 0 | 300 HP, a Bandit (9101), civilian until struck |
| Keith Bloodaxe, actor 7, RUDE 89 | (14909, -5947, 1486), the temple; stand at (14909, -5750) yaw -pi/2 | exit 50320 |
| Louhi Fresdotir, actor 36, RUDE 102 | (15401, -7291, 544) | the healer |
| Kluso's House front door | ExitTrigger2 (14531, -8438, 1659); stand at (14541, -8150, 1453) yaw -pi/2, walk to (14531, -8438) | prompt "Kluso's House"; the window (ExitTrigger1, (15104, -10199)) is the upper-floor way in |

Atli: "We have come seeking promotions." (gives 2075; forbidden with 226) -> "Yes." (needs 127: waived by
`promotions.yml`) -> "What is the first task?" / "What is the Second Task?" -> "We will do this." (224, 222) ->
"Goodbye.". Report: "We have completed your tasks." (needs 223, 225; gives 226) -> "Thank you.". The exit gives 227,
37 500 experience to each member (MM9 63 000 scaled), 5 000 gold, `MM9.promoteParty("Assassin")`. Afterwards
"Promote our eligible characters." is on his first page (done key 227).

Guaire: "Of course not." (talk only). Struck by the party's attack he turns hostile and `clear_hostiles` kills him;
his death hook (handler 97) gives 225. Before he is struck he is not hostile (clear_hostiles ignores him). The guide's
"in broad daylight" is not checked.

Keith: "We have come seeking promotions." (2078; forbidden 128) -> "Yes.  Some of us would like to become
Crusaders." -> "What is the task?" -> "We will accept this task." (128) -> "Goodbye". Report: "We have completed the
task." (needs 129, 133, 134, 135; gives 136) -> "Thank you." -> "Goodbye.". The exit gives 137, 16 500 experience each
(MM9 24 500), 5 000 gold, `MM9.promoteParty("Crusader")` (Paladin, Ranger, Monk: none in this party).

## Kluso's House (klusoshouse.blv, segment 51)

Arrival StartPoint0 (750, 842, 42) facing west. 5 Guard Captains and the Count awake on the ground floor, 8 sleepers
upstairs, hidden guards (group 1). Route: walk to (-130, -560, -20) (the planner; the hall's guards die), the
library's double door RotatingDoor0 (event 110, leaves 21/22) clicked once shut, straight (`plan: false`) to
(-900, -950, 1). **The knife is the Blackheart** (item 29, "Dagger"), a world item at (-942, -1126, 143) on the
mantle; its pickup (event 75) gives 223, rings the alarm, shows the hidden guards and wakes the sleepers (8 die). The
black chest TreasureChest1 (-1616, -961, 87; trap 18; items 180, 102) is optional. Out: walk to (850, 840, 42), then
straight to (1000, 840): ExitTrigger1 (963, 840) prompt "Drangheim City", arrival (14541, -8274) outside.

## Drangheim region (segments 54, 55)

| Who / what | Where | Notes |
| --- | --- | --- |
| Yobboes: Bandits 25-27, Cutpurses 28-31 | (1218..2529, -10021..-11332, ~1435) | handler 601: sixth death gives 129 and 6 000 experience; `YobboesDown` stops at 6 |
| Herbs (372), Plow (371), Dolly (370) | (2306, -12143), (2387, -12284), (2552, -12107), z ~1434 | world items, need 128; set 131, 130, 132; pick up from (2440, -12050) |
| Hring the Plowhands, actor 35, RUDE 91 | (-6039, -1178, 2205); stand at (-5850, -1178) yaw pi | "We have your plow." (needs 130, gives 133) -> "Thanks for your time."; exit 50030: item taken, key 200, 2 000 xp each, 500 gold |
| Ragnheid Lifegiver, actor 34, RUDE 92 | (-5712, -359, 2291); stand at (-5712, -560) yaw pi/2 | "We've got your bag of herbs." (131 -> 134); exit 50029: key 198 |
| Tyock A'Norta a'leipshi, actor 36, RUDE 93 | (-6073, -641, 2261); stand at (-5900, -700) yaw pi | "We've found your dolly." (132 -> 135); exit 50031: key 199 |

The guide puts the village "east of the city gate"; it is west of the region's centre (x about -6000).

## The Chasm of the Dead (segment 58)

Entrance and the way down to the canyon's ledge path as the main run's segment 15. **The X-shaped hall is not reached
from the tombs' junction** (the guide): from the tombs the planner finds no route. It is reached from the canyon's
ledge path at (500, 3600, -1884): Door34 (event 127, door 36, x 20..61, y 3523..3768) on its west side, the corridor
west and down the stairs (rooms 29, 30, 28, 26) to Door2 (event 111, door 20, x -8110..-8069, y 3523..3768,
z -2867), the X hall (floor -2867). The Lich Instructions (item 447, key 296) lie on the pyramid's top at
(-9380, 3767, -2540): walk up to (-9250, 3767) (arrives at z -2610), `pick_up` within reach. Doors auto-close after
5 s; each click waits until the door is shut. Doors 109 and 107 on the way back are opened by the walker.

## Yorwick and the Lich Lab (segments 60, 61, 62)

To Yorwick: travel to Thronheim, the Connecting Tunnels walked as main-run segment 53 (about 80 s). The lab's
entrance: Yorwick ExitTrigger5 (15769, -20738); stand at (16150, -20450, 1051) yaw -2.5. Arrival StartPoint0
(-1311, -4362, 1311); out: ExitTrigger0 (-1311, -4557, 1556), arrival (16332, -20257) in Yorwick.

Storeys: Level B (entrance, lobby, storeroom, ring round the atrium) z 1311; Level A (kitchen) z 2376; ground (cross
hall over the engine pit, east column) z 0; basement (engine hall, pods) z -655. **Rotating doors** (a click each,
open away from the party, shut after 5 s; a click on an open door shuts it): click only once `door_state` is closed.
Double doors here are two separate doorways with a post between (pass through one leaf's centre).

| Door (event, door id) | Box | Pass |
| --- | --- | --- |
| RotatingDoor176 (142, 54) lobby -> east side room | x 727..748, y -4035..-3830 | y -3930, from (550, -3930) to (950, -3930) |
| RotatingDoor138 (112, 24) side room -> hall | x 1782..1987, y -2058 | x 1885 |
| RotatingDoor184 (150, 62) hall -> storeroom | x -266..-61, y 563 | x -163 |
| RotatingDoor185 (151, 63) hall -> ring | x -2068..-1864, y 563 | x -1966 |
| RotatingDoor182 (148, 60) top hall -> central room | x -1413..-1208, y 727 | x -1311 |
| RotatingDoor193 (159, 71) central -> east room | x -92..-72, y 1864..2068 | y 1966 |
| RotatingDoor200 (166, 78) east room -> kitchen | x 717..922, y 3226 | x 820 |
| RotatingDoor188 (154, 66) ring -> NE room | x 2038..2058, y 8909..9114 | y 9011 |
| RotatingDoor137 (111, 23) NE room -> north corridor | x 2847..3052, y 9902 | x 2950 |
| RotatingDoor135 (109, 21) -> east column | x 3348..3369, y 10301..10506 | y 10404 |
| RotatingDoor146 (114, 26) east column | x 4004..4024, y 6922..7127 | y 7024, from (4300, 7024) west |
| RotatingDoor181 (147, 59) east column | x 3338..3543, y 3840 | x 3440 |
| RotatingDoor178 (144, 56) east column | x 3666..3871, y 2529 | x 3768 |
| RotatingDoor158 (126, 38) ground column -> room | x 3840..3860, y 3994..4198 | y 4096 |
| RotatingDoor160 (128, 40) room -> cross hall | x 1219..1239, y 4403..4608 | y 4505 |

Routes (the planner alone fails at the side room's pillar and the doors):
- Storeroom: lobby -> 142 -> (1536, -3328) -> (1885, -2300) -> 112 -> (1885, -1700) -> (-163, 380) -> 150 ->
  (-150, 2250). Elixir Ingredients (378) at y 2417, x -143..205 (pick from (-150, 2250)); Jars (358) at x -819..-492
  (pick from (-520, 2250)). Seven ingredients and four jars, world items.
- Kitchen: back to the lobby, grand stair straight north from (-1311, -3328, 1311) to (-1311, -768, 2376); (-1311,
  500) -> 148 -> (-1311, 1300) -> (-350, 1966) -> 159 -> (650, 2700) -> 166 -> (650, 3700). Cook pot event 222 at
  (696, 3932, 2376): ingredients -> Elixir Fluid (561). Burner event 223 at (1219, 4415, 2479), from (1100, 4250):
  fluid + jar -> Elixir of Defedation (246) into the **active member's** pack (char_cycle x3 from member 0 selects the
  Wizard; `evt.GetCurrentPlayerIndex()` checks it). The Elixir Instructions note (event 226) lies in the kitchen.
- Engine: Level A back to the lobby; 142, 112, west to 151 (-1966, 350), the ring north (planner) to (1850, 9011),
  154, 111, 109, south along the east column (4300, 7024), 114, 147, 144, east to (4464, 1929) and down the east
  wing's stair via (6024, 1929, 1303), (7178, 913, 709), (6091, 617, 171) to (4763, 992, 0); north to (4150, 4096),
  126, west to (1550, 4505), 128, (805, 4669, 0), straight down the south-east stair to (-1075, 4669, -654), pod 1
  at (-1260, 5765, -654) (POD_BOX x -1393..-1126, y 5632..5898).
- The pod: switch event 200 (lichswitch, (-1271, 5663, -544)); the lid lowers, 3 s later the strike: key 296 needed
  ("The engine shudders" without); each Wizard/Necromancer with an elixir (own pack first, else any) becomes a Lich
  (`evt.ApplyLichTransformation`); the first working strike gives 55 500 experience each (MM9 63 000) and key 299
  whoever it changes; `Transmuted` counts the changed; the pod rises 2 s later.

## Thjorgard City (segment 63)

From Yorwick the tunnels back to Thronheim (Yorwick ExitTrigger7 (-23768, -13893), arrival (-17164, -7782, 1501);
the tunnels' ExitTrigger1 (17243, -3850) to Thronheim), then travel to Thjorgard; the city's west gate as main-run
segment 22. Johannes Bem, actor 0 (5079, 12452, 1), RUDE 4: with key 294 (the Mage quest, block D) his first page
has "Promote our eligible characters."; the Mage row (Wizard -> ArchMage) has nobody once the Wizard is a Lich: "No
one among you can take this promotion now."

## Guide errors and findings

- steal-the-knife: the "dagger on the mantle" is the Blackheart world item (item 29); the guide's "Black's Heart" in
  the black chest is a different item. Its pickup alone gives the task's key 223 (nothing is handed to Atli).
- become-a-lich: the X-shaped hall is reached from the canyon's ledge path (Door34), not "west at the junction below
  the tombs". The Lich Lab's storeroom is on the entrance storey (Level B) north of the hall, the kitchen on the top
  storey (Level A), the engine in the basement: from the kitchen to the pods is a long walk round the atrium ring
  and down the east wing (no shorter way found).
- defeat-the-yobboes: the villagers stand west of the region's centre, not east of the city gate.
