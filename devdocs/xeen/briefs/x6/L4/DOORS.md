# X6 Desert of the Sphinx: doors and arrivals

A5, 2026-11-20. Written from the build (`output/studio_cal/x6/build_w/build.json`, the export) of the install of this
session. Units: X east, Y north, Z up; facing in MoveToMap units (east 0, north 512, west 1024, south 1536). A4's
`x6.yml` is still `planned`: these are the doors and points A4 fills in.

## Arrivals (for A4's `arrivals:` and Town Portal)

| Arrival | Cell | X, Y, Z | Facing | What |
| --- | --- | --- | --- | --- |
| `sphinx_wells` | (63, 61) | (-512, 1536, 1248) | 1024 (west) | in the street before the caravans' stables (4302): routes 427, 428, Asp's 431; the Town Portal anchor and the respawn; the new-game start of the tests |
| `warzone_coach` | (86, 96) | (11264, -16384, 1504) | 1024 (west) | inside the walled coach yard (D-8.1), the desert gate on the left, the arena gate behind: Rivercity's 406, Castleview's 415 |

## Map edges (`span`/`arrival` in project.yml, as X3/X4/D3: the orchestrator's edge_spans)

- **East (X4)**: the whole east edge leads to X4's west road at its x 20: **(-22528, 2048, 1184) facing east (0)**.
  X4's west edge should arrive at X6's `entrance:east_road` (107, 60) = **(22016, 2048, 1216) facing west (1024)**.
  X4 removes its sign `thing:west_road_end` at [19.8, 59.2] when it opens the edge. X4's edge column is 1,184-1,312
  on its road; X6's road bed at its edge is 1,152 (the level span 54-66 of both frames).
- **South (X5)**: the whole south edge leads to X5's steppe road at its y 20: **(-7168, 22528, 1280) facing south
  (1536)**. X5's north edge should arrive at X6's `entrance:south_road` (50, 107) = **(-7168, -22016, 1472) facing
  north (512)**. X5 removes its sign at the steppe road's end when it opens the edge.
- Tested both ways in the scratch root (its edge_spans and outdoor_travels rows: `tools/root_tables.py`).
- **West and north**: the world rim (x 24, y 24), a cliff above the stars.

## Dungeon doors (sealed until their maps are installed and their lanes give the inside point)

Open since the eleventh session: XD-15 (`entrance:x6_paws`) and XD-14 (`entrance:x6_gate`).

The user's double-door rule: each is two leaves with a wing picture, mirrored (a building door with `leaves: 2` in a
bay of A7's width). The studio keeps such a door 256 high (a taller door is cut into the roof as one plain face), so
**the openings are A7's width but 256 high**, not 512 / 448, until A1's paired-leaf word.

| Door | Thing (event) | Where (the leaves' middle, sill) | Opening | Facing | Its lane needs |
| --- | --- | --- | --- | --- | --- |
| XD-15 The Sphinx | `thing:northern_sphinx` door (`evt:door:thing:northern_sphinx`, A3's q-c9.door, then sealed) | (9216, 10240, 1408): the breast's face at (82, 44) between the forelegs | 384 x 256 | south (1536) | open: XD-15's `entrance:x6_paws` |
| XD-14 Castle Basenji | `thing:castle_basenji` door ("Castle Basenji.  Enter?", then sealed) | (-13312, 15507, 2592): the gatehouse on the terrace at (38, 33.7) | 384 x 256 | south | open: XD-14's `entrance:x6_gate` |
| XD-20 The Warzone | `thing:arena_gate` door ("Enter the War Zone?", then sealed) | (12640, -15872, 1504): the portal in the Barbaric cliff at (88.7, 95) | 384 x 256 | west (1024) | A7: the inside point |
| FD-02 The Southern Sphinx | `thing:southern_sphinx` door (A3's m40.sphinx_door, then in) | (-12544, -10240, 1536): the breast's face at (39.5, 84), beside the cove | 320 x 256 | east (0) | FD-02's `entrance:x6_door` (-256, 0, 0) facing west (D-57; open since the 18th session); FD-02's way out to X6's `entrance:fd02_door` (-12288, -10240), 256 before the leaves, facing east |

## The coach yard's desert gate (D-8.1; not a map exit)

`thing:yard_gate_outer_n/_s` (desert side: A3's `x6.warzone_gate`, sets 116100, hides all four leaves) and
`thing:yard_gate_inner_n/_s` (yard side: `x6.warzone_gate_open`, Gorm's gate_line before the bit) at (83, 96) =
(9728, -16384), a 512 opening in the west wall. `evt:yard_gate_state` hides the leaves on load once 116100 is set.

## House doors (door id -> A4 house)

| Door | House | Name | Kind | Door point |
| --- | --- | --- | --- | --- |
| `building:x6_tavern` | 4301 | The Last Waterskin | tavern | (-2432, 2224, 1248), facing south |
| `building:x6_stables` | 4302 | Sphinx Wells Caravans | stables | (-640, 2112, 1248), facing south |
| `building:x6_houses#1` | 4303 | The Well Keeper's House | residence | (-2432, 704, 1248), facing north |
| `building:x6_houses#2` | 4304 | The Saddle Loft | residence | (-1024, 704, 1248), facing north |
| `building:warzone_coach` | 4305 | The Warzone Coach | stables | (10880, -15296, 1504), facing south |

## People outdoors (A4's NPCs without a house)

Arie 4608 at (45.4, 45.0) by her tent below the cliff path; Saul 4602 at (31.1, 70.6) by his hermitage and urn; the
Summer Druid 4601 at (69.6, 90.2) by her spring.
