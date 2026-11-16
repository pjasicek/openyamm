# X2 Rivercity and Lake Darzog: the dungeon doors (for the dungeon agents)

Written by the X2 agent, 2026-11-15; **final values from the built map, 2026-11-16** (they replace the first
provisional table; see "Changes" below). X2 is `xeen_x2.odm` (MM7 world as a stand-in, as X1), map_stats 9136.
Each dungeon's exit to X2 should point at `xeen_x2.odm` with the **outside arrival** below: where a party leaving the
dungeon stands, 400 units in front of the door's dark click face, on open ground, facing away from the door. The
project's `neighbours` in `devdocs/xeen/briefs/x2/L4/project.yml` carry the same numbers in their notes.

Units: game map units (X east, Y north, Z up). Facing: degrees (0 east, 90 north) as a neighbour's `direction`, and in
the game's angle units (2048 a turn, 0 east, 512 north) as `evt.MoveToMap`'s facing. Cells: X2's sketch cells
[x, y] (x east, y south; X = (x - 64) * 512, Y = (64 - y) * 512). Positions read from the build
(`output/studio_cal/x2/build/`: the dark face of each doorway or cave mouth, the door of each building).

| Door | Neighbour id | Dungeon | Where on X2 | The door's click face (X, Y, Z) | Outside arrival X, Y, Z | Facing |
|---|---|---|---|---|---|---|
| Robbers' Den | `door:xd21` | `xeen_xd21.blv` | Rivercity, on the south quay beside the great bridge's south end: a dark door in an arched stone frame in the quay's retaining wall, facing the river (north) | 1280, 3772, 640 (cells [66.5, 56.63]), faces north | **1280, 4172, 640** | north: 90 deg, 512 |
| Ogre Lair | `door:xd27` | `xeen_xd27.blv` | North-west: a rock cave mouth in the bluff on the west bank of the north river, with the ogres' fire and the boulders they threw into the river below it | -20992, 17555, 1216 (cells [23, 29.71]), faces south | **-20992, 17155, 1248** | south: 270 deg, 1536 |
| Temple of Yak | `door:xd06` | `xeen_xd06.blv` | The fairy woods' dark south end, near the world rim: a stone temple front built against a rise, door facing north, torches and skulls | -1024, -18240, 1088 (cells [62, 99.63]), faces north | **-1024, -17840, 1053** | north: 90 deg, 512 |
| Darzog's Tower | `door:xd12` | `xeen_xd12.blv` | Lake Darzog's wooded island (tower centre cells [31, 58]): the door on the tower's east side, facing the island's jetty | -16031, 3014, 768 (cells [32.69, 58.11]), faces east | **-15631, 3014, 768** | east: 0 deg, 0 |

How the doors open on X2 (the outside's conditions; the dungeon decides its own inside):
- **XD-21** open (Q-C3, Roxanne's tiara; promotion T1-E). Hover "Enter the Robbers' Den".
- **XD-27** open (Q-C23, Captain Nystor's ogre boulders; his notice on the dock names the lair). Hover "Enter the Ogre
  Lair".
- **XD-06** needs the Yak Stone: qbit **110101** (`yak_stone`, the number X1 declared; set by Mirabeth's quest Q-C12 on
  X3, not built). Without it the door says so.
- **XD-12** needs the Skeleton Key (M13, from XD-11, not built): planned item **12100** (X2's range); in the MM7
  stand-in world the door tests item **1461** (MM7's William's Tower Key). The island is reached by Medin's boat from
  his jetty on the lake's east shore once the three lake dragons are dead (Q-C13, qbit 110201 `lake_beasts_slain`), by
  Water Walk or by Fly. A party leaving XD-12 arrives on the island; the boat at the island's jetty rows it back.

Each door's event leads into its dungeon at that map's own start (`into` without an arrival point); a dungeon agent who
wants the party set down elsewhere inside says so and the X2 agent (or the lead) adds the point.

## Changes

- 2026-11-16, after the first builds: the Robbers' Den's door moved from [66.25, 56.5] to [66.5, 56.63] (the door had
  to stand on the quay's level, 640); its arrival from (1152, 4250, 640) to **(1280, 4172, 640)**. The Ogre Lair moved
  one cell west (out of the river's bank): arrival from (-20480, 17152, 1152) to **(-20992, 17155, 1137)**. The Temple of
  Yak's arrival z from 896 to **930** and Y from -17485 to **-17584**. Darzog's Tower: the island was made larger;
  arrival from (-15488, 3072, 768) to **(-15631, 3014, 768)**.
- 2026-11-16, later the same day (the temple front made larger, the hills rolled more): the Temple of Yak's door
  half a cell back into its porch, arrival **(-1024, -17840, 1053)** (was -17584, 930); the Ogre Lair's arrival z
  **1184** (was 1137: the ground in front now lies at the mouth's floor). Robbers' Den and Darzog's Tower unchanged.
- 2026-11-16, the hills raised (the map's height range to the design's 2,500): the Ogre Lair's mouth floor 1216 (was
  1184) and its arrival z **1248** (X and Y unchanged). The other three unchanged.
