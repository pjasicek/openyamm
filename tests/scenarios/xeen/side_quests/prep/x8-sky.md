# X8-SKY Cloudreach: prep

Quest file `source/quests/x8-sky.yml` (ours, no giver: the sky map itself); bits 115020 explorer, 115021-115023 nests
1-3; award 406 Super Explorer; the statue +2 base Speed to every member (`xeen_quests.lua:10735`); each nest 500 XP to
every member (`:10748-10776`). No autonote, no journal line.

- **Way up** (the Witch Tower, XD-04; route `briefs/xd04/L4/playtest_m4.yml`, the M4-done visit): the cloud stair
  (XD-04 event 15) needs m4.done 110047 (the Crusaders, M4 + T1-A, segment 09) and the tower door (X1 event 73, from
  (12288, -9114, 858) yaw -π/2) the Crystal Key 12031, which Valia gives and never takes back (m4.yml). A new game
  stands for that with qbit 110047 and the key (story preconditions). XD-04 from the door (0, -2900): the east and west
  stairs to the third floor (0, 2560, 1280), the herb loft (780, 2060, 1472): the witches' stores, chest 47, the
  coven's key 12034; the north stair to the face door (event 34, door 15) at (-3072, 1080, 1920); the sanctum (the
  Head Witch and her sisters, alive on a new game: cleared), the ward (event 43, door 19, falls for Crusaders), the roof
  stair, the hatch (event 27, door 8), the roof (-5800, 448, 2560) and the cloud stair (-7150, 448), event 15: "You
  climb the stair of cloud into the sky." to X8 (11520, -6802, 0).
- **X8** (`briefs/x8/L4/playtest.yml`, A6): the arrival line ("The cloud holds under your feet like stone", status,
  once). The Witch Clouds' causeway (11520, -5232) → (10354, -4527) → (9078, -3319) → (7803, -2110) → (6656, -1024),
  the spires (7776, -127) → (9158, 978) → (10540, 2083) → (11776, 3072): nests events 9 and 10 ("Harpy Nest. Destroy?",
  Yes; No: "You leave the nest as it is." on the status line). The explorer's rock (11137, 4907) → (10715, 6120) →
  (10293, 7332) → (9728, 8360) → (11181, 10071) → (12258, 10895) → (13334, 11718) → (14080, 11988): the statue event 6
  (again: "The statue is silent."). Back the same way to the landing, the witch's perch (11520, -5632) → (11176, -6867)
  → (10833, -8103) → (10489, -9340) → (10240, -10240): nest event 11.
- **The fall** (D-6.2; `playtest_fall_east.yml`): off the Witch landing's east edge (east of x 12720 at y -5632); the
  one-second timer (event 7) below z -1000 calls `Xeen.skyFall(11264, -7936, 768, ..., "xeen_x1.odm")`: X1 by the
  Witch Tower, from Xeen.SkyFallHeight above the ground, about a third of each member's HP (immortality off for it).
