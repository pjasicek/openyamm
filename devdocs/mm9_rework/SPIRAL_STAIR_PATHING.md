# Spiral stair pathing in the Thousand Terrors

Status (2026-10-31): investigation done; option A1 (the data fix) is done, see [Done](#done-2026-10-31-option-a1) at the
end. Plan cost and worker queueing are measured in game in [Measured in game](#measured-in-game-2026-10-31).

Question: why do monsters not take the spiral stair between the crypts and the entrance level of the rebuilt
`1000terrors.blv`? Is the fault in our navigation, and should we use MM9's AI rails instead?

Short answer: there are three separate faults. Two are converter defects in the map data and cut off every body,
small or large. Fixing them in the data lets monks and demons plan the whole stair both ways in the engine's own
planner. The third fault hits only the Terrors. They are wider than the stair's bottom doorway, and the planner's body
shape makes squat bodies stall on every slab tread. MM9's rails would not fix the data holes, and they would add a
second navigation system. The recommendation is the data fix (option A1).

Scratch files are in `level_generation/projects/mm9r_1000terrors/work/pathing_investigation/` (called `work/pi/`
below).

## The stair

Measured from the built BLV (`util/map_export.py blv`):

| Item | Value (native units) |
| --- | --- |
| Centre, column | (7772, -6236); central column radius 97 |
| Treads | 63 treads and the landing, from the well floor (-2094) to the landing (-128); 16 treads per turn (22.5° each), so about 3.9 turns |
| Rise | 30.7 per tread (the monster step height is 40, the movement rise 50) |
| Tread band | radius 94 to 624 (530 wide); depth 141 at radius 360, 64 at radius 162 |
| Tread build | floating slabs 15–16 thick: a floor face, an underside (ceiling face) and sides; an open slot of about 15 under each tread edge |
| Headroom | 461–476 to the same tread one turn up |
| Bottom doorway | 246 wide (y -6359 to -6113 at x 8387–8571), 322 high, through the well wall (radius 626–665) |
| Top | landing at -128; exit 615 wide; the gate frame 430 wide and 343 high, with `StairGate` (door 105) and `StairGate0` (door 106) |
| Sector | the whole stair, the well floor and the landing are sector 18: no portal on the stair |

Bodies (MM9 tables in the review root): Monk 9123 radius 44, height 157; Lesser Demon 9241 radius 65, height 179;
Amphibious Terror 160 × 256; Desert Terror 9238 175 × 256; Reptilian Terror 9239 190 × 256.
The crypts hold 9 Lesser Demons, 6 Desert and Reptilian Terrors and 2 Sea Monsters (walkers).

## Findings

### 1. The old probe hit a closed gate, not the stair

`work/reach/probe_spiral.yml` (README "Audit") teleports the party from the entrance corridor to the crypt floor. The
demon then stops at (8235, -7124, -117). That point is in front of the gate frame (x 7875–8305, y -7055), south of
both StairGates. Both gates start closed (scene `doors`, state 2 = closed). The probe measured a shut door.
`work/pi/shots/04-top_gates.png` shows the shut gate from the landing.

In MM9 this is by design. `StairGate` opens when `LesserDemon0` (actor 76) dies, and its `OpenTrigger0` switches on rail
`AITrk57`, the only rail link between the stair and the entrance corridor (it starts off). So in MM9 too, the crypt
monsters cannot come up until that gate opens.

Side note: `StairGate0` has no opener in the built map Lua. In MM9 it is `DoorLock.scr "600; 1"`, `PushOpen`,
`AITriggerable`. Nothing sends it a message here, so it may stay shut for the party as well. The map owner should check.

### 2. A monster must see the party first

A demon spawned at the stair's foot with the party already on the landing never moves (`targeting_party=false` for
40 s). Every probe below therefore shows the party beside the monster for 1.5 s, then moves the party. This matches
the Ruined Temple note ("sight, not geometry").

### 3. In game, every body fails on the stair itself

The party is placed on the landing at (8100, -6900, -128), inside both gates. Headless runs:
`./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" --user-data "$PWD/work/pi/userdata_log"
--headless-run-scenario <yml>`. The user-data folder turns on `[logging] indoor_pathfinding`. The scenarios are made by
`work/pi/make.py`, and the logs keep only the probed actor.

| Probe | Body | Result over 40 s |
| --- | --- | --- |
| `up_monk` | 44 × 157 | climbs to -1019 (next to the -1050 hole), then stuck for 26 s |
| `up_demon` | 65 × 179 | erratic; stuck at -1050 for 22 s; at -527 when the run ends |
| `inside_demon` (starts in the well) | 65 × 179 | stuck at -558 for 28 s; reaches -159 at 40 s |
| `down_demon` | 65 × 179 | stays on the landing for 20 s, then stuck at -558 |
| `down_monk` | 44 × 157 | reaches the bottom in about 20 s |
| `up_terrorb`, `up_terrorc` | 175, 190 × 256 | never enter the well; wait on the crypt floor under the party (8100–8350, -7163) |
| `down_terrorb`, `down_terrorc` | 175, 190 × 256 | stay on the landing |
| `inside_terrorc` (starts in the well) | 190 × 256 | rocks on treads 1–3 (-2063 to -2007) for 40 s |
| `ctrl_demon_well` (plain floor, through the doorway) | 65 × 179 | closes to 363 of the party in 2 s |
| `ctrl_demon_floor`, `ctrl_terrorc_floor` (plain floor) | 65, 190 | close to 368 and 478 in 4 s, as monsters do |

The controls behave normally, so the failures belong to the stair. The demons' stall heights, -2033, -1050 and -558,
are exactly the tread holes of finding 4.

### 4. Why: three faults

All plan tests use `work/pi/path_harness`. This is the engine's own `PathMap.cpp` and `PathPlanner.cpp`, unchanged and
compiled standalone, with the request that `IndoorWorldRuntime` builds (step 40, step height 40, drop 100, riser 80,
8 000 nodes, partial paths). `dump_facets.py` writes the facets exactly as `IndoorPathfindingBuilder` does.
The harness reproduces the game's first plan exactly: `partial nodes=1709`, 13 672 candidates, 813 walk rejects.

**Fault 1: eight tread tops are missing (converter).** The converter dropped one small triangle (507 LT², `floor_tile_m.dtx`)
from the top of eight treads as "no air in front" (`work/dropped_faces.json`). The treads are at -2033, -1664, -1541,
-1172, -1050, -681, -558 and -189. Each hole is an 8° wedge across the full tread width (radius 94–624), so every
route up crosses it. The planner samples the floor every 2 units under the body's centre. Over a hole it finds the
tread one turn below (430–1905 lower), or it hits the kept underside, and it rejects the step. Bodies are wider than
the wedge and walk over it, so the demons crawl upward on direct steering between failed plans. That is the slow,
stalling climb. Four other treads (-1848, -1357, -865, -374) lost their underside instead, which is a visual fault only.

**Fault 2: a 3-unit crack at the top landing (converter, from MM9's brushes).** The landing face ends at y -6574 and
the exit floor starts at y -6577, both at -128. The 2-unit floor sampling falls into the gap onto the tread at -589,
a 461 drop, and the step is rejected. Whether a route gets across depends on where its lattice falls; the demon's never does.

**Fault 3: the Terrors (body size and body model).**
- The bottom doorway is 246 wide. A Terror is 320–380 wide in our tables, so it cannot enter the well at all.
- The planner's upper-body probe is a sphere of radius R at max(R, H−R) above the feet (`PathMap::traceWalkBody`).
  For a squat body (H < 2R + 15) that sphere reaches the underside of the next slab tread, 15.4 above the feet. The
  riser exemptions cover walls up to the step height and the low probe only, so every step is rejected. In the tread
  scan, radius 80 passes all 62 steps and radius 100 or more fails all 62.
- The same sphere needs 2R of headroom, not H. Where the exit slab hangs over the stair (its underside at -189), the
  clearance is 338–369, so radius 175 or more stalls there even without the slab undersides.

Not the cause: tread width (530), rise (30.7), turn radius, portals (none on the stair), the node limit (plans use at
most 4 300 of 8 000), or the movement code (bodies climb treads physically).

### 5. What the data fixes do (harness)

Plans from the crypt corridor (8968, -6236, -2079) to the landing (8100, -6900, -128) ("up"), and back ("down"):

| Facet set | Monk 44 | Demon 65 | Terror 160–190 |
| --- | --- | --- | --- |
| as built (`facets.txt`) | up partial (best -2033) | up partial (best -2033) | never enters the well (doorway) |
| + 8 tread tops (`extra_tread_tops.txt`) | up and down succeed | up stops at the landing crack; down partial (118 nodes) | unchanged |
| + tread tops + crack strip (`facets_fixed2.txt`) | up 998 nodes, down 1 738 | **up 1 030 nodes (265 ms), down 1 675 (656 ms)** | every tread rejected |
| + slab undersides non-blocking (`facets_fixed3.txt`), body placed in the well | succeed | succeed | 160: reaches the landing; 175 and 190: stall at -558/-589 under the exit slab |
| stair collision as an invisible ramp (`facets_ramp.txt`), in the well | succeed | succeed | 160 succeeds down, nearly up; 175 and 190 still stall at -527/-558 |

Tread-by-tread walk segments at radius 300–420 (`seg` mode): as built, 8 of 62 steps fail for radius 44 and 65, all at
the holes. With the fixes, none fail.

Cost: a plain-floor detour plan takes 8–10 ms. A full spiral plan takes 160–660 ms of one path worker. There are two
workers per world, and an actor replans at most once a second.

## Option A: our own navigation

### A1. Data only: restore the tread tops, close the crack (recommended)

- Converter (`mm9r_common/dungeon/rooms.assign_faces`): before dropping an up-facing polygon with no room, give it the
  room of a kept coplanar polygon of the same model that shares an edge with it. Alternatively, keep it by a map
  override. The tread triangle's quad neighbour on the same tread was kept.
- The crack: weld horizontal floor faces at the same height whose edges are within 4 units. Or add a filler strip in
  the map's `edit_polygons` hook (the harness strip: x 7772–8387, y -6578 to -6573, z -128).
- Effect: monks and demons (all the crypts' small walkers) path the whole stair both ways. Items and the party lose
  the holes too.
- MM6–MM8 risk: none (MM9 converter and map data only). The converter rule changes other MM9 maps' dropped faces.
  Rebuild them and rerun their audits.
- Performance: no engine change. Spiral chases now plan successfully, at about 0.3–0.7 s of worker time per plan.
  Watch for it in a desktop run with several demons. A4 removes that cost if it shows.
- Effort: half a day to a day, including the rebuild, the audit and the probes. Rerun `work/pi/up_demon.yml`,
  `down_demon.yml`, `up_monk.yml` and `down_monk.yml`: they should reach the landing and the foot.
- Still open: the Terrors. They keep to their level, and so does the Amphibious Terror at the stair top.

### A2. Data for the Terrors (not recommended)

Make the stair's slab undersides untouchable, or give the stair an invisible ramp as its collision, and widen the
bottom doorway. In the harness this is enough for radius 160, but not for 175 and 190 (the exit slab's headroom).
It changes MM9's look and still leaves the two largest Terrors stuck.

### A3. Engine: a cylinder body for squat walkers

- Change: in `PathMap::traceWalkBody`, test the upper body as a cylinder. Skip faces that lie below the feet plus
  `riserHeight` and that the low probe already exempts (risers, step undersides). Check overhead clearance against H,
  not 2R. The movement controller should get the same rule if it rocks on the treads too (`inside_terrorc`).
- MM6–MM8 risk: medium. 256 of the 655 engine descriptor rows are squat by this measure (H < 2R + 15: rats, spiders,
  dragons, behemoths, beholders). Their routes near stairs and low ceilings would change, mostly for the better.
  A low ceiling right over the body must still block.
- Tests: a PathMap unit test with slab treads and a squat body; a test that a low ceiling still blocks; the existing
  pathing and actor tests; MM8 headless chases on stairs.
- Performance: neutral. Effort: one to two days. The 246-wide doorway still keeps radius 160 and above out of this
  well, so it needs a data decision as well.

### A4. Engine: navigation links (only if spiral plans prove too slow)

Add per-map links: a polyline from the foot to the top, authored in the scene or derived from MM9's rails. The planner
treats a link as one edge and follows its points as waypoints. Plans drop from about 0.3 s to milliseconds. Maps
without links are unchanged, so the MM6–MM8 risk is low. Effort: two to four days.

## Option B: MM9's AI rails

What they are (DAT, read with `transcode_mm9_dat_to_odm.read_dat_world`; `work/pi/aitrk_1000terrors.json`,
`airail_1000terrors.json`):
- Each rail is an `AIRail` object with a brush `AITrk<n>`. Most brushes are flat boxes, 16 LT thick, over a walkable
  area. The Thousand Terrors has 363 rails. 330 start on and 33 start off; triggers switch them (`AITrk57 on` from
  `StairGate`, `AITrk151 off` from the button puzzle).
- Properties: `StartOn`, `RailLink0-3` (explicit links; 154 rails have them, 209 have none and presumably join by
  touching), `OneWayOnly`, `IsLadder`, `NoRunZone` (all 0 here). Monsters carry `UsesRails 1`, `RailDist 14400`,
  `RailCheckInterval 0.25`, `MaxRailPath`, `CanReachAll`.
- `object.lto` has `FindRail`, `BuildRailPath`, "Off rail, but heading towards next rail path" and `CheckForAIBarrier`.
  The joining rule for unlinked rails can be confirmed there with Rizin; it was not done here.
- The spiral is about 41 boxes, `AITrk181`–`AITrk221`. Each covers 1–2 treads, is 287–460 wide (native) and steps
  41–61 at a time. The top joins the corridor only through `AITrk57`.
- Use: 18 of the 24 built BLVs have rails (Thousand Terrors 363, Chasm 790, Thjorad Mine 580, Lich Lab 516, Beethoven
  436, Drangheim Prison 406, ...; `work/pi/rails_survey.txt`). Bath House, Connecting Tunnels, Dark Passageway,
  Dragon Stadium, Dungeon of Secrets and the Hall of the Gods have none. Many outdoor maps have them too.

What it would take:
- Converter: export each map's rails (footprint, top height, links, start state, flags) to a scene block. The map Lua
  dispatcher must also pass rail on/off messages to the engine. About a day.
- Engine: a rail graph per indoor map, with state saved in the map delta. Plan with A* over the rails (a few hundred
  nodes), turn the rail chain into waypoints, and keep the lattice planner for the ends (monster to rail, rail to
  party). Add debug drawing and tests. About five to eight days.
- MM6–MM8 risk: low if the code runs only when a map has rails. Performance: rail plans are cheap; following is as today.

Cons:
- It is a second navigation system beside ours, and six built maps have no rails.
- Rails know nothing of our body sizes. The rail through the bottom doorway is 96 LT wide, as wide as the door, so a
  Terror would follow it into a doorway it cannot pass.
- It does not fix the holes and the crack. Those also affect the party, items and our planner wherever no rail covers.
- The rail semantics (joining, one-way, ladders, barriers) need more reverse engineering.

A cheap use of the rails without the runtime: as an audit check. Where two rails join but our planner finds no route
for a small body, the audit has found a real fault like faults 1 and 2.

## Other built maps (quick survey)

`work/pi/survey_holes.py` lists up-facing faces dropped beside a floor of the same height that leave a hole. It is
noisy: tops of beams and ceilings show up too. `work/pi/survey_stairs.py` counts slab treads and squat walkers.

- Holes worth a look: Drangheim Prison (70 dropped metal floor faces at cell-walkway heights, `pr_metal_riv`), Temple of
  Honk (17 `honkfloor4` tiles at 515), Anskram Keep (5 `anskramwood` planks at 0), Connecting Tunnels (46, mostly
  `woodgrain02`). In the Thousand Terrors the survey finds exactly the 8 tread holes.
- Squat or large walkers on stair maps: Anskram Keep (40 Imps and Nagates, 109–250 radius; its spiral has 61 risers,
  which no monster or party can climb: a separate, known limit), Beethoven (18 Lobbers 112 × 199, 78 slab treads),
  Chasm of the Dead (7 Imp Elders 125 × 200), Drangheim Prison (3 Nagate Elders 138 × 154), Dark Passageway (Sea
  Monsters 192–230). Fault 3's slab rule applies to them wherever their stairs are slab-built.
- Other spiral stairs (from their READMEs): Inventa Storca (exit stair, 61–92 risers), Yanmir's Fort (basement),
  Verhoffin Ruins (start), Ruined Temple (ramps; a radius-64 Dagrell reaches the party). Their walkers are radius
  below 100, so faults 1 and 2 are what to check there. Rerun `survey_holes.py` after the converter fix.

## Recommendation

1. Do A1: restore the dropped tread tops with the shared converter rule and close the landing crack. Rebuild, then
   rerun the four stair probes and the audit. This keeps our own navigation and needs no engine change.
2. Accept that the Terrors keep to their level. They do not fit the bottom doorway, and it is not shown that MM9's
   Terrors pass it either. If the user wants them to follow, do A3 and decide on the doorway (widen it, or use MM9's
   real collision size if that is smaller than our extents-based radius).
3. Keep rails out of the runtime. Consider the audit check above.
4. Small follow-ups: correct the README's "stalls at the first step" note (it was the gate); check that `StairGate0` can
   be opened; give future chase probes a sighting phase.

## Files

- Scenarios and logs: `work/pi/{up,down,inside}_{monk,demon,terrorb,terrorc}.yml|.log`, `ctrl_*.yml|.log`; generator
  `make.py`; `userdata_log/settings.ini` turns on path logging.
- Harness: `path_harness.cpp` (build line in the file), `dump_facets.py`, the facet sets `facets*.txt` and the extra
  faces `extra_*.txt`.
- Rails: `aitrk_1000terrors.json`, `airail_1000terrors.json`, `rails_survey.txt`. Surveys: `survey_holes.*`,
  `survey_stairs.*`.
- Screenshots: `shots/03-bottom_doorway.png` (the 246-wide doorway into the well), `shots/04-top_gates.png` (the shut
  StairGate seen from the landing).

## Done (2026-10-31, option A1)

Work files: `level_generation/projects/mm9r_1000terrors/work/floor_holes/` (`fh/` below).

- **Converter rule** (`mm9r_common/dungeon/floors.py`, called from `rooms.assign_faces` and `build.Build.geometry`; on
  by
  default, opt out with `map: {restore_floor_holes: false, weld_floor_cracks: false}`): a dropped up-facing polygon is
  kept when a kept coplanar polygon of the same model and role shares an edge with it and labelled air lies above it
  with no polygon in between (it takes that polygon's room); same-height horizontal floors whose facing edges are at most
  6 units apart get a strip over the crack. The build now prints `WARNING: n floor holes` / `n floor cracks` for what is
  left and writes `work/floor_holes.json`. Details and numbers: the playbook's Thousand Terrors section.
- **Proof:** the 24 built dungeons scratch-built before and after (`fh/compare_before_final.txt`): 18 byte-identical, 6
  changed, and every restored face and weld is a hole in the installed BLV (`fh/hole_proof.py`). Lich Lab changes too
  (3 grate pieces of 80 LT² at its tables' feet, 10 units over the face below); with both settings off it is
  byte-identical to before (`fh/optout_check.py`).
- **The Thousand Terrors:** the 8 tread tops restored, the landing crack (x 7772-8387, y -6577 to -6574, z -128) and a
  4-5.5-unit crack in the crypts welded; 17 779 faces. Drangheim Prison, Anskram Keep and Connecting Tunnels are
  unchanged: their survey hits are tops under walls and the backs of the mine beams (no labelled air above, `fh/diag_*.txt`),
  not holes. The Temple of Honk gains 4 floor tiles, Lindisfarne 38 cracks welded, the Hall of the Gods 1, Verhoffin
  Ruins 2 crevasse ledges and 1 wading-water quad.
- **Rebuilt maps:** the six changed maps are installed in the review root and rebaked through `bake_slot.sh`;
  `tools/lighting/stale_bakes.py --assets output/mm9_rework/assets_dev --check` lists no MM9 map. Their scenarios pass
  (Thousand Terrors 3, Temple of Honk 4, Lich Lab 3, Verhoffin Ruins 3, Lindisfarne 4, Hall of the Gods 4); their
  walkability audits are unchanged except Verhoffin Ruins (its README). Screenshots before/after: `fh/shots/` (the
  Terrors' treads and landing, Verhoffin's water quad and ledges, Lindisfarne's cracks).
- **Stair probes** (`work/pi/{up,down}_{demon,monk}.yml` unchanged, logs in `fh/probes/`): all four reach the far end.
  Up:
  the demon is on the landing (-128) after about 10 s and stops 365 from the party; the monk after 10 s, 350 away. Down:
  the demon reaches the well's doorway (-2087) in about 8 s, 370 from the party; the monk in 6 s. Before: up stalls at
  the tread holes for 22-26 s, the down demon stuck at -558.
- **StairGate0** (door 106): MM9 gives it `DoorLock.scr "600; 1"` but `Locked 0`, `PushOpen 1`, `AITriggerable 1` and no
  object sends it a message: a plain use opens it (the script only takes the Stairs Key, item 600 from TreasureChest5,
  from a party that carries it). Now event 369 (a click: open/close, the key taken) and a poll that opens it for a hostile
  monster beside it (on the landing, or south of it once StairGate is open). It does not shut after MM9's 10 s, since our
  monsters cannot open it again. `scenario_scripted.yml` proves the real click (StairGate stays shut) and the monster push.
- **The Terrors' collision size:** MM9 gives all three Terrors `models\Terror.abc`, whose 15 AnimBindings all have
  half-extents (25, 50, 25) LT, with `Scale` 1 (`MONSTERS.txt` rows 237-239 and every DAT object): radius **64**, height
  256 native. Our 160/175/190 come from the MM8 Behemoth stand-in rows (`tools/mm9_import_discovery/
  mm9_monster_legacy_replacements.tsv` 237-239 -> 208-210, copied whole by `generate_mm9_monster_tables.py`). At radius 64
  (128 wide) they fit the 246-wide doorway, and they are not squat (256 > 2 x 64 + 15), so the slab treads would not stop
  them either. The change that applies it: the `Radius` column (4th) of rows 9237-9239 in `worlds/mm9/data_tables/
  monster_descriptors.txt` to 64, made in the generator or as a per-row override (the file is generated), not in the
  review copy; or per actor in `convert.py` (as Dook's Castle does), which misses the spawned Terrors. **Applied
  2026-10-31** with every other MM9 row's body ([monster collision](MM9_MONSTER_COLLISION_RE.md#applied-2026-10-31)):
  rows 9237-9239 are 64 x 256. Headless on the review root (unrebuilt map, new table): a spawned Desert Terror (9238)
  at the stair's foot (8872, -6236, -2079) climbs the well to the landing (8103, -6551, -128) in about 12 s
  (`up_terrorb.yml` of `work/pathing_investigation/`); at 175 it never entered the well. The placed Terrors keep 160-190
  until the Thousand Terrors is rebuilt.
  Not proven from the binary: no MM9 script sets dims, the Terror classes in `object.lto` only override `Filename`; that
  LithTech sizes the body from the animation dims is the usual rule, not traced (no Rizin on the host).
- **Open:** the Terrors' size (above); the walkability audit still calls the crypts unreachable (its lattice treats the
  shut StairGates as walls); spiral plans cost 0.3-0.7 s of a path worker (not measured in a desktop run).

## Done (2026-10-31, option A3): squat bodies on stairs

A body is **squat** when it is wider than it is tall (height < 2 × radius). The planner's upper sphere then sits at its
radius, reaches down to its feet and up to 2R, so it hit the next slab tread's underside on every step and needed 2R of
headroom. Indoors only (the riser rule, `riserHeight > 0`); bodies taller than they are wide are unchanged by
construction. Pathing doc: [Monster pursuit](../ACTOR_PURSUIT_AND_REACH.md#squat-bodies-on-stairs).

Change:
- `PathMap::traceWalkBody` (`game/pathfinding/PathMap.cpp`): for a squat body the obstacle loop skips a face wholly over
  its head, and a face it climbs (`PathMap::isClimbedStepFace`, new): within `riserHeight` of the feet, either a step's
  underside (a ceiling face with a floor at most 24 above it) or a riser (a wall facing the move within 60° whose top
  meets a floor). A railing (no floor on its top), a stair's side (it runs along the move), a ceiling under the head and
  a lintel still block.
- `IndoorMovementController::resolveMoveSingleStep`: the game run showed the same stall in movement (the Terror stood
  `ceiling_floor_crush` under the next tread). For a squat body: the leading floor probe looks 64 ahead, not its radius
  (at 190 it passed over the next tread onto the floor under the stair); it steps up early from any face at its own
  height (a tread built of two faces); and its sweep ignores faces wholly over its head.
- Tests (`tests/PathMapTests.cpp`): "squat body climbs slab treads ..." (fails on the old code, as does the ceiling at
  260 and the lintel at 270) and "squat body is still blocked by low ceilings, railings and narrow doorways" (low
  ceiling, railing, stair side, jambs 200 and 400 apart, lintel 230).

Regression (frozen binaries, before = 10:34 build, after = final):

| Check | Before | After |
| --- | --- | --- |
| `openyamm_unit_tests` | 2 396 / 2 396 | 2 411 / 2 411 (2 new here; the rest other sessions' new tests) |
| `openyamm_runtime_tests` | 54 / 55 (New Sorpigal braziers) | 54 / 55 (the same case) |
| `indoor` regression suite (`--world mm8`) | 174 / 174 | 174 / 174 |

MM6-MM8 routes (`work/pi/compare_mm678.py`, engine planner old against new): 115 indoor maps, 12 pairs of spawn points
at different heights each, five squat sizes (giant rat 32 × 42 to ancient behemoth 190 × 256) and a thief control:
8 220 plans. Control 1 370 of 1 370 identical. Squat: 5 264 identical, 1 204 the same end by another route, 75 partial
plans now succeed, 70 no-route now reach part or all of the way, 39 partial plans end farther (more than 64; partial
ends are heuristic). No success became a failure. Mean plan time 241 → 253 ms (+5 %, parallel run).

MM6-MM8 chases in game (`work/pi/mm678_chases/`, the map's monsters killed, the monster sees the party, then the party
stands at the far end, 40 s): 16 cases on d05, d13, d44, d45, 7d26, 7d28, 7d34, 7d37, mdr05 and mdt10. 12 end within
20 units of before; 2 closer (d05 giant spider by 228, mdt10 spider by 75); 2 farther (7d26 spider 407 from the party
instead of 253, on the same level; mdt10 giant rat by 147, 1 666 away, on a 17-high step instead of the floor). The
planner's "better" cases do not show in game: those monsters stop for other reasons (sight, stand-off distance), as before.

The Thousand Terrors (map with A1's fixes, built 11:13):

| Probe | Before | After |
| --- | --- | --- |
| demon, monk up and down | reach the far end | identical (not squat) |
| Terror 190 placed in the well, party on the landing | rocks on treads 1-3 | climbs to -927 in 8 s, then stops |
| Terror 190 on the landing, party at the foot | stays on the landing | descends to -896 |
| Terror 190 at the foot, outside the well | stays (246 doorway) | stays (246 doorway) |

Plan cost (harness, best of five, machine busy with the regression run): the Terror's spiral plan now succeeds or reaches
the landing and costs 0.6-1.05 s of a path worker (1 000-1 700 nodes); before it failed in 25-160 ms. Demon and monk plans
are node-for-node identical (0.2-0.7 s). At MM9's own Terror radius 64 (above) the body is not squat and plans in
0.25-0.55 s.

Open:
- The Terror still stops at -927 going up: the movement sweep's spheres (radius 190) touch the column (radius 97) and
  the tread edges two steps ahead, and other monsters in the well block it. A radius-190 body has 149 of the 530-wide
  tread band to use. With MM9's real radius 64 none of this applies; the descriptor change above is the better fix.
- Bodies exactly 2R tall (an Ogre Brawler 90 × 180) are not squat by this rule; their upper sphere reaches 0-15 above
  the feet and still stops on slab treads (none of the MM9 rows on slab-stair maps is in that band).
- A squat body's ledge look-ahead is 64 instead of its radius.

## Measured in game (2026-10-31)

Question: how expensive spiral plans are in the real game, and whether they make the two path workers queue up.
Short answer: a full spiral plan costs 0.1-0.25 s of a worker on a quiet machine (2-4 times the per-node cost of
an MM8 or MM7 dungeon, about the same per plan as MM7's long stair routes). Up to six chasing demons, the workers stay
below a third busy and the queue is empty. Ten demons with the party running across the crypt every 3 s fill both
workers when the machine is contended. The long waits a monster sees (1-4 s for a new route) come mostly from the
main thread's map-wide plan throttle, and MM7 has them as well. The recommendation is to keep the code as it is (see
the end of this section).

Work files are in `level_generation/projects/mm9r_1000terrors/work/path_cost_measurement/` (`pcm/` below).

### Method

- Existing logs do not give these numbers. `logging.indoor_pathfinding` prints each consumed plan (status, nodes,
  candidates, discards), but no time, queue time or worker. `logging.performance_trace` (`[IndoorActorAiPerf]`) prints
  only main-thread costs and counts per second. Nothing records when a plan is queued, when a worker starts it or how
  long it runs.
- So there was no engine change and no build. `pcm/tracer.py` is a gdb Python script on an unmodified, frozen copy of
  the Release binary (`build/game/openyamm` of 12:34, sha1 7282b04d). It sets non-stopping breakpoints on
  `ActorPathRuntime::queuePlan` (queue time, actor, body, sim time), on `PathPlanner::plan` entry and on its two
  return sites (worker or main thread, status, nodes), on `ActorPathRuntime::clear` (a settled door drops every route)
  and on the path map build. Each hit pauses the game for about 0.3 ms. That 0.3 ms is the floor of every wait below.
- Cases (`pcm/gen.py`; each one is both a headless scenario and a desktop console tour). The map's own monsters are
  killed first, the spawned ones see the party for 1.5 s, and the party is then moved. Probes run for 30 s.
  - `up_<body><n>`: n monsters at the stair's foot; the party waits on the top landing.
  - `kite_demon<n>`: n demons on the landing; the party then moves between the stair's foot and a crypt-floor point
    2 120 away every 3 s. Every demon replans from the stair, and one monk on the crypt floor is the plain-floor control.
  - `bounce_demon<n>`: the party moves between the landing and the foot every 4 s (whole-spiral replans both ways).
  - `door_demon6`: like `up_`, but StairGate0 (event 369) is toggled four times. It settles 7-14 s after each use, and
    each settle clears every route.
  - Terrors keep their current radius (rows 9237-9239: 160, 175, 190). `inside_` places them in the well.
- Headless (`--headless-run-scenario`, synchronous plans on the main thread): plan counts and costs that repeat,
  3 runs each. Desktop (`tools/run_game.sh --isolated`, minimized, the gdb wrapper `pcm/gdb_game.sh` as `--binary`):
  real worker threads, 3 runs (5 for the heaviest cases).
- Wall times are noisy. Other sessions kept the 32-thread machine at load 13-46 throughout. The harness benchmark
  (`pcm/bench.sh`, the two demon spiral plans) took 130/314 ms at load 20 and 210/536 ms at load 46. The tables give
  medians over runs. No FPS was measured.
- Baselines: MM8 `d05.blv` (Lizardman Warriors 60 × 160, an 824-high stair route from the A3 chases), headless only,
  because isolated MM8 desktop starts on d05 ran no actor AI (`[GameplayUpdatePerf] actor_ai_frames=0`, also without
  gdb; not investigated). MM7 `7d26.blv` (Zombies 64 × 166, the A3 spider route, 416 high), headless and desktop.

### Cost per plan

Headless, long plans only (more than 200 nodes), medians of 3 runs:

| Case | Long plans per run | ms (median, max) | Nodes (median, max) | Status of long plans (3 runs) |
| --- | --- | --- | --- | --- |
| demon up (`up_demon1`) | 1 | 105, 111 | 1 030 | success 3 |
| demon down (`down_demon3`) | 7 | 241, 318 | 1 627, 1 682 | success 21 |
| 10 demons up (`up_demon10`, crowding replans) | 23 | 105, 450 | 1 013, 4 369 | success 66, partial 3 |
| 10 demons, party kiting (`kite_demon10`) | 44 | 242, 382 | 1 622, 3 676 | success 132 |
| monk up / down (`up_monk3`, `down_monk3`) | 4 / 5 | 94 / 225 | 1 015 / 1 812 | success |
| Terror 160 / 175 / 190 up, from the crypt floor | 28 / 24 / 24 | 33-39, max 60 | 700-844 | partial, some no_route (the 246 doorway) |
| Terror 160 / 175 / 190 down, from the landing | 9 / 9 / 12 | 327-340, max 440 | 1 336-1 713 | no_route and partial |
| Terror 160 / 175 / 190 placed in the well | 1 | 333-349 | 1 357-1 704 | partial (one plan, then it follows it) |
| MM8 d05, 3-10 lizardmen | 3-41 | 61-64, max 72 | 1 924-1 948 | success |
| MM7 7d26, 3-10 zombies | 3-69 | 162-237, max 367 | 2 961-2 971, max 8 001 | success, a few node-limit partials |

On the desktop (worker threads, busier machine) the same plans took 1.5-2 times longer. Demons up took 154-197 ms,
and monks took 192 ms up and 481 ms down. Terrors took 508 ms down and 628-806 ms in the well; the A3 harness
measured 0.6-1.05 s for those. Plans that reached the 8 000-node limit took up to 1.2 s (MM9) and 2.6 s (MM7).

Per node, MM9 costs more: demons 153 µs (p10-p90 102-197), monks 120, Terrors 53. MM8 d05 costs 32 µs and MM7 7d26
costs 66 µs. In callgrind, 98 % of a spiral plan is `PathMap::resolveWalkStep` (the body trace of each lattice step),
and 54 % is its `candidateFacetsForBounds`. The stair is dense: 13.1 facets per 256-unit grid cell in the well against
4.3 on d05's route, because every tread is a slab with a top, an underside and sides. A finer grid does not help: in
the harness, 128 changes the cost by -3 to -10 % and 64-96 add 60-90 %. A path map rebuild after a door settles costs
7-11 ms on the main thread.

### Worker load and queueing (desktop)

Busy is the time inside `PathPlanner::plan` summed over both workers, as a percentage of one core, so 200 % means both
are full. Wait is the time from the queue to the start on a worker. Admission is the time from the party's move (the
first request with the new target) to a monster's own request. Latency is the time from the party's move to the end of
the monster's new long plan. Wasted is worker time on plans that a door clear made worthless. Values are medians over
runs; a max is the median of the per-run maxima, except for wait max and latency max, which are the largest of any
run.

| Case | Runs | Long plans per run | Long ms (median, max) | Busy | Peak plan ms in 1 s | Wait median / p90 / max (ms) | Cheap-plan wait, max (ms) | Admission max (ms) | Latency median / max (ms) | Wasted (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| up_demon1 | 3 | 1 | 154, 246 | 1.8 % | 154 | 0.4 / 1.0 / 8 | 1 | 0 | 155 / 247 | 0 |
| up_demon3 | 3 | 3 | 197, 303 | 5.2 % | 592 | 0.5 / 2.6 / 135 | 2 | 188 | 286 / 545 | 0 |
| up_demon6 | 3 | 12 | 197, 665 | 6.2 % | 1 077 | 0.6 / 2.6 / 455 | 1 | 1 646 | 1 042 / 2 235 | 0 |
| up_demon10 | 3 | 20 | 156, 1 165 | 10 % | 1 046 | 0.5 / 1.0 / 495 | 3 | 2 275 | 666 / 2 659 | 0 |
| kite_demon3 | 3 | 18 | 414, 1 062 | 14 % | 1 240 | 0.5 / 1.8 / 182 | 18 | 3 017 | 659 / 3 519 | 0 |
| kite_demon6 | 5 | 41 | 516, 1 514 | 31 % | 2 590 | 1.5 / 5.5 / 1 781 | 197 | 3 069 | 970 / 4 079 | 517 |
| kite_demon10 | 5 | 128 | 450, 872 | 134 % (52-191) | 3 074 | 14 / 1 099 / 5 516 | 2 722 | 3 859 | 1 720 / 5 480 | 1 354 |
| bounce_demon3 | 3 | 55 | 180, 701 | 26 % | 1 272 | 0.4 / 7.5 / 463 | 90 | 898 | 374 / 1 120 | 0 |
| bounce_demon6 | 3 | 109 | 191, 867 | 71 % | 2 365 | 0.6 / 87 / 1 108 | 220 | 1 473 | 644 / 2 460 | 883 |
| bounce_demon10 | 5 | 165 | 234, 1 172 | 105 % (73-125) | 2 664 | 0.7 / 499 / 4 247 | 211 | 2 861 | 1 039 / 5 380 | 1 118 |
| door_demon6 | 3 | 28 | 225, 725 | 19 % | 2 264 | 1.3 / 10 / 578 | 5 | 1 455 | 1 246 / 2 240 | 0 |
| MM7 down, 3 zombies | 3 | 22 | 177, 1 030 | 41 % | 2 578 | 4.4 / 288 / 855 | 133 | 2 819 | 1 417 / 3 842 | 0 |
| MM7 down, 6 | 3 | 35 | 147, 994 | 24 % | 2 582 | 2.3 / 417 / 1 684 | 5 | 3 022 | 1 481 / 4 039 | 0 |
| MM7 down, 10 | 3 | 57 | 281, 2 586 | 39 % | 2 364 | 35 / 408 / 2 658 | 2 | 3 447 | 1 888 / 5 543 | 0 |
| MM7 bounce, 3 | 3 | 35 | 262, 1 110 | 22 % | 2 422 | 2.2 / 297 / 759 | 171 | 2 763 | 790 / 4 136 | 0 |
| MM7 bounce, 6 | 3 | 68 | 284, 1 623 | 37 % | 2 557 | 1.2 / 304 / 2 016 | 241 | 2 231 | 1 000 / 4 654 | 0 |
| MM7 bounce, 10 | 5 | 113 | 291, 947 | 62 % (58-86) | 2 839 | 1.8 / 267 / 1 386 | 170 | 2 749 | 1 171 / 4 089 | 0 |

The heaviest cases depend on the machine load. Per run (`pcm/logs/load_queue3.txt`, `pcm/logs/summary_*`):
- kite_demon10: busy 52 % and 59 % with long plans of 277-307 ms, but 134-191 % with plans of 450-600 ms. In the
  loaded runs both workers stay full, the median wait is 0.6-0.7 s and the worst is 5.5 s. Slower plans also make more
  of them: 78-91 long plans per run against 128-163, because routes go stale while they wait (up to 9 stale-target
  discards per run).
- bounce_demon10: busy 73-125 %, wait p90 66-1 159 ms.
- MM7 bounce with 10 zombies: busy 58-86 %, wait p90 116-678 ms.

What the tables show:
1. Up to six chasers on the spiral, the workers are not the bottleneck. Busy is at most 71 % of one core (35 % of the
   pair), and the median wait is the tracer's 0.3-1.5 ms. Spiral plans alone do not queue the workers.
2. Ten demons with the party moving across levels every 3-4 s is the only load that queues, and it does so when plans
   run 1.5-2 times slower than on a quiet machine. MM7 7d26 with ten zombies loads the workers about half as much
   (62 % against 105-134 %) because its routes are replanned less often. Its plans are as slow or slower (node-limit
   partials up to 2.6 s), and its wait p90 is often higher.
3. Other monsters are delayed. The monk's plain-floor detour plans take 1-2 ms, but in `kite_demon6` they waited up to
   0.23 s for a worker, and in `kite_demon10` up to 0.59 s (median of runs; 2.7 s worst for any cheap plan). A
   monster's new route (latency) arrived after a median 0.27 s (3 demons), 0.64 s (6) and 1.39 s (10), with a worst
   of 3.2 s.
4. Most of the latency is admission, not the workers. `IndoorWorldRuntime` lets one plan request through per 0.1 s
   for the whole map (`IndoorActorPathPlanIntervalSeconds`; a consumed worker result also resets it). During a burst
   the requests are 0.10-0.15 s apart, so the n-th monster of a burst waits about n × 0.1-0.2 s before it is queued.
   With 6-10 demons the worst admission is 1.5-3.9 s, against 2.2-3.4 s in MM7. In the MM9 cases, 71-84 % (up) and
   24-70 % (kite) of all requests are trivial: plans that end at once with 0 nodes and a direct route. They are made every 0.1-0.3 s
   by demons near the party and take admission slots from the long ones. In MM7 they are 2-20 %.
5. Doors: each settled StairGate clears every route. In-flight plans are then wasted (0.5-2.1 s of worker time per
   run in the kite and bounce cases, from StairGate0's monster poll), and all demons replan within 2 s. In
   `door_demon6` the replans from mid-stair are cheaper (200-400 nodes), so the door adds load (busy 19 % against 6 %)
   but no queue.

### Recommendation

The cost is acceptable as it is. Neither the step cache nor per-stair links is needed now.
- The numbers that decide it: a spiral plan costs 0.1-0.25 s of a worker (0.5 s when loaded), close to MM7's long
  stair routes (0.15-0.3 s). With up to six chasers the workers are at most 35 % busy and their queue is empty. The
  only case that queues needs ten demons on the stair while the party runs between levels every 3-4 s, on a loaded
  machine. The Thousand Terrors has nine demons in the crypts, so that case is at the edge of what the map can
  produce.
- The step cache would hit the right cost (98 % of a plan is the step trace). But the lattice is anchored at each
  monster's own position (candidates are the current point ± 40, keys are rounded), so steps hardly repeat across
  plans or monsters. A cache would need a world-anchored lattice first. It would help MM6-MM8 maps as much as MM9
  (MM7 7d26 is as slow per plan). Consider it only if a single-session desktop run in normal play shows the pair of
  workers above 50 % busy for seconds at a time, or if fights with eight or more spiral chasers are a design target.
- Per-stair links would make spiral plans take milliseconds, but only on hand-linked stairs. They are worth it only if
  MM9 alone ends up over that threshold.
- If chase responsiveness matters, the bigger lever is engine-wide: the 0.1 s map-wide admission throttle and the
  trivial direct replans that use its slots, which make up most of the 1-4 s route latency in MM9 and MM7 alike. This
  measurement did not change them.

### Files (`pcm/`)

- `gen.py` writes `scenarios/*.yml` (headless) and `tours/*.yml` (desktop). `run_headless.sh` and `run_desktop.sh` are
  the queues. `tracer.py` and `gdb_game.sh` are the gdb tracer (field offsets from `offsets.cpp`, return sites from
  objdump of the frozen binary). `analyze.py`, `summarize.py` and `extras.py` do the statistics. `bench.sh` is the load
  gauge, `path_harness_cell.cpp` the grid-size test, and `pathfinding_sources.sha1` the planner sources measured.
- Logs: `logs/headless/` and `logs/desktop/` (`<case>_<run>.trace`, gzipped game logs). Summaries:
  `logs/summary_headless.md`, `summary_desktop.md`, `summary_desktop_heavy.md`, `extras_*.txt`. MM8 desktop runs
  without actor AI: `logs/desktop/mm8_no_actor_ai/`.
