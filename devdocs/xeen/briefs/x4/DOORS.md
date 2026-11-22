# X4 Burlock Savannah: doors, edges and arrivals

A5, 2026-11-20. **Built values** (no longer provisional): read back from the installed map
(`assets_dev/worlds/xeen/maps/xeen_x4.odm`) with `oymap things devdocs/xeen/briefs/x4/L4 --assets assets_dev --json`
and the ODM's height map (`output/studio_cal/x4/tools/doors_x4.py`); every arrival below is held by the headless check
`output/studio_cal/x4/run/arrivals.yml` (`tools/gen_arrivals.py`: the pose, 3 s, the party's feet still there).
X = (x - 64) * 512, Y = (64 - y) * 512 for sketch cells [x, y]. Facing: degrees (0 east, 90 north; the unit of a studio
`teleport`'s `direction`) and the game's 2048 units (0 east, 512 north; `evt.MoveToMap`'s facing).

| Id | Leads to | Click face / point (X, Y, Z) | Outside arrival (X, Y, Z) | Facing | State |
|---|---|---|---|---|---|
| `edge:south_x2` | X2: the south edge **east of x 0** (the world's `edge_spans`, D-11.6; the travel row `xeen_x4.odm` Down -> `xeen_x2.odm up 5` for the rest of the side) | the road out at [96, 128] | X4's south start for X2's north edge: **(16384, -22016, 992)**, cells [96, 107] | north: 90, 512 | live (A2's rows) |
| `edge:south_x3` (D-11.6) | X3: the south edge **west of x 0** (the world's `edge_spans` row; the project neighbour's `span: [-32768, 0]`, no travel row); no plate or barrier since 2026-11-20 16:5x | the Asp road out at [36, 128] | lands on X3 at its north arrival **(-7168, 22016, 1120)** | south: 270, 1536 | live (A1's merge point 9) |
| X3 to X4 | X3's north edge (the world's `edge_spans` row, `at` given) | - | **(-14336, -22016, 992)**, cells [36, 107] (the scene's second "south start"; the first, X2's at x 96, is the one the game takes by name) | north: 90, 512 | live |
| west (X6), east (X7) | not built | signs at [19.8, 59.2], [108.2, 65.6] | planned [20, 60] (-22528, 2048), [107, 66.5] (22016, -1280) | e / w | sealed |
| `thing:castle_gate` | XD-07, inside at **(0, 384, 0) facing north (90, 512)**: the gatehouse before the Crusaders' portcullis (XD-07's start) | the gate (a 384 x 448 door in a stone frame on the gatehouse's south wall), sill 1,888, centre (-1024, 7168) | **(-1024, 6912, 1808)** on the castle lane's top (the ramp), cells [62, 50.5]; XD-07's castle door uses it (landing 1,802) | south: 270, 1536 | live (`XD07_LIVE`); **gate sill 1,888** (D-11.2: 1,900) |
| XD-07 throne fall | lands beside the west tower, outside the walls | - | **(-4608, 9728, 2504)**: ground 1,504 there (the rise's west slope) + 1,000; XD-07's throw uses it | east: 0, 0 | live (a fall: D-4's 1,000 over the ground, ordinary fall damage) |
| XD-07 postern | XD-07's `exit:x4_moat` (A7): X4 has no moat; the arrival is the flat ground at the castle rise's west foot, 1,024 west of the rise's face, clear of water, props and trees | - | **(-5120, 8448, 1312)**, cells [54, 47.5] (ground 1,312) | west (away from the wall): 180, 1024 | for A7 (held by `arrivals.yml`) |
| `thing:xd25_stair` | XD-25, inside at **(-2208, 1760, 256) facing east (0, 0)**: the cellar stair's top (XD-25's start); open from day one (the field of light inside drops with q-c5.pedestals, 112101) | the hatch's dark face (-11520, -9192, 1056..1200) | **(-11520, -9448, 1056)** before the hatch, cells [41.5, 82.45]; XD-25's cellar door uses it (landing 1,057) | south: 270, 1536 | live (`XD25_LIVE`) |
| `thing:xd26_eyrie` | XD-26, inside at **(1344, -1000, 0) facing north (90, 512)**: the cave mouth (XD-26's start) | the cave mouth's dark face (-9216, 11464, 1824..2178) | **(-9216, 11208, 1824)**; XD-26's mouth exit uses it (landing 1,821.5) | south: 270, 1536 | live (`XD26_LIVE`) |
| XD-26 sky crack | the ledge platform (-7808..-7040, 14336..14848), top 3,592 | - | **(-7424, 14592, 3600)**; XD-26's sky crack uses it (landing 3,593) | south: 270, 1536 | live (one way out of XD-26) |
| `thing:xd02_adit` | XD-02, inside at (2720, 5184, 256) facing east (0) | the doorway's dark face (20672, -16320, 1504..1824) at the foot of the red hill's west face (the hill 2,144, the pad 1,504), cells [104, 95.5], torches either side | **(20080, -16128, 1504)** for XD-02's adit exit, on the pad before it, cells [103.2, 95.5] | west: 180, 1024 | live, qbit 110020 |

A4's arrivals (`source/towns/x4.yml`):

| Arrival | (X, Y, Z) | Facing |
|---|---|---|
| `burlock_square` | (-1536, 3584, 1312), cells [61, 57] | south: 270, 1536 |
| `burlock_stables` | **(614, 4096, 1312)**, cells [65.2, 56]: before the Royal Stables' door (moved: the stables now stand at [66, 55], and [67, 57] fell on their wall) | west: 180, 1024 |
| `asp_travel_pit` | (-7168, -10240, 1056), cells [50, 84] | west: 180, 1024 |
| `asp_square` | (-12800, -11776, 1056), cells [39, 87] | north: 90, 512 |
| `x4_river_landing` | (9728, -18944, 736), cells [83, 101] | west: 180, 1024 |

**A7's exits onto X4, checked on the 2026-11-20 rebuild** (the dungeons' installed Lua, `MoveToMap`; ground from the built
height map and the ramp/ledge floors): XD-07 castle door (-1024, 6912, 1808): right, on the castle lane's ramp
(floor about 1,802; the older (-1024, 6768, 1760) was also on the ramp, floor 1,757.7, but is superseded). XD-07 throne
throw (-4608, 9728, 2504): right, a fall of 1,000 onto ground 1,504 (D-4). XD-26 mouth (-9216, 11208, 1824): right
(floor 1,820); the older (-9216, 11376, 2340) was wrong: 88 in front of the mouth's dark face, within the mouth's rock
(terrain 1,915 there; A7's run set the party down at 2,300-2,360, about 500 above the doorway's floor). XD-26 sky crack (-7424, 14592,
3600): right (the ledge's top 3,592). XD-25 cellar door (-11520, -9448, 1056): right (ground 1,056). XD-02 adit
(20080, -16128, 1504): right.

