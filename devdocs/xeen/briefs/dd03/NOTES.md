# DD-03 Castle Kalindra: notes before the build (lane A8)

Built 2026-11-20 (L1-L4 in this folder; the build notes are `L4/NOTES.md`). This file holds what other lanes need: the
stage map for A6's outside, with the measured heights.

## Which part returns at which stage (for A6's outside on D1, decider D-30)

From the approved graph (`devdocs/xeen/mockups/act3_graphs/dd03.graph.yml`) and D-26. **Measured (the L4 build):**
ground floor 0, second floor 640, third floor 1280, the dungeon -640 and Scraps' kennel -1152. The decider's suggestion
is kept, adjusted to the rooms:

| Stage (qbit) | Inside (rooms in phase) | Outside on D1 (solid white stone, `xkshimmer` until then) |
|---|---|---|
| 1 (111381, m19.stage1) | ground floor (z 0): gate passage, entrance hall, throne room, north and south wings, banquet hall, kitchen, coat closet, armory; the Cloud Stairs' foot (the stair itself mist) | the gatehouse and gate, the curtain walls, the keep's ground storey |
| 2 (111382, m19.stage2) | second floor (z 640): the landings, Captain's corridor (houses 4502-4504: Dimitri, Megan, the Observatory), Sleeping Chambers, phase gallery, vaults (the disk safes) | the keep's second storey, the observatory's turret (the telescope's room is on this floor) |
| 3 (111521, m26.stage3) | the dungeon (z -640; the kennel -1152): Scraps' kennel, Maximum Security (Guido 4505), the cell block, guardroom, dungeon vault, the old well | the towers over the dungeon and the cell block (the dungeon itself is below ground and shows nothing outside) |
| 4 (111522, m26.stage4) | third floor (z 1280): landing, the Queen's gallery, Royal Bed Chamber, the Queen's court (houses 4506-4509, 4511), bell tower, shimmering attic; and the open-sky stable yard on the ground floor (Stables 4510, Mirror 4512) | the keep's third storey, the bell tower, the remaining towers and their cones, the banner, the stable yard's gate |

For A2 (the Act IV region), **measured**: stage 3's monsters stand on the dungeon floor at z -640 (rooms -640 to -128,
the old well's shaft to 384) and Scraps at z -1152 (the kennel, -1152 to -128); stage 4's on the third floor at z 1280
(rooms 1280 to 2304); none in the stable yard. Stage 2's stand at z 640, stage 1's at z 0. A monster of the map at
z < -100 or z > 1200 is Act IV.

The castle's footprint in the map's frame (x east, y north; the gate in the west, the party enters facing east): the
gate passage x -2048 to -1024; the keep's ground storey x -896 to 4992, y -1408 to 2688; the stable yard x -1664 to 1024,
y -3200 to -1024 (south of the entrance hall); the second floor over the north half (y 1408 to 3456); the third floor
and the bell tower further north (y 3072 to 5632, x -2048 to 3584); the dungeon under the south-east (x 768 to 5888,
y -7296 to -2688).

## D-32 (levelRadiusLimit 60) for the build

Monsters wider than 60 move at radius 60 indoors and pass 128-wide openings; large monsters are kept in by **low**
openings. Scraps and the two Bone Dragons are 450 tall: the kennel's opening and the stair to Scraps at 288 high or
less, the old well's way out too unless a door leaf closes it (`mockups/act3_a8_decisions_a.md`, reworded by D-32).

## Double doors (the user's rule, 2026-11-20)

Kalindra's gates, the throne room's and great halls' doors and the vault doors: two leaves, each with its own wing
picture (mirrored for the other side), opening apart (lanes/README.md).
