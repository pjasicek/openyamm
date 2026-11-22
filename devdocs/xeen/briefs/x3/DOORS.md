# X3 Lifeforce Lagoon: doors, edges and arrivals

Written by lane A5's X3 agent, 2026-11-20; brought to the installed build by A5's fifth session (X3 installed
2026-11-20, `assets_dev/worlds/xeen/maps/xeen_x3.odm`) and the sixth (XD-08 and XD-13 live, the north edge by edge_spans). Z values are the installed terrain's. X3 is `xeen_x3.odm`, map_stats 9101. Values change only when the map is rebuilt; this file is kept current.

Units: game map units (X east, Y north, Z up). Facing: degrees (0 east, 90 north) and in the game's angle units (2048
a turn, 0 east, 512 north) as `evt.MoveToMap`'s facing. Cells: X3's sketch cells [x, y] (x east, y south;
X = (x - 64) * 512, Y = (64 - y) * 512). An outside arrival stands about 400 in front of a door's click face, facing
away from the door (inward, D-11.6). Z values marked * are read from the build's terrain and should be checked in game
before a neighbour hard-codes them.

| Door / edge | Leads to | Click face (X, Y, Z) | Outside arrival on X3 (X, Y, Z) | Facing | State |
|---|---|---|---|---|---|
| `thing:high_magic` (XD-11 Tower of High Magic) | `xeen_xd11.blv`, its own start | 256, -2074, 992 (cells [64.5, 68.05]), faces north | **256, -1674, 992** | north: 90 deg, 512 | live: A3's `m13.tower_door` (Enchanted Key 12306) |
| `thing:xd13_stair` (XD-13 Newcastle Keep) | `xeen_xd13.blv`, inside (0, 320, 0) facing north (512) | pit hatch at 10496, 15616, 1750 (cells [84.5, 33.5]) | **10496, 15216, 1760** (XD-13's gate exit; the terrain there 1760) | south: 270 deg, 1536 | live: with the deed (m8.deed, qbit 111160), else "A board is nailed across the stair: CROWN LAND. FOR SALE. ENQUIRE AT EBENEZER'S TENT." |
| `thing:tomb` (XD-08 Tomb of a Thousand Terrors) | `xeen_xd08.blv`, inside (0, 384, 0) facing north (512) | barrow door at about -15360, -10240, 1248* (cells [34, 84.5]), faces north | **-15360, -9830, 1146** (XD-08's door exit; the terrain there 1146) | north: 90 deg, 512 | live: A3's `m10.tomb_door` (the Stone of a Thousand Terrors 12304) |
| `thing:coffin_closed` / `thing:coffin_open` (XD-24 Nightshadow Crypt) | installed (A7, 17:41): into XD-24's start (0, 704, 0) facing south (1536) | 17664, -4608, 992 (cells [98.5, 73]) | 17664, -5120, 992 (cells [98.5, 74]) | south: 270 deg, 1536 | two refusals, `q-c7.coffin`, then the stair in |
| `edge:east` | `xeen_x2.odm`, X2's west start | road at y 40 (cells), X 32768 | X3's east start **21504, 12288, 1024** | west: 180 deg, 1024 | live from X3 |
| `edge:west` | `xeen_x5.odm`, X5's east start | road at y 59, X -32768 | X3's west start **-22016, 2560, 864** | east: 0 deg, 0 | live from X3 |
| `edge:north` (D-11.6) | `xeen_x4.odm`, X4's x 36 arrival **(-14336, -22016, 992, X4's ground) facing north (90 deg, 512)**, the world's `edge_spans.yml` row (the project's `span: [-32768, 32768]`; no travel row) | the whole north edge (the north road meets it at x 50) | X3's north start, X4's south edge west of x 0 (edge_spans): **-7168, 22016, 1120** | south: 270 deg, 1536 | live |

## What the neighbours should use

- **X2's west edge** (live since A5's fifth session): arrives at X3's **east start (21504, 12288, 1024)**, facing
  west; X3's east edge arrives at X2's west start (cells [21, 40]).
- **X5's east edge** (A6): `arrival_side: west`, X3's **west start (-22016, 2560, 864)**, facing east (the fen road
  at y 59). X5 needs an east start (an `entrance:east_road` on its lagoon road at about cell [107, 58]) for X3's
  `edge:west` to land there; until then the game sets the party on X5's party start.
- **XD-08's exit** (A7, the tomb door): **(-15360, -9830, 1146), facing north (512)**; X3's tomb door leads to XD-08's
  start (0, 384, 0) facing north. Both checked (A7's `playtest_exit.yml`, X3's walk).
- **XD-13's exit** (A7, `exit:gate_door`): **(10496, 15216, 1760), facing south (1536)**, in the ruin's courtyard
  below the hatch; X3's hatch leads to XD-13's start (0, 320, 0) facing north, with the deed. Both checked.
- **XD-24** (A7, installed 17:41): `thing:coffin_open` takes `into: {map: xeen_xd24.blv, at: [0, 704, 0], facing:
  1536}` (A7's start, the coffin stair's foot); its exit arrives at (17664, -5120, 992) facing south.
- **XD-11's exit** (A8, `exit:x3_door`): **(256, -1674, 992), facing north (512)**, on the islet in front of the
  tower's door, looking up the causeway.
- **A4's arrivals** (towns/x3.yml, Town Portal and mirrors):
  - `nightshadow_square`: **(18432, -5120, 1008), facing north (90 deg, 512)** (the paved court stands 16 over the terrain; A4): the square's south side, looking at
    the coffin and the dial walk (cells [100, 74]).
  - `newcastle_gate`: **(9216, 13312, 1504*), facing north (90 deg, 512)**: outside the gate below the ruin, by the
    mirror 4121 (cells [82, 38]). 1504 is the installed terrain there, on the stair lane below the gate's apron
    (1,750); the walk stands there and the tour shot looks right.
- **X4** (installed): X3's whole north edge leads to X4's x 36 arrival (-14336, -22016, 992) facing north; X4's south
  edge west of x 0 leads to X3's north start (-7168, 22016, 1120) facing south (D-11.6, the world's `edge_spans.yml`).
  Both walked (`tests/scenarios/xeen/edge_spans.yml`, X3's walk).
