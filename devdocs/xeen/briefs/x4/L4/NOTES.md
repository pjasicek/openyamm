# X4 Burlock Savannah: L2-L4 build notes (A5 sub-agent, 2026-11-20)

## State (2026-11-20, A5 tenth session): texture fit (merge point 16)

- **Installed with its bake 21:22:07** (after A1's 21:05:55 tile table, so the bake is fresh). The base course
  (`foundation` 128) fell back to the wall, so the plaster kit's `hhm2b2` showed 1.5 times up one-storey walls (4
  `trim_tiled` errors): gen.py gives every plaster plot a dark seamless stone footing (`textures.base: cwb1`); the
  L4 differs by that word only. Audit: 0 errors; the three known coplanar warnings inside the studio's own forms.
- `xkarrow` (the castle towers' arrow slits, one per storey) and the half-timber `hhm2*` panels are D-41 `module`
  panels: no finding now that the class file carries `storey_stack` (20:52). The slits stay in every storey of the
  towers (a `fit: true` window would leave the towers blank above the ground row).

- **Shop signs (A6's texture classes of 21:58: the MM7 `7sg*` signs are pictures meant once):** the kit hung them on 96 x 96 boards, showing the 64 x 64 picture 1.5 times (`feature_repeated`); the board now takes the picture's own size from `texture_classes.yml` (`sign_size`). Reinstalled with its bake in the second pass (`output/studio_cal/a5/fit/pipeline2.log`), walk and hostility 2/2 there.
- **The east edge to X7 (D-40), opened:** `places.X7_LIVE` (X7 installed with its row 9105): `edge:east` to X7's entrance:west_road (-22016, -1024, 1408) facing east, 5 days; X7's west edge returns to `entrance:east_road` (107, 66); the "Lava has crossed the road" sign gone. The walk crosses into X7 and back (gen_walk's X7 leg).

### Texture fit exceptions

None.

## State (2026-11-20, 20:08: the west edge to X6 open, the castle gate in two leaves)

**Ninth A5 session (20:03 and 20:08:46, both by install_baked.sh, bake fresh):** the west edge to X6 open (`places.X6_LIVE`, the gen.py neighbour with X6's arrival, the road-end sign dropped); the walk crosses it into X6 and loads back (`run/s9_walk1.log`, `s9_walk2.log`, 411 steps 2 of 2 on the 20:03 install; hostility 2 of 2). Merge point 15's door check: `thing:castle_gate` is a doorway of two leaves (chb1dl and its mirror, `places.DOORWAY_LEAVES`); reinstalled 20:08:46; audit 0 errors (`run/audit_s9.txt`). POIs 52 (the sign gone). Walk and hostility after it: `run/s9b_*.log`.

## Earlier state (2026-11-20, 16:55: the south edge by edge_spans, installed with its bake by install_baked.sh)

**Latest pass (16:50-16:58):** D-11.6's workaround gone (no step plate, no barrier along y 107.5; the X3 neighbour
has `span: [-32768, 0]` and its arrival); installed by `output/studio_cal/a5/install_baked.sh` (staged install, bake
from the stage with `--sources assets_source`, swapped in back to back) at **16:55:28** (`run/install_baked_7.log`);
`stale_bakes.py`: 0 stale; stage removed. Audit (`run/audit_final_7.txt`): no error, the same three coplanar warnings,
dressing clean. POIs 53, wild land 0.157, 6,000 rule 6,069 at [54, 24] (`run/measure_final_7.txt`). On `build-xeen`
16:42: walk 399 steps **2 of 2** (`run/walk_51.log`, `walk_52.log`: the south edge west of x 0 into X3 at
(-7168, 22016), east of x 0 into X2), hostility **2 of 2** (`host_51.log`, `host_52.log`), arrivals pass
(`arrivals_7.log`), A1's `tests/scenarios/xeen/edge_spans.yml` passes (`edge_spans_7.log`, X3's leg included).
Town feel exceptions below.

### Earlier pass (16:44): rebuilt, installed and baked; the three dungeon doors open, D-20's cuts

**Latest pass (16:29-16:47):** decoration swaps (below), XD-07/XD-25/XD-26 doors live, D-20's POI cuts. Installed
16:29:04 (`run/install_6.log`), baked 16:44:12 straight after in the same command line (`run/bake_6.log`; it waited
for X2's bake on the Blender lock); `stale_bakes.py` does not list xeen_x4. Minimap unchanged (no land change).
`oymap audit` of the installed map (`run/audit_final_6.txt`): no error; the same three coplanar warnings; dressing 460
props (the bound `bush03` is no longer a prop), 32 house doors, 23 walking lines, no error, no warning. Measured
(`run/measure_final_6.txt`): **POIs 53 by D-20's census** (band 35-55; the 12 service doors count one each, the camps
and Asp's pedestal ring with its well and rule stone one spot each); wild land 0.157; 6,000 rule farthest 6,069 at
[54, 24] (one rim-crest tile, as before), over 3,000 0.188; hostiles 135.5; chests 10. Checks on `build-xeen` (16:06
binary, exit 0, no shutdown crash): `playtest.yml` 397 steps **2 of 2** (`run/walk_41.log`, `walk_42.log`: now enters
XD-25 at (-2208, 1760, 256), XD-07 at (0, 384, 0), XD-26 at (1344, -1000, 0) and comes back), `playtest_hostility.yml`
52 steps **2 of 2** (`host_41.log`, `host_42.log`), `arrivals.yml` 58 steps (A7's exits and the postern point
included) **pass** (`arrivals_6.log`). Pictures: `tour/d/` (sheet `tour/sheet_d.jpg`): the postern point, the open gate,
the hatch, the eyrie mouth, the three camps, the lists' flags. The figures below are the 16:05 pass's unless they say so.

**Installed in assets_dev** (`output/studio_cal/x4/vw.sh --install`: map, scene, studio sidecar, `events/maps/xeen_x4.lua`,
`terrain_materials/xeen_x4*` through `output/studio_cal/a5/terrain_swap.sh`) at 16:02:46, **baked right after** at
16:05:17 (`output/studio_cal/x4/present/redo.sh bake`: its own `bake_profile.json`, no texture source root needed,
Blender under `output/studio_cal/a5/locks/blender.lock`); `tools/lighting/stale_bakes.py` does not list xeen_x4. Minimap
`icons_x2/xeen_x4.png` (15:36; the map's outline has not changed since). A2 wrote map_stats 9102 and the travel rows.

How to run: `vw.sh` (generate L1-L4, fmt, validate, build into `build_w`, `tools/measure_x4.py`, X1's dress_check);
`vw.sh --install` and then at once `present/redo.sh bake` (never install without the bake straight after).
Checks: `tools/gen_walk.py <L4> <build_w> assets_dev` -> `playtest.yml`; `tools/gen_hostility_x4.py` ->
`playtest_hostility.yml`; `tools/gen_arrivals.py` -> `output/studio_cal/x4/run/arrivals.yml` (every DOORS.md arrival
holds the party); `output/studio_cal/x4/walk_world.sh <scenario> <log>` runs one headless in a lane game slot;
`tools/gen_tour.py <name>` writes a review tour; `tools/doors_x4.py` reads the built doors and arrival heights;
`tools/mirror_x4.py` the Burlock doors' mirror pairs (TOWN_FEEL 2).

Measured on the installed build (`tools/measure_x4.py`, `output/studio_cal/x4/run/measure_final.txt`):
- hostiles at load 135.5 (45 markers: renegades 12, ogres 15, gargoyles 18; 14 placed); chests 10.
- first fights (D-15: edge arrivals and the new-game start only): X2's south start 5,247, the X3 arrival at x 36 3,578,
  the build's start (Asp's square) 3,826. Town buffer (2,500, no upper limit): nearest hostile to a town door 3,001;
  burlock_square 8,774, burlock_stables 7,675, asp_travel_pit 6,248 (D-15's recheck: over 2,500), asp_square 3,826.
  Dungeon-exit arrivals under the 6,000 rule (XD-02's adit 1,856 from the ogres' camp).
- POIs by D-15's census (chained within 400, service doors, mirrors and A4's outdoor NPCs in, residences out): 72,
  superseded by D-20's census (`tools/measure_x4.py`): **53** after D-20's cuts (the cairn by the bridge, the jouster's
  grave and the red waymark are dressing; the barrow stone's and the graves' lines are their chests'; each camp's chest
  within 400 of its fire). The eyrie waystone and the boundary stone keep their clicks (53 is under 55).
- 6,000 rule: farthest land 6,072 at [54, 24] (the range's crest by the rim, one tile); land more than 3 cells from
  anything 0.159 (D-11.5: about 0.16); more than 3,000 from a place or fight 0.202. Three devices were added for it:
  the climbers' cairn [40.5, 26.6] (+5 Luck), the wind stone [75.5, 26.6] (+5 Speed), a climber's bones [22.4, 27.4].
- textures 58 of the outdoor cap 120 (2 new: xnpedred, xnpedblu); road tiles 1.4 %; decorations 1,360.
- `oymap audit assets_dev/.../xeen_x4.odm --world xeen --reach --solve`: three coplanar pairs inside the studio's own
  forms (the ruined watch post's caps, 23 square units, the `ruin` defect X2 noted; the waterfall's water and bank
  rims, 63-73 square units), nothing else; the dressing audit of the brief: 583 props, 32 house doors, 23 walking
  lines, **no error, no warning**. `oymap fmt --check` clean on L1-L4. `tools/xeen/towns.py --strict`: nothing for X4.
- Build warnings kept (11): the XD-25 hatch's back edge stands as a step (from behind it reads as a grass hump, tour
  b `18-asp_stair_from_behind`); the falls' cut land; 5 road cells merged; the King's Bridge's 4 water cells (the
  bridge carries the road); 2 west-downs trees found no place; the informational "not built yet" lines.
- Town feel (`openyamm-studio/calibration/town_feel.py`, `output/studio_cal/x4/run/town_feel_{burlock,asp}.txt`):
  Burlock's mirror share 0.86 -> 0.57 (houses moved and turned: the tavern, weapons and armour shops shifted, the
  training hall faces south, three cottages turned), its lanes now dirt (soil from the square to the doors and the
  south gate). Left outside the ranges, with the reason: the monster figures (the checker reads spawn rows from the
  engine's table, not world xeen's: it sees only placed groups), residences 0 (it reads house types from the engine's
  house_data), the towns' spread and coverage (a walled village of 14 doors and a cursed hamlet, smaller than any
  shipped town), Asp's road off the compass axes (the Asp road crosses the town on the diagonal L1 drew), flat land
  0.98 in Burlock (the walled village is one terrace).

Walk and hostility (all from assets_dev, `output/studio_cal/x4/run/`):
- `playtest.yml` 394 steps: **2 of 2** on the final install (`walk_31.log`, `walk_32.log`), and clean on the
  earlier binary (`walk_11.log`, exit 0). It solves the pedestals (a wrong touch undone, then 1/3/5/7 red: 112101),
  checks the closed texts and, with q-c5.done, the house screens of Asp; walks onto the Asp road's plate (now the edge) into X3
  (`xeen_x3.odm` at X3's north start), burns the barbarian camp (No, then Yes: 116060), opens Burlock's six services,
  the mirror, well and herald; the castle gate's line; the lists' refusal; the Olympian Fountain once; Carlawna,
  Falagar, Joe, Adam, Eve and the Autumn Druid; the eyrie's and the undercroft's lines; the renegades' and the ogres'
  camps; XD-02's adit refused, then with 110020 entered (`xeen_xd02.blv` at (2720, 5184)); the south edge to X2.
- `playtest_hostility.yml` 52 steps: **2 of 2** (`host_31.log`, `host_32.log`).
- `arrivals.yml` 54 steps: every arrival of DOORS.md holds the party (`arrivals_4.log`).
- The binary rebuilt at 15:52:52 segfaults at shutdown after the last step of every headless scenario (X2's too):
  the runs above log every step PASS and exit 139 (reported to A1 through the lead).

Pictures (HUD off, noon): `output/studio_cal/x4/tour/a/` (30 shots, sheets `sheet_a_1..5.jpg`), `tour/b/` (32 shots
on the near-final install; `sheet_b_*.jpg` the changed spots), `tour/c/` (the castle gate and the adit, final).
Fixed from them: the King's Guards stood in the south and east gateways (now beside them); the castle gate was a
128-wide house door (now `thing:castle_gate`, a 384 x 448 door in a stone frame); XD-02's adit sat on the edge of a
drop with no hill behind it, then half buried in the slope (now at the foot of a 2,144 hill's face with two torches).

## Dressing exceptions

None: the D-7 audit of the installed map has no error and no warning (2026-11-20 16:3x rebuild too: 583 props, 32
house doors, 23 walking lines). The audit's only warnings are the three coplanar pairs inside the studio's own forms
(the ruined watch post's caps, 23 square units; the waterfall's water and bank rims, 63-73 square units), unchanged
since the first install.

## Town feel exceptions

D-20 (1): `town_feel.py --small` (TOWN_FEEL.md §5c, world xeen's own monster and house tables), 2026-11-20 16:5x,
`output/studio_cal/x4/run/town_feel_small_{burlock,asp}_p.txt` (`--project` on a scratch build; Asp measured with its
houses open as after q-c5.done, `X4_ASP_OPEN=1`, since the checker counts a condition-gated door as no house). Burlock
3 out, Asp 7 out; kept, one line each:
- Burlock, straight road run, longest 1,024 (3,072-5,655): the walled village's ways are dirt lanes; the only road
  tiles inside are the King's road's stub at the south gate (the castle lane is a ramp, a structure).
- Burlock, thematic sprites per cell in town 0.076 (0-0.056): the barrel pairs by the walls, the hay by the stables
  and the square's flags in a walled village of 14 doors, smaller than any shipped town.
- Burlock and Asp, monsters within 1,500 of a wild road per 1,000 of road 0.0 (0.03-0.58): a map-wide figure; D-11.2
  keeps the markers 2,500 from town doors and arrivals and in their L1 areas off the roads (road tiles are 1.4 % of
  the land).
- Asp, road length on compass axes 0.28 (0.66-1.0), road turns of 80-100 deg 0.0 (0.36-1.0) and longest straight run
  2,611 (3,072-5,655): the Asp road crosses the hamlet on L1's approved diagonal, from the Asp gate fork to the south
  edge.
- Asp, stables rank from centre 0.93 (0-0.81): the Travel Pit stands at the east edge, outside the curse (WORLD_DESIGN
  5.1: open from day one).
- Asp, flat terrain share in town 0.98 (0.73-0.97): the hamlet is one terrace round the pedestal ring.
- Asp, built footprint covered by buildings 0.14 (0.15-0.37): the open square for D-4's eight pedestals, the well and
  the rule stone at the hamlet's middle.

## Decoration swaps (2026-11-20, 16:3x): kinds without a 3D model

Same places, same dressing rules, each to a bound kind: `6tree12` -> `tree29` (scatter.py SAV; 11 placed), `bush07` ->
`bush03` (scatter.py bushes; 122), `fla2__01` -> `fla1__01` (the lists' two flags), `fire01` -> `dec24` (the ogres' fire,
a campfire with a light), `rock66` -> `rock65` (the champions' barrow stone and the snakeskin graves), `rock67` ->
`rock68` (the wind stone and the standing stone, their clicks kept), `7dec24` -> `7dec21` (the barrel beside Joe's
bigbarel). Counted on the built scene: none of 7dec12, 7dec24, 7dec41, rock66, rock67, bush07, bush08, mushrm04,
mushrm06, tree43-46, 6tree12, fire01, fla2__01 is placed; every placed name has a binding but `haybale2` (no bound hay):
**3 hay bales stay** (two by Burlock's stables, one at Joe's wagon).

## What the user should look at

- The castle over the lists from the lists' south end (`tour/b/01`): the stands on the right and the village wall in
  front hide most of the castle; only the towers show at that distance.
- Burlock's square and gate (`tour/b/04`, `05`, `10`): the new gate, the dirt lanes, the houses after the asymmetry pass.
- The falls (`tour/a/12`): the sheet leans as a broad panel and the right-hand crag looks loose above it.
- Asp's pedestal ring with A6's caps (`tour/b/15`): the caps are wide and read as crates from the side.
- The eyrie ledge: the arrival check holds the party at 3,592, but a tour camera set there slid down the range
  (`tour/b/21`): look whether the ledge reads as a ledge.

## Next steps

1. XD-07's postern: A7 opens `exit:x4_moat` to the rise's west foot (-5120, 8448, 1312) facing west (DOORS.md).
2. West (X6) and east (X7) edges when those maps exist.

## What was built (L4)

- **L1 changes** (gen_l1.py): D-11.2 Shrine of Fire to [104, 46]; south fields 12 -> 9, west downs 7 -> 4 markers; three
  wandering pairs: knights 2 on the river road [85-88, 90-94], ogres 2 on the Firestone road [92-96, 71-75], and on the
  west road one ogre marker [40-43, 62-65] and one knight marker [52-55, 70-73]. D-11.5 devices: cairn [77, 77.5],
  herders' well [93, 50], standing stone [21, 83], jouster's grave [69, 106], eyrie waystone [42, 50.5], red waymark
  [104, 76] (44 POIs). D-11.6 notes on both south edges.
- **Land**: savannah 990-1,350 rising north; the Gargoyle Range to 3,900 (crest y 30), the rim cliff at y 24 over water
  0; castle rise 1,888 (terrace [56-68, 43-50]) with a 576 step over the walled village 1,312 ([55-69, 50-62]); lists
  1,088; Asp 1,056; river 640, banks 704; the falls from a tarn at 1,536 into the pool (waterfall structure); red hills to
  about 2,400; lava fields (wasteland ground) 1,600-1,900.
- **Burlock**: A4's 14 doors (4151-4156, 4158-4165) on L1's plots, the village wall with south and east gates, the
  castle lane as a ramp to the gate, Well of Might (+10 Might temporary), the mirror (`Xeen.useMirror(4157, ...)`), the
  herald's board, flags, barrel pairs against walls, hay by the stables. Castle Burlock (gate sealed with a line).
- **Lists**: tilt barrier (fence), stands on posts, two pavilions, the Master of the Lists' challenge (Might 30, once,
  +2,000 XP), flags.
- **Asp**: A4's 16 doors (4170-4176, 4178-4186; 4177 the mirror `thing:asp_mirror`), the well, eight pedestals (D-4),
  the rule stone (`q-c5.pedestal_rhyme`), the undercroft stair (hatch, sealed), Adam (4301) and Eve (4302), the town sign.
- **Savannah**: the Autumn Druid's ring (4321 inside), Carlawna's round hut (4166), Falagar's hut (4167), Joe's wagon
  (4320), Nystor's jetty, post (qbit 112461) and boathouse, the King's Bridge with its cairn, King Burlock's statue, five
  signposts (the Asp one calls `x4.sign_asp`), barbarian camp, renegade knights' camp (burn: +1,500), ogres' camp (burn:
  +1,500), quintain, Olympian Fountain (+2 Might permanent, once per party by map var, as X2's Sage's Fountain), Shrine
  of Fire (+5 Fire resistance permanent, once), burned caravan, rim lookout, mill ruin, obelisk, three wells, the eyrie
  mouth (sealed), the sky-crack ledge platform, the King's beacon, the XD-02 west adit (qbit 110020).
- **Chests (10, each with a reason)**: barbarian chief, renegades, ogres' loot, ore cart, gargoyle roost, burned
  strongbox, sunken barge, saddlebags, champions' barrow, sexton's chest.
- **Actors**: barbarians 11100 x4, 11101, 11102; ogres 11060 x3, 11061; renegades KNIGHT_ROWS (11680 x3, 11682); villagers
  (MM7 peasants as X2's), four King's Guards 11143 (friendly), three Asp townsfolk, the four NPCs.

## Slots (A2's map_rows, written 2026-11-20)

Map 9102: slot 1 `Xeen Renegade` (D-11.2: A2's own family, 11680 Renegade Jouster, 11681 Knight, 11682 Captain) Dif 1,
2-3, 27 %; slot 2 `Xeen Ogre` Dif 0, 2-3, 33 %; slot 3 `Xeen Gargoyle` Dif 1, 2-4, 40 %; music 29. Placed: the
renegades' camp three Jousters 11680 and their Captain 11682 (`KNIGHT_ROWS` in places.py). Unchanged on the 16:44 pass.

## Pedestals: the quest bit

A3's hook `q-c5.pedestals` sets qbit 112101; the map's timer (`evt:pedestals_set`) calls only the hook (the map no
longer sets the bit itself). The walk checks 112101 after the solution.

## Sealed exits and what opens them

- West edge (X6): **open since 2026-11-20 20:03** (`places.X6_LIVE`): A2's edge_spans row sends it to X6's (107, 60)
  = (22016, 2048, 1216) facing 1024; the sign at [19.8, 59.2] is gone; the walk crosses it and X6's walk comes back.
- East edge (X7): no neighbour; a sign at the road end. Open: set `LIVE` in gen.py, drop the sign.
- South edge (D-11.6): **since 2026-11-20 16:5x the world's `edge_spans` table** (A1's merge point 9) sends the side
  west of x 0 to X3's north arrival (-7168, 22016, 1120) and east of it to X2; X3's north edge comes to X4's x 36
  arrival (-14336, -22016, 992). The project's X3 neighbour carries `span: [-32768, 0]` with its arrival; the barrier
  along y 107.5 and the Asp road's step plate are gone.
- XD-07 castle gate (`thing:castle_gate`), XD-25 stair, XD-26 eyrie mouth: **open since 2026-11-20 16:3x**
  (`XD07_LIVE`, `XD25_LIVE`, `XD26_LIVE` in places.py, each `into` the dungeon's start: XD-07 (0, 384, 0) north,
  XD-25 (-2208, 1760, 256) east, XD-26 (1344, -1000, 0) north; no condition on any: XD-07's Crusaders' portcullis and
  XD-25's field of light are inside). XD-07's postern has no door on X4: its arrival is in DOORS.md.
- XD-02 west adit: live, condition qbit 110020; into XD-02 at (2720, 5184, 256) facing east, inside the collapsed adit
  past the fall (A7 to confirm or name its own arrival). Its outside arrival for XD-02's exit: DOORS.md.

## Words needed (workarounds)

- One edge, two destinations (D-11.6): answered by A1's `edge_spans` and the studio's `span` (merge point 9); the
  barrier and step plate are gone.
- `kind: barrier`: the schema's x-kinds lack `line` and `height` for barrier, so validate warns "does not apply" though
  `OutdoorThings.cpp raiseBarrier` reads them (A1: schema).
- No `question` word in the outdoor sketch (XD-05's wiring has one): raw Lua `evt.AskQuestion` on the tents.
- A texture swap back (`set_texture` from the texture an earlier swap set) is refused by validate; the pedestals use
  show/hide caps instead.
- The royal kit's MM6 textures (hcwall, hcwindo, hclgdr, cswl128, cstyl ...) are not textures of world xeen's outdoor
  builds ("the world xeen has no texture hcwall"); XD-07 (indoor) uses them. The castle stands in MM7 chb1 meanwhile.

## Original lines

To check and source with their aaze references before done: Sarah Slither's lisp (A4's greeting), the pedestal rhyme
(A3's hook text), "You have stumbled upon a Barbarian encampment. Burn?" (A3's hook note). Lines written here are ours.

**Obelisk (A5 lead, 2026-11-20 16:2x):** the obelisk calls A3's `obelisks.x4` (word, qbit 115043, autonote) instead of
the map's own line. Only `xeen_x4.lua` changed (map and scene identical, so the 16:05 bake stays fresh); checked
headless (`execute_event` of `evt:thing:obelisk`, the message, 115043 set).

## Eighteenth session (2026-11-21, A5): the eyrie arrival off its mound (merge point 25)

- `entrance:xd26_eyrie` [46, 41] (-9216, 11776, 2240; lifted +114 by the new studio, on the cave mound) is now
  [46, 43] = (-9216, 10752, 1792), 512 in front of the mouth's footprint on the eyrie path, facing south (1536, out
  of the dungeon; it faced north into the mountain). `tools/gen_l1.py` (POINTS and the plan entrance), backup
  `gen_l1.py.pre_s18`. No lift warning left; no plaza or square arrival changed height on X4.
- XD-26's `exit:x4_range` (A7) uses a raw point, (-9216, 11208, 1824), just in front of the footprint at floor level:
  it works; asked of A7 to use the name or (-9216, 10752, 1792) (its hint's "ground 2,330" is stale).
- Rebuilt (`vw.sh`), audit 0 errors (3 kept warnings), installed with its bake 06:22:24 (0 stale bakes). Walk 427 2/2,
  hostility 2/2, the new point stood on and walked off (`output/studio_cal/a5/s18/x4_*.log`); walk unchanged.

## Nineteenth session (A5, 2026-11-21)

- `entrance:xd02_adit` stood beside the adit's north wall facing into it ((20480, -15872), facing 0; the adit's model
  spans x 20384-20896, y -16320 to -15936). It now stands on the lane 416 before the face, (19968, -15872, 1504) facing
  1024, out of the adit (`tools/gen_l1.py`). For XD-02's `exit:x4_adit` (A7).
- The sky-crack ledge (768 x 512 at [49.5, 35.5], top 3,592) holds no grid node, so `entrance:xd26_sky_crack`
  (-7680, 14848, 3648) is on the peak's slope at the ledge's back edge. XD-26's raw point (-7424, 14592, 3600) is the
  ledge's centre, and the better landing. Both are stood on in `output/studio_cal/a5/s19/arrivals_x4.yml` (2/2).
- Only studio.yml changed (odm, scene and Lua byte-identical, so the bake stays fresh): installed 07:49:14. Audit 0
  errors (the 3 kept warnings). Walk 427 2/2 and hostility 2/2 from assets_dev (`output/studio_cal/a5/s19/x4_*.log`).

## Twenty-first session (A5, 2026-11-21): D-70, the temporary sources once a day

- Well of Might, Quintain, both Herders' wells (`herders_well` +5 Endurance, `savannah_well` +5 Might), Wayfarers'
  well, Standing stone, Climbers' cairn and Wind stone go through `places.daily()`: `Xeen.usedToday("x4_<thing>")`,
  `Xeen.markToday` and `evt.ForPlayer(Players.All)` before the gain; a second use the same day gives the refusal
  only (wells "The water is cool and refreshing.", the standing stone "No one seems to be listening.", the quintain,
  cairn and wind stone their own lines). Gain texts say "until you rest". Backup `x4/tools/places.py.pre_s21`.
- odm and scene byte-identical: Lua and studio.yml installed 08:26:10 (`a5/s21/stage_lua.sh`), bake fresh (0 stale).
- New `playtest_daily.yml` (`x4/tools/gen_daily.py`): two tilts give every member +5 Accuracy, not +10; after a rest
  0 and the quintain still refuses that day; the next day +5 again. 2/2 from assets_dev, walk 427 and hostility 2/2,
  audit 0 errors (3 kept warnings).

## Twenty-third session (A5, 2026-11-21): AU's night beds, the barbarian camp's buttons (D-72)

- AU's session 5 list copied into `output/studio_cal/a5/beds/x4.yml` (previous in `a5/beds/before_s23/`): nine
  `bed_night_*` (`xeen_amb_night`, `night_only`, `pan: false`) at the savannah beds' points; day lines unchanged.
- The barbarian camp's three tents (D-72: the message already ends on the question) ask one Yes/No prompt with
  buttons, "You have stumbled upon a Barbarian encampment. Burn?" (`AskChoiceWithAnswerSteps`, Yes step 1 calls
  `x4.barbarian_camp`, No step 2 the "leave the camp standing" line); no `SetMessage`, no typed answer
  (`tools/places.py`). The walk asserts the prompt's text before No and before Yes.
- Sketch diff: `sounds` and the three tents; audit 0 errors (3 kept). Installed with its bake
  (`output/studio_cal/a5/s23/pipeline.sh`); 0 stale.
- Walk 431, hostility 52 and playtest_daily 39, each 2/2 from assets_dev (`output/studio_cal/a5/s23/x4_*.log`).

## Twenty-sixth session (A5, 2026-11-21): D-85

- Joe the Merchant (4320, actor 34, (12083, -12186)) stood among four hostile markers: river-road pair 40 at 1,221
  and 39 at 2,991, red hills 21 at 1,600 and 18 at 2,765. Two area nodes changed in `tools/gen_l1.py` (backup
  `gen_l1.py.pre_s26`); counts and slots kept, no area added, the other nodes' markers unmoved:
  - `pop:pair_river_road` (slot 1, 2 markers): [85-88, 90-94] on the river road -> [88-90, 100-103] on the Rivercity
    road just past the landing fork, between Nystor's keep-clear and the X2 end's. The river road between Joe and the
    fork lies wholly within 5,888 of him, so the pair cannot stay on it. 39 -> (89.9, 100.0), 6,354 from Joe;
    40 -> (89.8, 101.8), 7,258. D-11.2 kept: 3,481 from the river landing, 4,159 from the X2 arrival (D-15's
    first-fight band 2,000-6,000; it was 5,247).
  - `pop:red_hills` (slot 2, 8 markers): the west corner cut back from [89, 88]/[92, 95]/[90, 80] to [97, 78],
    [98, 82], [100, 88], [100, 95]; all eight re-placed (18-25), nearest to Joe 21 at (98.4, 81.8), 6,340. None within
    4 cells of the adit (the adit's nearest hostile 2,977, was 2,240).
- Joe's nearest hostile: 1,221 before, 6,340 after; `check_d85.py` at 5,888 clean on every giver, so no warnings kept.
  Spawn totals 45 and per-slot counts (12/15/18) unchanged; "spawn points found no place" 0 before and after; the sketch
  differs by the two nodes, the plan by one note; the Lua is byte-identical.
- D-72: no typed-answer prompt in `xeen_x4.lua` (the camp's three tents already use `AskChoiceWithAnswerSteps`; the
  hooks the map calls ask nothing; `Xeen.useMirror` keeps its typed destination). No event changed.
- Audit 0 errors (the 3 kept coplanar warnings). Installed with its bake 19:32:59 (`output/studio_cal/a5/s26/
  pipeline.sh`), 0 stale. Walk 431, hostility 52 and playtest_daily 39, each 2/2 from assets_dev
  (`output/studio_cal/a5/s26/x4_walk_*.log`, `x4_host_*.log`, `x4_extra_*.log`).

## Twenty-ninth session (A5 s29, 2026-11-22, merge point 41 rebuild; run files output/studio_cal/a5/s29/)
- Rebuilt twice and installed with bakes (01:11-01:15, again ~01:21). D-91: the Autumn Druid (4321) on Druidess A 517,
  "her ring", a sketch relation {of: [517], toward: party, friendly} (517 is a hostile MMerge row: the walk's
  clear_hostiles killed her). F13/D-90 2: quintain, standing stone, the two crest stones, the lists, the knights' tents and
  the ogre camp write `evt.StatusText` (`places.status()`); quests.py open rows removed. F8: the Eyrie 640 wide. F16:
  trans 5007/5025/5026 (XD-02's adit: the standard window). gen_daily.py checks the status line.

## Thirtieth session (A5 s30, 2026-11-22; run files output/studio_cal/a5/s30/)
- D-91: the Autumn Druid (4321) on lane S's friendly row 11929 Xeen Druidess; `places.relations()` returns nothing
  (the map-wide 517 relation dropped; backup `places.py.pre_s30`). `key_npcs.py --write`: 0 errors. Installed with its
  bake 01:35; audit 0; walk, hostility, daily pass from assets_dev.

## The world's rim as void and hull (2026-11-23, agent `xeen-rimmap-a`; U-12, D-106, D-109, D-112, D-113)

Scripts and logs `output/xeen_rimmap_a/` (`build.sh x4`, `install.sh x4`, `tests.sh`; `x4/run/`). Regenerated twice
(the second from the first build's land), walk and daily playtests rewritten from the build (unchanged), installed
with its bake 15:35 (`--sources output/studio_cal/x4/present/srcroot`); minimap re-rendered and its void painted.
- **The rim.** The north rim sea `water:rim_sea` is `void:rim_sea` (y < 23); 32 hull pieces along the edge. The
  rescue (`evt:rim_fall`) has only 3 return points, (107, 27), (52, 27), (46, 27): the rest of the rim top lies on
  the Gargoyle range, which the party cannot reach from the start (wild.py keeps reachable level ground only). A party
  over the void anywhere is lifted to the nearest of the three. Shrine altars (D-103), campfires (D-104); the tents
  and the lists' pavilions single-sided, the ruins closed (F30/F31).
- **xd25_stair (F25, the kit's `SunkenEntrance`):** the mouth is a dark arched doorway in the end face, no land or
  water inside (before: grass and a water strip under the arch). `town_fit_check` 0; dropped from
  `town_fit_pending.yml`. Captures `output/xeen_rimmap_a/x4/cap_look2_before/` and `cap_look2_after/`.
- **The falls** (`thing:falls`, inland from the tarn to the pool at 640; not a rim fall, so no spillway, D-112 does
  not apply): the studio's F29 cut lowers 2 nodes under the sheet; it reads as before
  (`cap_look_before/`, `cap_look_after/`).
- Checks (build, private root and assets_dev): audit 0 errors, town fit 0, walls 0, doors 0, D-85/D-87 0, empty
  zones, props support, check_wild clean, house signs 0, `stale_bakes --check` 0.
- `check_faces` (41, all kept as known): `village_wall` coplanar 32 and `xd26_eyrie` 6 (same-facing pairs of the
  studio's wall and model joints), `falls` 2 (the sheet over the top water), `xd25_stair` back to back with
  `xd25_stair_cap` 1 (the kit's cap from the frame's back, as X1's culvert). Tents and ruins: 0.
- Build warning `gates.road_off` on `thing:kings_bridge` (line y 76, the road's tiles 76-77): not moved here.
- Tests: walk, daily, hostility from the root twice and from assets_dev pass.
- Captures `output/xeen_rimmap_a/x4/cap_after/` (rim low/along/high/mid day and night, the falls, the stair, the
  hull from the void day/night, the reachable rim at (46, 30), the far void); before `output/xeen_rim/before/x4/`.
