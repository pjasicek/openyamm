# MM9 dungeon to native BLV: playbook

Status: shared converter ready

The route of the [MM9 rework](../../../devdocs/mm9_rework/PLAN.md) from an MM9 DAT dungeon to a native OpenYAMM indoor
map (BLV: sectors, portals, linear movers, lights, exit volumes), faithful to MM9's own geometry (converted, never
generated). The shared converter is the package [`dungeon/`](dungeon/), generalised from the Anskram Keep pilot
([`../mm9r_anskramkeep/README.md`](../mm9r_anskramkeep/README.md)); the Temple of Honk
([`../mm9r_templeofhonk/README.md`](../mm9r_templeofhonk/README.md)) is the first map built on it. Everything builds
into the isolated review root `output/mm9_rework/assets_dev` ([`review_root.py`](review_root.py)); `assets_dev` is
written only for the MM9 world's decoration rows and prop models (below, under a lock).

User decisions that apply to every dungeon (2026-10-29): proper BLVs; MM9's painted map on the minimap and journal map,
one image per floor picked by the party's height as in MM9, with the MM6–MM8 line map as the Map style setting's
alternative (2026-11-09, superseding the line map only: [painted maps](#painted-maps-2026-11-09)); our own baked indoor lighting from the map's lights
(MM9's lightmaps only as a reference); props as 3D decorations in the MM9 world's decoration contribution; MM9
scripted objects as native events; MM9's placements now, MM6–MM8 density later.

## The package

| Module | What it does |
| --- | --- |
| `source.py` | the project (`overrides.yml` section `map`), the frame (`native = (LT.x, LT.z, LT.y) * 2.56 - offset`), the DAT world and its texture aliases, the model rules, `floor_below` |
| `geometry.py` | v66 rings, coplanar merge, clipping, voxel grid, air flood, GLB writer |
| `rooms.py` | doorway portals (UserPortals, door leaves), air voxels, archway cuts, room labelling, portal sides, face assignment and splitting, plan images |
| `package.py` | native face rings (integer, planar or triangulated, sharpest corner first), MM9 texel UVs, the source package |
| `movers.py` | linear movers from the model rules (`dat`, `rise`, `sink`, `nudge`, `slide`), door click events |
| `lights.py` | MM9 `Light` objects as BLV point lights (at most 4 per floor point), coverage check |
| `content.py` | decoration entities from `props.json`, touch triggers as pressure pads, actors from MM9 monster rows, chest loot from `tools/mm9_import_discovery/mm9_item_sources.py` |
| `tables.py` | the map's rows in `map_stats.txt`, `map_transitions.txt` and the minimap catalog (under the review tables lock), install of BLV, scene and Lua |
| `lua.py` | the map Lua scaffolding: door table, door and chest events, metadata, registrations |
| `build.py` | the pipeline and `Hooks` (the map's population, actors, script, scene changes); `main()` with `--plan` and `--scratch DIR` |
| `scenarios.py`, `tour.py`, `sheet.py`, `audit.py`, `lighting.py`, `survey.py` | scenario helpers, review tours, sheets, the walkability audit, the bake, the DAT survey |

A map project `level_generation/projects/mm9r_<map>/` holds `overrides.yml`, `convert.py` (a `dungeon.Hooks`
subclass with the map's own events, about 200–500 lines), `make_scenarios.py`, `make_tour.py`, `props.json` (from its
props project), `README.md`. Map-specific scripted logic stays in the map project.

## Steps

```sh
cmake --build build --target mm9_compile_indoor_source -j25      # once (inside locks/cmake_build.lock, below)
python3 level_generation/projects/mm9r_common/dungeon/survey.py <MAP>.dat          # 1. classes, models, portals, scripts
python3 level_generation/projects/mm9r_common/dungeon/survey.py <MAP>.dat --rules  #    draft of overrides.yml models
python3 level_generation/projects/mm9r_<map>/convert.py --plan     # 2. rooms: work/rooms*.png (10–60 s); iterate cuts
# 3. props: level_generation/props/mm9_<map>_claude/ (Anskram props README route), tables under the decorations lock
python3 level_generation/projects/mm9r_common/review_root.py       # 4. link new models and world rows into the review root
python3 level_generation/projects/mm9r_<map>/convert.py            # 5. build, compile, install (30–60 s)
python3 level_generation/projects/mm9r_<map>/make_scenarios.py     # 6. scenarios from the built map, then run them:
for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_<map>/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_<map>   # 7. walkability
python3 level_generation/projects/mm9r_common/actor_floor_audit.py <map>   # 7b. every placed actor (and MAW copy) on a floor
python3 level_generation/projects/mm9r_<map>/make_tour.py v01 [--original]          # 8. tours (same views both maps)
./tools/run_game.sh --isolated <name> --world mm9 --map <map>.blv --assets "$PWD/output/mm9_rework/assets_dev" \
    --position X Y Z --yaw-radians A --pitch-degrees 0 --warmup 3 --seconds 150 \
    --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_<map>/review_tour_v01.yml
./tools/run_game.sh --isolated <name>orig --world mm9 --map <map>.odm --assets "$PWD/output/mm9_rework/assets_original" \
    ... --set video.view_distance=unlimited --set debug.screenshot_tour_path=.../review_tour_v01_original.yml
python3 level_generation/projects/mm9r_common/dungeon/sheet.py <project>/review/v01 <project>/review/v01_original
python3 level_generation/projects/mm9r_common/dungeon/lighting.py level_generation/projects/mm9r_<map>  # 9. bake
#    (profile tools/lighting/baked_indoors/profiles/mm9_<stem>.yml; --samples 16 draft, --recompose, --remove)
# 10. lighting tours (original | unbaked with --set video.lightmaps=false | baked), sheet of three folders; README
```

`--scratch DIR` builds and compiles into DIR (its `source/`, `runtime/`, reports) and installs nothing: use it to
compare a converter change against the installed map.

### overrides.yml

```yaml
map:
  stem: templeofhonk                 # assets_dev/worlds/mm9/maps/<stem>.material_aliases.yml, old map <stem>.odm
  display_name: Temple of Honk
  starts: [StartPoint0]              # DAT names; start 0 is the default arrival
  monster_classes: [Honk, Honk2, ElderHonk, Goose]   # DAT classes placed as actors (and air seeds)
  offset: [0, 0, 0]                  # keep the old map's frame when it fits int16: transitions and bounds stay valid
  ambient: 20                        # sector minimum light level (0 brightest, 31 black)
  model_lighting: false              # true (or {light_scale, add}): MM9's model lighting for decorations and actors
                                     # (scene model_lighting, devdocs/INDOOR_MODEL_LIGHTING.md); off by default
  split_minor_rooms: true            # default: always split a polygon at a portal plane it crosses (false: only when
                                     # its second room has 15 % of the samples; Anskram's off left black doorways)
  restore_floor_holes: true          # default: keep dropped floor pieces beside their kept coplanar neighbour (floors.py)
  weld_floor_cracks: true            # default: close same-height floor cracks up to 6 units (floors.py)
  corner_samples: true               # face votes sample each polygon over its corners only (below, "Corner samples")
models:          # every DAT world model: static | skip | {group, motion, ...} (movers.py docstring); none may be missing
model_patterns:  # name prefix -> rule
portals:         # archway cuts: {name, axis: x|z, point or points (LT), span}: a voxel slice sealing that opening
exits:           # DAT exit name -> {bottom_lt: y}: reach an exit volume down to a floor
skip_lights:     # Light names left out (documented why)
seeds:           # extra air seeds (LT points) for air no object reaches but the party can
plan_levels:     # name -> [low, high] LT y: one plan image per storey (rooms_<name>.png)
seed_exclude:    # objects of a seed class standing outside the map (relay triggers, script holders)
glass:           # tuning of MM9's translucent faces per texture: {texture: {opacity, tint, two_sided}} (or a list); which
                 # faces are glass comes from MM9's Translucent flag (rooms.Glass; see the 2026-11-07 section)
spr_surfaces:    # opt-in: MM9's .spr faces that are no liquid get their frames, the Translucent ones translucent faces
                 # at the brush Alpha ({skip: [models], translucent: false}; dungeon/spr_surfaces.py)
liquids:         # {not_water: [DAT objects]}: solids drawn with a water sprite that liquids.py must not retexture
skip_user_portals: # UserPortals not to use as door portals
textures:        # MM9 source texture -> {alias, width, height}: textures the old import gave no alias (sky markers),
                 # or pseudo textures the map's hooks use (a pool's water surface)
```

## Decisions: what each DAT object class becomes

| DAT | Native |
| --- | --- |
| `PhysicsBSP` | the static world (lightmapped in MM9). `VisBSP` is the visibility hull: only its UserPortals are read |
| `WorldObject` (carpets, trims, pillars) | static faces; non-solid ones are untouchable (`TRIGGER_nonsolid_*`) |
| `InvisibleBrush`, `LadderBlocker` | invisible collision faces (`TRIGGER_invisible_*`) |
| `RotatingDoor` double doors (`DoubleDoorL/R<n>` with a `PortalName`) | one `rotate` mover per leaf ([rotating movers](../../../devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md), MM9's swing, open-away, auto-close, reopen on contact), a click toggles the pair; doorway portal at the leaves' face. Older maps still use `rise` |
| `Door` (linear) | `dat` mover with MM9's MoveDir, MoveDist, Speed, ClosingSpeed |
| a free MM9 door (PushOpen, not Locked, named by no message or script, no map event) | a click toggles it (movers.free_door: MM9's USE), doorway or not; `click: false` opts out. A rule's `drives: [groups]` makes its click toggle those groups too (Sturmford's Portcullislever). `authored_open` on a `rotate` leaf: MM9 authors it open (StartOpen), built swung shut, starts open (Drangheim Prison's Celldoor18) |
| `RotatingDoor` levers, switches, panels | `rotate`; older maps still use `nudge` (8 LT down) or `slide` (`move_lt`) |
| `DestructableBrush` (walls, plugs, cages, boards) | scene `destructibles` (devdocs/INDOOR_DESTRUCTIBLES.md): static faces with the brush's cog, or `motion: break` for one that keeps a mover's place in the plan (not solid in the voxel pass, its `doorway` portal) with the old click as a second route (a killing blow, event 38000 + its index); the map hook `destructible_events` binds its Death/DamageTrigger handlers. Older maps still drop them as click `sink`/`slide` movers, which weapons never break |
| `RotatingDoor` traps (pivoting floors) and hatches | `rotate` with `bodies: push`, `carry: true`; `rect_portals` cut the pit off at the floor plane (a mover is not solid in the voxel pass, so its pit's air floods from the corridor); `ladders` for the way out. Anskram Keep is the worked example |
| `UserPortal` | a door portal (diagonal ones: from the leaves' plane instead) |
| archways and open halls | archway portals from voxel cuts in overrides.yml |
| `Light` | BLV point light (radius × 2.56, colour as authored); over four per floor point: a bake-only light |
| `DirLight` | a bake-only spot with the profile's `dirlights: true` (aim from `Rotation`, `FOV`, BrightScale; `dungeon/lighting.py`): the runtime has no spot lights. `StaticSunLight` only fed MM9's bake |
| `WorldProperties` `EnableFog`, a `Fog` object with `StartOn` | the scene's `fog`, automatically ([indoor fog](../../../devdocs/INDOOR_FOG.md); `map: {fog: false}` leaves it out). `Fog` objects are point controllers, not volumes; `WeatherMan`'s switching is not carried |
| `Prop`, `WallTorch`, `Brazier`, `Barrel`, `BonePile` | 3D decorations (props project); the light paired with a torch or brazier is its BLV light, the row carries none |
| `TreasureChest` | decoration whose click opens loot container k (event 41 + k); loot from the shared MM9 item sources |
| `PickupItem`, scripted `Prop` (keys, quest items) | decoration with a click event that grants the item/QBit and hides it (`evt.SetSprite`) |
| monster classes | placed actors at their DAT position on the first surface under it (`Content.actor_floor`: any solid one, invisible collision and movers included; a position in the ground stands on the top over it, one on a slope too steep to stand on moves to the nearest floor round it, `actors_moved` in `work/content.json`), facing 90 − ry, monster row `MM9 <Family> A\|B\|C` (`content.monster_bases`: the old importer's replacement table; with `npc_rows=True`, used by the regions and the Temple of Honk, a class without one takes its own MM9 row from mm9_npc_actor_rows.tsv: farm animals, fish, geese; others are listed as omitted) |
| `BlueWater` (pools) | the volume's top face as an untouchable water face (no translucency, no swimming; Temple of Honk) |
| `skymarker` faces (skylights) | drawn with an MM9 sky texture through `textures` (no sky indoors); the bake's sky light (profile `emitters`) |
| `Trigger` (touch volume) | invisible pressure-plate pad 3 over the floor under it, shrunk to one floor and one room |
| `ExitTrigger` | MM9 positioned transition volume (`map_transitions.txt` row; the indoor runtime supports them) |
| `StartPoint` | `party_start_points`, on the floor, facing 90 − ry (below); arrivals into the map take the facing of the start they resolve to |
| `ScriptObject`, `*.scr` | native Lua in the map project (read the SCR and GrayFace-style references; keys are QBits 90000 + key, items `MM9.ItemIds`) |
| `Ladder` | a scene `ladders` entry (`overrides.yml` `ladders`: which way it faces, where a climber stops, the exit at its top). Only Drangheim City's TowerLadder1 leans among MM9's 68: a leaning ladder takes its bottom and top from the rung face in the map's `convert.py` and is climbed along that line; `grab_at_top` where the ladder is the only way down ([leaning ladders](../../../devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md)) |
| `PerceptionBrush` | a red trap hint (Perception.spr, brush `Alpha`), shown to a party with its `PerceptionValue`: an untouchable translucent face with a cog, which the map script shows or hides (Anskram Keep `place_perception_hints`, `script_hints`). Read these before calling a red floor a carpet |
| `AIBarrier` | monster-only walls by rule (no `overrides.yml` entry): invisible, untouchable `TRIGGER_barrier_*` faces listed in the scene's `actor_barriers`; `map: {actor_barriers: false}` skips them (below, "Monster barriers") |
| `AITrk`, `AIRail`, `Marker`, sky objects, `AmbientSound` | not built (AI helpers, sky); the rails are the answer key of `rail_check.py` (below); ambient sound is a later pass |

## Deviations the engine forces

- Rotating movers and ladders exist since 2026-10-30. Anskram Keep, the Temple of Honk and the Lich Lab use them;
  `rise` and `nudge` remain only for a map that keeps them. A leaf's node is its model's name, so a Lua `DOORS.<name>`
  names a leaf (drive a pair by both leaves, or by group ids); `one_node: true` keeps the group's name for a model
  whose name is not a Lua identifier (`peasant door`).
- MM9 touch volumes fire on any part of the party in their box; native pads fire when the party stands on them.
- Decorations do not move: props on moving parts (spikes under a crusher) are dropped or scripted.
- Sky faces in a dungeon (`skymarker` texture): no sky indoors; see the map README for what replaced them.
- MM9 AI scripting (patrol paths, ceremonies, goose chases) has no native equivalent: actors stand at their DAT
  positions; hostility and grouping are kept with groups, hostility bits and the monster damage/killed hooks.

## Quality gates (each map's README reports them with numbers)

1. **Every DAT world model has a rule** (the build stops otherwise) and every skipped class is listed with a reason.
2. **Sealed air**: `stats.leaked_to_border` false; every air component that the party can reach is seeded; the
   dropped faces (`work/dropped_faces.json`) are faces between brushes, facing out, or in sealed unbuilt pits.
3. **Every portal joins two rooms**: `stats.portals_without_two_rooms` 0; no portal in `build_report.json` skipped.
   **No hole in the portal graph**: `stats.uncovered_barrier_voxels` 0 (`work/uncovered_barriers.json` lists any:
   barrier voxels between two rooms that no portal face covers, `rooms.uncovered_barriers`). After a map is installed,
   the portal sweep (`tools/indoor_portal_sweep.py`, below) finds no clipping from a standing pose.
4. **No holes**: look at every review view; faces mixed over rooms (`mixed_faces.json`) are explained; the floor
   check (`build_report.json` `floor_check`) leaves only door sills (Temple of Honk 628 LT², Anskram 18 LT²); the
   floor-hole check (`work/floor_holes.json`, the build's `WARNING: ... floor holes` / `floor cracks` lines) is
   explained hole by hole (restore it in an `edit_polygons` hook, or say why it is no hole).
5. **Review sheet**: MM9 original | native BLV at 20 or more eye-level views covering every room type (halls,
   corridors, stairs, doors, the scripted objects, chests); lighting compare original | unbaked | baked.
6. **Walkability**: every step and flight in `work/walkability.json` explained (MM9 stairs above the party's 50-unit
   step, frame lips), unreachable regions under 0.1 M units², actor notes explained.
7. **Scenarios pass**: doors and exits (a closed door stops the party, opens on its event, the party walks through,
   every exit raises its transition), every chest opens, every scripted object does what MM9 does.
8. **Starts**: each start on a floor, facing into the map (check the first view of the tour), arrivals from the
   neighbouring maps on the floor.
9. **Compiler unit tests** pass (`openyamm_indoor_source_tests`).
10. **Lights**: no floor point under more than 4 lights (`content.json` `light_coverage`); bake current (not stale).

## Reference runs: always lift the view limit

The "MM9 original" column is our outdoor renderer drawing the old import, not MM9. Those scenes can carry
`view_distance_scale: 0.4`: the view ends at 6477 native (2530 LT) and geometry fades into our Enhanced sky from 3562
on, which reads as a bright white mist in any long view (the Lich Lab's cross hall measured 100 with it, 34 without, and
was calibrated against it for a day). **Every original-map tour runs with `--set video.view_distance=unlimited`.** Do not
calibrate against an original shot taken without it. MM9's own `FarZ` is 100000 unless `WorldProperties` says otherwise.

## Gotchas (Anskram Keep, Temple of Honk)

- **The v66 double ring.** Each poly stores its ring twice: the plain ring, then the same ring with its T-junction
  vertices. The reader sums the counts; `geometry.poly_ring` keeps the second (watertight) ring. The old transcoders
  concatenate both, which is where their "degenerate triangles" come from.
- **CRLF table line endings.** `map_stats.txt` mixes CRLF and LF rows: read and write tables with `newline=""`
  (`tables.read_lines`) so each line keeps its own ending; merge by row id into the review root's current copy.
- **Saving in the original.** The old scenes forbid saving (`allow_save_game: false`), which the isolated launcher
  needs: `tables.install_original_comparison` puts a copy that allows it into `output/mm9_rework/assets_original`.
- **Exits under unclimbable stairs.** MM9 stairs with 24 LT risers (61 native) are above the party's 50-unit step:
  reach the exit volume down to the floor at the foot of the stair (`exits: {name: {bottom_lt: y}}`).
- **Flat doorway leaves get a horizontal portal.** `rooms.leaf_rectangle` takes a leaf set less than half as tall as
  it is thick across (a ceiling slab, a hatch) as a horizontal doorway, normal up; before, it got a vertical rectangle
  through its middle and was skipped ("portals without two rooms"). Verhoffin Ruins' `BreakOut0/1` (2026-11-10) are the
  only such leaves today.
- **Door portals on the leaves' far side.** The engine collides the party with door faces of the next room only once
  its sphere reaches the portal; a portal through the middle of thick leaves lets the party walk half way into a
  shut door. `rooms.door_portals` moves each doorway portal to the leaves' face on its normal's negative side.
- **Stale bake after a rebuild.** The bake belongs to the BLV it was made from; the game ignores a stale one. Every
  `convert.py` that changes the map needs the bake (`dungeon/lighting.py`) again. `tables.install_map` keeps the indoor
  `.lighting` (OYILIT1) while removing the old map's ODM `.lighting` of the same name.
- **Review root refresh.** After `review_root.py` (refresh), rerun `convert.py`: it removes the old map's sidecars
  from the mirror again (they are recorded as owned).
- **Stale-bake audit on the review root.** `tools/lighting/stale_bakes.py --assets output/mm9_rework/assets_dev`
  rewrites `STALE_LIGHTING_BAKES.txt` in place, which is a hard link to `assets_dev`'s note: run it with `--check`
  (or rerun it on `assets_dev` afterwards to restore that note).
- **Hard-linked assets_dev.** `assets_dev` files share inodes with the review mirror: never write in place; temporary
  file, then `os.replace`.
- **Entity names.** A decoration entity named like a decoration resolves as that decoration: the build refuses it.
- **Floor queries on several storeys.** `floor_below` returns the highest floor under the point below the query
  height: give tours and pads a query height on the right storey (`tour.write` view element 5).
- **Headless picking** follows door motion only while frames render: a chest behind a moved panel is opened by its
  event in scenarios, not by interact.
- **Authored-open doors.** MM9 sometimes authors leaves apart and its "open" shuts them: `authored_open: true` builds
  them shut (the pose that must collide from both rooms) and starts them open.
- **Light budget.** BLV point lights: at most 4 per floor point; MM9's large fill lights are the ones dropped.
- **Facing is 90 − ry.** LithTech objects face +z rotated by ry about y: native yaw = 90 − ry (`source.facing_degrees`).
  The old importer's −ry (`yaw_degrees`) is right for prop models (their bake and placements use it) but a quarter
  turn off for starts, actors and arrivals (a south-facing start looked at the west wall).
- **Floors under another room's air.** A long floor strip running from a hall under a wall into a vault stays whole
  in the hall when the vault holds few of its samples; the engine finds a party's sector by the floor under it, so
  the vault then renders black from inside. `split_minor_rooms: true` splits every polygon at a portal plane it
  crosses; the floor check (`build_report.json` `floor_check`, stats `floor_area_under_other_rooms_lt2`) lists floor
  area under another room's air: keep it to door sills (Temple of Honk: 628 LT²). Since 2026-11-06 it samples a voxel
  and a half up (at 8 LT it read the floor's own solid voxel and missed nearly everything), and `rooms.doorway_floors`
  gives every floor piece in a doorway (the opening's width, 6 voxels each way) the room of its side of the portal:
  Anskram's doorway floors and Drangheim City's house sills (a strip along the front wall that never crosses the
  plane) put a party standing on them in the room behind the portal, and the view drew black.
  Two rooms with **no portal between them** are not split by `split_minor_rooms`: a hall's floor running on under a
  room's walls into it stays whole in the hall, and a party in that room is put in the hall (Verhoffin Ruins' water
  trap room, 52 966 LT² in `floor_check` "18->23", the view black, 2026-11-07). Cut that floor at the walls standing
  on it with the shared `dungeon/wall_splits.split_at_walls(polygons, kinds=("floor",), select=...)` in the map's
  `edit_polygons`, selecting only the floors that need it: cutting every big floor added 14-25 % faces to the hall,
  the sector whose face count drives the monsters' line-of-sight cost (devdocs/mm9_rework/BLV_GEOMETRY_COSTS.md).
  The cities still carry their own copies of `split_at_walls`.
- **Props in MM9's pose.** LithTech draws a prop in its first animation at its first key; the `*NS` furniture
  (DresserNS, BookCase02NS, Desk01NS, Cabinet0xNS, the pews, Table01NS, WeaponRackNS, Stovens...) is its twin's file
  whose pose turns it a quarter. `dungeon/prop_pose.py` turns every prop whose pose is a rigid quarter turn and whose
  GLB is the unposed bind mesh (yaw -ry - 90); props.json yaws for those are replaced.
- **Sinking plugs go under the floor.** A `sink` plug drops until its top is under the floor in front of it: a plug
  set in a wall over the floor (Anskram's cage window) that sank only its height ended in the wall below, coplanar
  with its faces (z-fighting).
- **Node prefixes.** The compiler reads only `ROOM_`, `PORTAL_`, `TRIGGER_`, `MECH_`, `DECOR_` and `LIGHT_` nodes;
  any other node (a `WATER_` face) is silently dropped. Extra faces go in `TRIGGER_<kind>_<name>` with surface flags.
- **Map timers run from load.** `RegisterMapTimerEvent` timers repeat from the map's load: every timer handler
  checks a map variable before acting (`evt.StartTimer(id, seconds)` re-arms it with its own delay).
- **Hook handlers get their context.** `RegisterMonsterDamageHook(id, title, function(context) ... context.monsterId
  ... end)`; there is no global `GetHookContext`.
- **1× MM9 textures under the desktop x4 tier.** Until 2026-10-30 01:29 the game sized every BLV texture as its
  pixels ÷ the profile's surface tier (x4 on desktop), so MM9's 1× bitmaps drew 4× too dense on every face; the build
  of 01:29 sizes a texture by the tier of the folder it was loaded from. Any review image taken with an older binary
  shows 4× tiling: compare the binary's time with the capture before judging texture scale.
- **Mover face texels.** The indoor renderer recomputes door/mover face UVs from geometry at one texel per unit, as
  MM6–MM8 do, except for a face whose vertices all move with its door and whose stored texels differ from that
  projection by more than 2 texels: it keeps its stored texels (`indoorMoverFaceKeepsStoredTexels`, 2026-10-30), so
  MM9 door leaves draw at MM9's own mapping (one double-door picture across both leaves). Stretching frame faces
  still use the geometry rule.
- **Mover faces in the bake (2026-10-30).** A face one door moves rigidly a short way (every MM9 door leaf, panel,
  lever, plug; travel at most 1024) is baked in the BLV's stored pose and the game moves its lightmap with it
  (`IndoorBakedLighting::faceLightmap`, devdocs/INDOOR_BAKED_LIGHTING.md); before, mover faces were vertex-lit and drew
  about twice as bright as the baked walls. A door keeps its stored-pose light wherever it slides (accepted); a mover
  travelling farther (a lift crossing rooms) or a face that stretches stays vertex-lit. Every bake after 2026-10-30
  includes them: rebake older sidecars to get it (they render as before).
- **Ceiling (2026-10-30).** MM9's lightmaps clip at ×1: a profile's `max_lighting: 1` stops overlapping torches from
  setting the whole map's scales (devdocs/INDOOR_BAKED_LIGHTING.md).
- **Dark props under the bake: model lighting (2026-10-30).** Under a bake, decorations take the room's actor ambient
  minus the frame ambient and read far darker than the walls (Ruined Temple banners 0.35 of the wall, Klusos chairs
  0.37, Inventa Storca's black tables; `map.ambient: 31` only removes the subtraction). MM9 lit its models with the
  world `AmbientLight`, ModelAdd 30 and every light at full colour (no BrightScale, no shadows), which is why its props
  are as bright as the walls or brighter. `map: {model_lighting: true}` in overrides.yml writes the scene's
  `model_lighting` block (ambient from the DAT's WorldInfo `AmbientLight`) and the engine then lights decorations and
  actors that way ([indoor model lighting](../../../devdocs/INDOOR_MODEL_LIGHTING.md)); scene only, no rebake. It
  takes the BLV light colours as MM9's: a map whose `convert.py` writes colour × BrightScale into the BLV (Ruined
  Temple, Training Hall, Tasar Academy, Bathhouse, Beethoven) also sets `light_scale` (about 1 / its typical
  BrightScale), e.g. `model_lighting: {light_scale: 1.4}`. **Not a default yet:** in Klusos House (2026-10-31) it drew
  the props darker than the calibrated old path and than MM9, because MM9's models also took the fill lights the
  converter caps out of the BLV (bake-only extra lights), which ours never see; compare a map's real-shot views
  before keeping it.
- **Sky and fill light in the bake (2026-10-30).** MM9 lights some halls through skylights and windows (the Temple of
  Honk) and with large fill lights; the Lich Lab's bright "sky-lit halls" were the reference's view fade, so check a
  map's reference first (Reference runs). The native map has no sky, and the converter leaves the fill lights out of the BLV once a floor
  point is under four lights. `dungeon/lighting.py` passes those capped lights (`work/lights.json`, reason "a floor
  point already under four lights") to the bake as bake-only lights (`--extra-lights`), and the map's profile lists
  its sky faces (the `skymarker` alias, drawn with MM9's Clouds1 sky `CLOUVKSJD0`) and outward window panes as
  `emitters` (area lights; a pane counts only where its back looks out of the map or at the sky). Give a new map's
  skymarker faces a sky texture of their own (`textures` in overrides.yml), not a texture the walls use, so the
  profile can name them. Calibrate per view as well as on the mean: MM9's dungeons are dark rooms around bright halls,
  and a high `ambient_scale` that matches the mean flattens them.
- **Items come to the hand.** `GiveItem` puts the item in the hand (the held item goes to the inventory); headless
  `execute_event` does not hand items over at all, only interact does: scenarios that check a granted item click
  the object from in front of it (`scenarios.look_at` + `press_interact`) and assert `held_item`.

- **Tour floor queries.** `tour.write` takes a view's floor under a query height (view element 5): on maps with
  storeys, give every view the height of its own storey, or the eye lands on the floor above.
- **Interact in scenarios.** Small objects (a key lying flat, 1.3 high) need a close, steep look
  (`scenarios.look_at(..., distances=(80, 100), height=1)`); an actor standing behind the object takes a missed ray
  (`avoid=` actor positions keeps them off the line of sight and 300 beyond); an object on an altar stands above the
  floor in front of it (`max_drop`).
- **Bake calibration.** Measure the mean brightness of the tour views (centre crop) for MM9 original, unbaked and
  baked, and tune with `--recompose` (seconds) before rebaking. MM9 dungeons lit by large fill lights that fall over
  the four-per-point cap come out dark where those lights were and bright where torches and braziers cluster: raise
  the sector ambient (`map.ambient`, rebuild and rebake) and lower `direct_scale` (Temple of Honk: ambient 14,
  direct 0.65, ambient scale 1.3 → mean 127 against MM9's 125).

## Shared fixes from Thjorgard City's play-test (2026-11-01 evening)

The user's play-test of Thjorgard City found faults that every MM9 map shares. Fixed in the shared converter and props
rules and rebuilt in **Thjorgard City only** so far; every other map gets them at its next rebuild (rollout pending the
user's play-test). Check a rebuilt map against these (counts in its `build_report.json`):

- **Doorway faces on the wrong side** (`rooms.portal_side_faces`, `faces_moved_to_their_portal_side`): a doorway one
  wall thick is one barrier voxel, so the threshold, reveals and lintel pieces cut at the portal plane took the room
  of the nearest air voxel, often the far one; the engine then put a party standing past the portal in that room and
  drew the wrong room (Thjorgard: 224 faces; 29 of 31 maps have such floors).
- **Floors under ramps** (`floors.cut_floors_under_ramps`): a flat floor running on under a ramp that rises out of it
  is cut where the ramp is lower than the party, so the party climbs the ramp instead of walking under it (the throne
  room's carpet ramp; Thjorgard 82 floors).
- **Openings onto two rooms** (`rooms.split_straddling_portals`): a window or door whose outside straddles a street
  cut is split at the cut's plane, one portal per room (Thjorgard 4; sky showed through part of the window).
- **T-junction cracks** (`package.repair_t_junctions`, `t_junction_vertices_inserted`, `t_junction_faces_split`): a
  vertex lying on another face's edge (a coplanar neighbour, or a wall standing on a floor's edge) and in that face's
  plane within a unit is inserted into the edge (rings restart at their sharpest corner: the compiler reads a face's
  type from its first three vertices; without that, doors and shops scenarios failed). Where the inserted vertex rounds
  off the face's plane, the face becomes triangles over its new ring (`triangles_over_ring`: a fan from an untouched
  corner, else from its middle). Thjorgard 19 068 vertices, 611 faces split; the dotted sky-coloured lines are gone.
- **Carpets over floors** (`floors.cut_floors_under_overlays`, `floors_cut_under_overlays`, `overlay_skirt_faces`): a
  rug or carpet a few units over a floor left two walkable faces stacked, and the party's support alternated between
  them (the head bobbing up the throne room's carpeted ramp). The floor under the overlay is cut away and a skirt runs
  from each overlay edge down to the floor's plane (the rug's thickness; without it the view slipped through the slit).
  Thjorgard 80 floors, 539 skirt faces.
- ~~**Window boxes as glass**~~ (withdrawn 2026-11-07: MM9's opaque window boxes stay opaque; see "Package changes from
  Bootcamp's play-test").
- **Decoration heights** (`content.entity`): positions round up to whole units, so a base just under its floor no
  longer puts the decoration in the room below (where it was hidden whenever that room was not drawn).
- **Props** (`level_generation/props/mm9_thjorgardcity_claude/scripts/placements.py`, to copy to every map's props
  project): a model whose first animation pose is a rigid turn (the `*NS` props: a quarter turn) is placed turned,
  checked against MM9's posed mesh (`pose_turn_degrees`; Thjorgard 86); a prop whose base is under the floor under its
  DAT position is lifted onto it (`floor_lift`; MM9's MoveToFloor 0 props have their base at Pos, the ABC origin is
  mid-height: beds, cabinets and dressers were sunk half their height; Thjorgard 183); a city CandleProp without Blue
  takes `chandelier3orange` (the Ruined Temple's chandelier3 burns blue).
- **Hung shields and wall notices** (props, 2026-11-02): MM9 hangs a Shield.ABC pitched pi/2 on the wall (its centre
  half a shield's thickness off it). Sturmford's `shield1flat`/`shield2flat` and Thronheim's `shield3flat`/
  `shield4flat` lie flat (measured against the old import's flat bake): map the pitched shields to Dook's Castle's hung
  `shield1`/`shield2`/`shield3r`/`shield4` (Thjorgard's `props_table.TILT_OF`/`TILTS`). A MoveToFloor prop within 8
  units of a wall and 24 or more over its floor (a notice pinned beside a door) stays at its DAT height
  (`placements.wall_distance`, entry field `wall_hung_raise`). Away from a wall, an upright letter (scroll-open,
  MoveToFloor, no pitch) lies flat as 1000 Terrors' `scrollp90` on what it stood on (`props_table.LAID_FLAT`): MM9
  shows it standing like a placard. 19 maps place `scroll` (Thjoradmine 8, Anskram Keep and Guberland 5 each).
- **Copy Thjorgard's `placements.py` lookups** (`WorldTriangles`, `floor_below`, `wall_distance`) at the rollout: the
  per-face Python loop took 22 minutes for Thjorgard's props, the grid 16 s with identical output.
- **Engine** (every BLV): the sector lookup keeps every floor candidate, not MM8's first five (a tall street sector
  hid the palace stairs' room; MM6-MM8 unchanged on all 161 BLVs); a card material's primitive is split into its
  connected cards, so each flame turns about its own candle.

## Door sounds (2026-11-02)

MM9's doors name their own sounds (`OpenStartSound`, `CloseStartSound`, `CloseStopSound`, the busy loops,
`JiggleSound`; 1 767 Door/RotatingDoor objects over the 36 maps: wooden open, creak and shut, stone slides, metal slams,
latches, cell doors, trapdoors). `movers.door_sounds` writes them as the scene door's `sounds` block (the old outdoor
exporter's names, `Door/door01open.wav`), and the engine plays them instead of MM6-MM8's environment loop
(`game/events/MechanismAudio.h`, shared with the outdoor model mechanisms; a door without the block sounds as before).
Since the play-test of 2026-11-06 a door that names no sound (151 RotatingDoors, 144 Doors: Drangheim City's
BlacksmithDoor0/1, levers, drawers, breakable brushes, traps) gets an empty block and moves silently, as in MM9, and so
do a mover's `_INV` and `_GLASS` parts (they played MM6-MM8's loop under the MM9 sounds); only spinners keep the
environment's. One with only a jiggle (Thjorgard's 69 locked sliding doors) moves silently too. A name in a folder MM9
misspells (`Sounds\Doors\elestart.wav`) takes the one world sound of that name (`movers.world_sound`). A door MM9 leaves
silent that should sound gets a `sounds` map on its overrides.yml model rule (the same keys, world sound names such as
`Door/doorslammetal02.wav`), which replaces the DAT object's (`movers.mover_sounds`; 1000 Terrors' CoffinGate2, the
play-test of 2026-11-10). The engine
compares each door with what it last heard, not with the step's snapshot: a click (or the reversal it asks for) sets
the mechanism before the snapshot, so until 2026-11-06 an MM9 door sounded only when its mover reversed it or closed it
by itself. Check every built scene with `door_sound_check.py` (every door has a block, a mover's first part names exactly
its DAT object's sounds, the files exist). The jiggle (a locked door's knock) is carried but not played yet. Opening on contact: 7 MM9 doors
have `TouchToOpen` (Bathhouse Door3/4, Lich Lab's peasant doors, Dungeon of Secrets' axe triggers and elevator); every
other door opens when used (`PushOpen`).

## Water volumes and swimming (2026-11-02)

**One shared rule for every map (2026-11-06, the user: MM9's volumes are the authority).** Every MM9 water volume is
the scene's water, swum where it is deep and waded where it is not; `water.swimming(project)` is on unless
overrides.yml says `map: {swim: false}` (an opt-out that must say why; none so far). With it the shared build:

- makes non-solid every up-facing polygon with a liquid texture (`water.LIQUID_TEXTURE_WORDS`: water, ocean, slime,
  lava) within 8 LT of a volume's top inside its footprint (`water.surface_polygon`): MM9's own surface brushes and
  the wading floors the maps' hooks built there (`swim_wading_surfaces_nonsolid`), where a floor lies under it in the
  volume; over an unbuilt bed (Frosgard City's open sea) it stays a solid wading floor (`swim_surfaces_kept_no_bed`);
- draws the top of a volume MM9 shows with its sprite (ShowSurface 1, `water.SURFACE_SPRITES`) whose model the map
  skips and whose top no liquid polygon covers (`water.drawn_surfaces`, `swim_drawn_surfaces`); a hook that builds a
  volume's surface itself later (a mover's faces) names it in `Hooks.own_water_surfaces`; DrainWater.scr volumes are
  their movers';
- places MM9's swimmers (`water.SWIMMER_CLASSES`) whose DAT position lies in a volume at their box-centre height
  (`water.swimmer_foot`, `Content.actor`);
- reports `water_room_mismatches` and `water_bed_holes` for every map (`Build.water_checks`, build_report.json
  `water` with each volume's tops and depth).

`dungeon/swim_check.py <project> [--isle]` writes a `scenario_swim_check.yml` from the built map (the party on each
volume's deepest bed, up to the surface; swimmers still in their water). The pilot was Verhoffin Ruins
(devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md).

- **The scene's `water_volumes`** come from the DAT (`dungeon/water.py`, written by `Build.scene_file`): every
  liquid-class object (BlueWater, DirtyWater, ClearWater, CorrosiveFluid, Kato, LiquidNitrogen; not Hidden) with a world
  model, one piece per up-facing brush polygon down to the brush's lowest point under it (a box: one piece), MM9's
  light scale as `tint`, `fog` only with FogEnable, `current` only over 1 LT/s, and `mover_door_id` for a volume whose
  model is a mover (DrainWater.scr). The top of a mover-bound volume is the BLV's stored pose of the door's faces: a map
  that builds its moving water elsewhere (Verhoffin's trap face at its full height) sets it in its scene hook.
- **Surfaces**: a liquid model a map keeps as `static` has its tops made non-solid and its invisible sides dropped
  (`Build.swim_surfaces`); surfaces a map builds itself (Verhoffin's Ocean3 quads, the pit's WaterSurface) must take the
  role `nonsolid` there. The liquid shader draws both sides; liquids.py makes a surface see-through when its room's bed
  is under it (add the family's opacity to SEE_THROUGH when the build asks).
- **Rooms and beds**: with the surface non-solid the voxel pass sees one air over and under it, so the flooded bed is
  part of the room above (the engine crosses rooms only at portals). Check in the map's hook with
  `water.room_mismatches` (pieces whose air under the top is another room than over it: must be 0) and
  `water.bed_holes` (open water with no floor inside the volume: a swimmer would sink out of the map; must be 0).
  MM9's brush rectangles run on under the ground round the water: samples in rock do not count.
- **Audit**: `dungeon/audit.py` adds the water rule: floors in a volume, or beside it at most 59 over the top (the
  surface jump), are one swim set; from it the party walks, drops and climbs 50. Pits and unreachable regions the party
  swims out of are marked `water` (walking monsters still cannot: they walk the bed, as in MM9); each volume reports
  whether the party gets out and the rims beyond the surface jump. A pit whose rim is out of reach needs a way out
  (Verhoffin's electrified pit keeps its invisible ledge).
- **outdoor_blv.py** (the isles' seas) is not switched yet; see the Isle of Ashes notes in the design's status.

## Build speed (2026-11-02)

Thjorgard City's build took about 4 minutes, mostly in per-polygon Python. Five changes, each checked byte-identical
(the scratch outputs of Thjorgard, Lich Lab and Sturmford old against new, `diff -rq`; build.log differs only in its
output path): `Polygon.normal`/`area` keep the Newell vector keyed on the points' bytes (2.4 million reads, 140 s
profiled); `city.structure._rectangles` keeps each row's best rectangle and rescans only the rows a taken rectangle
changed (74 s); `city.hooks._FloorIndex` (the half steps' 110 000 floor lookups, 26 s); `rooms.label_rooms` dilates
each small pocket in its box and sums room centres by slices (21 s); `floors._FloorBoxes` for the crack and hole
checks; `geometry.sample_polygon` keeps its barycentric grids; `label_rooms` counts room sizes with `bincount` (7 s);
Thjorgard's `split_at_walls` builds the walls' ends and tangents once (Guberland already did). Thjorgard City: about
4 min -> 120 s (114 s CPU, peak 3.8 GB), byte-identical. What is left is real work: the voxel build samples 216 million
points (marking them in one batch or in chunks was no faster), the street portals relabel the rooms three times. For
a rollout, run the maps in parallel (one Python process each; 32 cores, about 4 GB per city).

Second pass (2026-11-07, after R6), each checked byte-identical (`--scratch` outputs of Lindisfarne, Frosgard, Bootcamp,
Sturmford City, Thronheim City, Thjorgard City, Lich Lab, Chasm against the old code; the camera gate's moves and the
transfer's pages compared apart): `water.bed_holes` tests each floor against the water lattice block under its box
(Lindisfarne: 300 000 samples x every floor, most of its 21 minutes); `rooms.crossing_portals` keeps the portal boxes
per portal list (over half of a dungeon's build); `liquids.has_bed` and `floors.cut_floors_under_ramps` /
`restore_floor_holes` filter by array boxes (4, 2 and 1.5 minutes on regions and Thronheim City); `source.FloorsBelow`
for the population report; the solid voxels are marked in 4 forked processes (`geometry.mark_polygons`); the camera
gate keeps its per-direction and per-origin ray terms; `lightmap_transfer` tests a chart's texels only inside each
face's box (the Isle of Ashes 157 s -> 20 s; its outputs differ only by the recipe's `producer_sha256`); the
compiler's BSP partition search (editor/import/IndoorDerivedGeometry.cpp `buildSectorBsp`) stops counting a candidate
once its score cannot beat the best (Frosgard City's compile 350 s -> 36 s, the same BLV on 11 maps). Convert:
Lindisfarne 21.6 min -> 1.5 min, Frosgard City 12.6 -> about 1.8, Frosgard 6.5 -> 1.2, Thronheim City 7.6 -> 1.9, Lich
Lab 2.3 -> 0.8, Bootcamp 2.3 -> 0.7. Profile a map with `python3 -m cProfile -o out.prof <project>/convert.py --scratch
DIR` (the compiler: `perf record -g`).

## Shared resources

- `assets_dev/worlds/mm9/data_tables/decoration_data.txt` (rows 2001–2999, sprites 24801+, contiguous and in order),
  the world decoration sprites and `worlds/mm9/models/indoor_decorations.yml`: append only inside
  `flock -x level_generation/projects/mm9r_common/locks/mm9_decorations.lock <command>`, re-reading the next free row
  inside the lock; write by temporary file + `os.replace`. Same lock for any other `assets_dev/worlds/mm9` table.
- Review-root shared tables (`map_transitions.txt`, `map_stats.txt`, the minimap catalog): only the map's rows, inside
  `locks/review_tables.lock` (`tables.update_tables` takes it), CRLF preserved.
- C++ builds inside `flock -x level_generation/projects/mm9r_common/locks/cmake_build.lock`; no Vulkan builds.
- Game runs may overlap with other agents' and the user's: no waiting. Launch with `./tools/run_game.sh --isolated
  <unique name>` (minimized, timed exit). Never put `--set` before `--headless-run-scenario`.

## Verification of the package (2026-10-30)

The package run on Anskram Keep into a scratch directory (a scratch hooks file reproducing Anskram's `content.py`
population with its own event tables) gives byte-identical `source/anskramkeep.glb`, `anskramkeep.geometry.yml`,
compiled `anskramkeep.blv`, `doors.yml` and `faces.yml`, the same 256 decorations, 17 pads, 47 actors, 7 chests, 112
lights, 65 movers, 49 sectors and 55 portal faces, the same scene (loot, doors, actors) except the facing fix below,
and the same `map_stats` and minimap catalog texts as installed (`split_minor_rooms` off, Anskram's setting). The loot
now comes from the shared item sources instead of the old scene: identical records. The one intended difference is
the facing (90 − ry, gotchas): Anskram's starts turn from 0° / 180° to 90° / 270° (into the keep from each entrance,
which settles its README's open question) and every actor's `initial_yaw_units` turns a quarter. The floor check finds
18 LT² of Anskram floor under another room's air. Not reproduced: Anskram's map Lua (map-specific, stays in its
project).

**Done 2026-10-30:** `mm9r_anskramkeep` is on the package. The port alone reproduced the old build byte for byte (BLV,
doors, faces, loot, 259 decorations, 20 pads, 99 movers), with the facing change above as the only scene difference
(`mm9r_anskramkeep/compare_builds.py`; the old converter and build stay in its `legacy_converter/`).

## Maps built on the package

| Map | Faces | Rooms | Portal faces | Movers | Lights | Decorations | Chests | Actors | Record |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Anskram Keep | 8 968 | 47 | 63 | 103 | 112 | 259 | 7 | 47 | [`../mm9r_anskramkeep/README.md`](../mm9r_anskramkeep/README.md) |
| Temple of Honk | 5 789 | 22 | 24 | 35 | 130 | 154 | 5 | 18 | [`../mm9r_templeofhonk/README.md`](../mm9r_templeofhonk/README.md) |
| Lich Lab | 12 459 | 65 | 145 | 94 | 417 | 185 | 8 | 147 | [`../mm9r_lichlab/README.md`](../mm9r_lichlab/README.md) |
| Beethoven | 7 255 | 37 | 40 | 34 | 112 | 111 | 11 | 84 | [`../mm9r_beethoven/README.md`](../mm9r_beethoven/README.md) |
| Chasm of the Dead | 11 971 | 62 | 65 | 93 | 89 | 314 | 16 | 171 | [`../mm9r_chasmofthedead/README.md`](../mm9r_chasmofthedead/README.md) |
| Drangheim Prison | 12 844 | 90 | 96 | 105 | 125 | 261 | 6 | 80 | [`../mm9r_drangheimprison/README.md`](../mm9r_drangheimprison/README.md) |
| Inventa Storca | 9 057 | 27 | 29 | 88 | 71 | 108 | 5 | 39 | [`../mm9r_inventastorca/README.md`](../mm9r_inventastorca/README.md) |
| Klusos House | 1 716 | 10 | 13 | 26 | 36 | 112 | 1 | 20 | [`../mm9r_klusoshouse/README.md`](../mm9r_klusoshouse/README.md) |
| Dook's Castle | 4 588 | 11 | 12 | 16 | 156 | 96 | 7 | 47 | [`../mm9r_dookscastle/README.md`](../mm9r_dookscastle/README.md) |
| Ruined Temple | 3 724 | 9 | 10 | 54 | 65 | 68 | 3 | 15 | [`../mm9r_ruinedtemple/README.md`](../mm9r_ruinedtemple/README.md) |
| Training Hall | 6 697 | 13 | 17 | 69 | 52 | 53 | 5 | 22 | [`../mm9r_traininghall/README.md`](../mm9r_traininghall/README.md) |
| Verhoffin Ruins | 5 957 | 29 | 32 | 76 | 85 | 94 | 6 | 30 | [`../mm9r_verhoffinruins/README.md`](../mm9r_verhoffinruins/README.md) |
| Lindisfarne Monastery | 13 804 | 7 | 13 | 40 | 106 | 125 | 0 | 27 | [`../mm9r_lindisfarnemonastery/README.md`](../mm9r_lindisfarnemonastery/README.md) |
| Ta'Sar Academy | 6 918 | 29 | 34 | 45 | 116 | 304 | 4 | 26 | [`../mm9r_tasaracademy/README.md`](../mm9r_tasaracademy/README.md) |
| Thousand Terrors | 17 779 | 19 | 20 | 121 | 379 | 402 | 14 | 114 | [`../mm9r_1000terrors/README.md`](../mm9r_1000terrors/README.md) |
| Yanmir's Fort | 10 667 | 27 | 31 | 79 | 86 | 158 | 11 | 73 | [`../mm9r_yanmirsfort/README.md`](../mm9r_yanmirsfort/README.md) |
| Dark Passageway | 4 424 | 29 | 22 | 44 | 76 | 113 | 7 | 44 | [`../mm9r_darkpassageway/README.md`](../mm9r_darkpassageway/README.md) |
| Thjorad Mine | 11 076 | 59 | 62 | 71 | 257 | 371 | 15 | 93 | [`../mm9r_thjoradmine/README.md`](../mm9r_thjoradmine/README.md) |
| Hall of the Gods | 2 165 | 1 | 0 | 0 | 34 | 41 | 0 | 10 | [`../mm9r_hallofthegods/README.md`](../mm9r_hallofthegods/README.md) |
| Dungeon of Secrets | 5 096 | 10 | 10 | 155 | 139 | 55 | 0 | 1 | [`../mm9r_dungeonofsecrets/README.md`](../mm9r_dungeonofsecrets/README.md) |
| The Arena | 1 421 | 4 | 4 | 6 | 16 | 22 | 0 | 5 | [`../mm9r_thearena/README.md`](../mm9r_thearena/README.md) |
| Connecting Tunnels | 4 254 | 31 | 32 | 4 | 76 | 119 | 2 | 38 | [`../mm9r_connectingtunnels/README.md`](../mm9r_connectingtunnels/README.md) |
| Dragon Stadium | 1 480 | 3 | 2 | 0 | 3 | 5 | 2 | 1 | [`../mm9r_dragonstadium/README.md`](../mm9r_dragonstadium/README.md) |

Package changes made while building the Temple of Honk (all backward compatible for Anskram's settings):
`split_minor_rooms` and the floor check, `textures` substitutes, `facing_degrees` (90 − ry) for starts, actors and
arrival rows, `seed_exclude` (Lich Lab), `scenarios.look_at` `max_drop`/`avoid`, `tour.write` per-view query
heights and pitch, `survey.py`.

## Lessons from Anskram Keep's review (2026-10-30)

- **Bars close the voxel pass.** A barred window's bars stand in one 16-LT voxel column, so the air pass sees a wall, the
  rooms get no portal and the engine draws black through the bars. Add a `rect_portals` entry in the window. To find
  them: voxelise at 6 LT with movers solid and scan axis-aligned sight lines for two rooms with no portal between them.
  A rect portal's sides are sampled 24 LT off its plane: put the plane where both samples fall in air.
- **Which light gives a dungeon its colour.** Compare MM9's lightmaps (`poly.lightmap_pixels_bgra`) with the shots before
  blaming textures: Anskram's are (101, 95, 75) on average from 408 `DirLight`s (241, 235, 154) the converter skips, while
  its BLV lights are the torches' orange. `dirlights: true` in the bake profile.
- **MM9's lightmaps clip at ×1.** A room lit by many overlapping lights saturates in MM9 (255 = the texture as is) while the
  bake reaches ×4: the bright rooms overshoot and the mean hides it. Read the views' ratios, not only the mean.
- **MM9 originals at unlimited view distance.** Capture the old map with `--set video.view_distance=unlimited`: the outdoor
  renderer fades enclosed maps at `view_distance_scale: 0.4`, which is not MM9.
- **Crosses and other mechanisms have a way through.** Read a mover's geometry and its speeds together before calling
  something unreachable: Anskram's niches are reached by riding the V of the pivot cross on its slow closing swing.
- **A floor trap belongs to the room above it.** `owner_lt` on a mover standing in a portal's plane: a party on the cross
  was found in the pit's room, and from there the portal looks away, so the whole view went black. The pit stays its extra
  room. A hatch keeps the pit as owner: the ladder needs that, and a party on it still draws from the corridor.
- **A pad is a floor.** A pressure pad over a pit or shaft holds the party up when the cover goes; surround the shaft.
- **Keys over map variables** for what the world outside the map reads: `MM9.giveKey` sets QBit 90000 + key, which also
  lets a scenario set the state (`console: qbit set`).

## Lessons from Lich Lab

Lich Lab (four storeys, 147 monsters, 92 movers, 44 glass panes) is the first large map on the package. Package
changes made for it (backward compatible: each is off unless the map's overrides ask, or only affects what was wrong):

- **`seed_exclude`** (`rooms.build_voxels`). Seeds outside the built air flood the outside (`leaked_to_border`):
  relay triggers and script holders MM9 parks outside the walls, a touch box whose centre lies under a floor, a monster
  buried under the floor, a script object inside a solid pedestal (a sealed pocket that becomes a portal-less room and
  puts the floor under it into the wrong room). Find them by labelling the air without barriers and listing the seeds
  of every component that touches the border or is small.
- **`glass`** (`rooms.Glass`, `glass_portals`, `glass_backed`, portal `ring`). MM9's translucent panes are
  translucent faces ([translucent indoor faces](../../../devdocs/INDOOR_TRANSLUCENT_FACES.md), 2026-10-30; before:
  clear portals with an invisible collision face): a pane between two rooms is a portal shaped as the pane plus the
  pane as a solid glass face (STATIC_glass<k>_<room> nodes, the compiler's `faces.yml`, the scene's
  `translucent_faces`); a pane inside one room only the glass face; a pane with air on its front only is glass when a
  built face stands behind it, else opaque; a mover's glass a part `<node>_GLASS<k>`. Opacity = the texture setting x
  the brush `Alpha` (one entry per kind); the texture's own alpha multiplies it at run time. Glass blocks sight and
  missiles (MM9 `SURF_SOLID`). The bake lets 1 - alpha of the light through each pane.
- **`LIGHTDEFS` texture lights** (`dungeon/lighting.py`): a DTX with a `LIGHTDEFS` `center x y radius r g b` section
  lights every surface that uses it in MM9. Default: one bake-only point light per built brush. A brush centre shut in
  behind metal lights nothing (the Lich Lab's pods): the profile's `texture_lights: {per_polygon: true, scale, offset_lt}`
  puts one light in front of each polygon instead, at `scale` of full strength (37 in the Lich Lab).
- **Invisible faces of movers** (`movers.build_movers`). Movers drew their Invisible.dtx collision shells with that
  texture; they are now a second mechanism `<node>_INV` with the same motion, flagged invisible, moved by the group's
  events (the Lua `DOORS` table has both; drive groups, not node names).
- **Authored-open doorway rectangles** (`rooms.leaf_points`). MM9 hangs some doors over an open gap and lowers them to
  shut: the doorway rectangle from the authored pose missed the gap (`portals without two rooms`); it now comes from the
  shut pose.
- **Compiler planes in double precision** (engine, `editor/import/IndoorDerivedGeometry.cpp`). The derived-geometry
  check used the face cache's float Newell normal: long thin triangles far from the origin (y about 7 900) sat 0.3 off
  their own plane and the compile failed ("non-planar after coordinate quantization" on a triangle). Rebuild
  `mm9_compile_indoor_source` (and the unit tests) if a map stops there.

Map lessons:

- **Archway cuts beside the beams, not through them.** A cut through a corridor's arch beam leaves the air above the
  beam outside the slice's component: the rooms stay joined round it (`portals without two rooms` with both sides the
  same room). Put cuts 64 LT off the frames; a split opening (stair posts, arches in a row) takes `points` with one
  point per opening; widen `span` when the opening is wider than 512. Loops (a stair tower joining two storeys round
  a hall) cannot be cut once: leave the tower in its hall. Diagnose a failing cut with a breadth-first path between its
  sides over the air minus all barriers: the path shows the leak in a few voxels.
- **A floor under a portal-less pocket** reads as "floor under another room's air" in the floor check: look for sealed
  pockets (above) before tuning cuts.
- **Timers.** Every one-shot timer needs an arm variable (`arm(timer, delay)` / `fired(timer)` in Lich Lab's Lua): two
  timers registered at load both tick at load + their delay, so a later strike's raise timer fired with the strike.
  `evt.StartTimer(id, delay)` sets only the next tick; a repeating handler re-arms itself each tick for its own period.
- **Items into the packs.** `evt.GivePartyMemberItem(active member, item)` puts an MM9 item in the packs (MM9's
  `giveitem`) and works headless; fall back to `MM9.giveItem` (the hand) when every pack is full.
- **The walkability audit and invisible ramps.** MM9 lays invisible collision ramps over stair feet; the audit does
  not follow them and reports the floors above as cut off. Prove such a stair with a scenario walk.
- **Headless party**: one member; `console: {line: "player add Wizard Risdar"}` adds member 1 of a given class.
- **Prop names across projects.** Two props projects built `mm9_deco_<name>` from the same ABC minutes apart and the
  second install overwrote the first: check `assets_source/engine/models/` before naming, and reuse.
- **Unscripted MM9 machinery.** Read the scripts to the end: ILSHealerRoom.scr waits for a "Fix" nothing sends (MM9's
  Lich promotion never runs); the native map has to choose what makes it work (Lich Lab: the quest key and the
  elixir) and say so in its README.

## Lessons from Beethoven

Beethoven (three storeys of sewers and catacombs, the maze hall, six ladders, swinging doors, flooded cavern). Package
change: `Hooks.edit_polygons(build, polygons)`, a map's own edits of the merged polygons before voxels and rooms (off
unless a map overrides it).

- **Water brushes are single quads over a storey.** `WaterTop1`/`WaterTop10` are one translucent quad each over the
  whole map (9 000 x 9 000 LT), split by the BSP; only the channels show, the rest lies in the rock. Merged, it is one
  huge face through every wall. Drop the brush and raise a copy of each channel bed polygon to the water's height: the
  surface stops at the channel walls and the portals split it with the beds.
- **Water volumes** (`BlueWater`, `ClearWater`) have no drawn faces: their `ShowSurface` top is a face of the map's own
  (box top, `.spr` first frame or a `liquids.yml` entry with `worlds: [mm9]`, in the review root until accepted).
- **Flooded caverns.** No swimming yet: a deep volume's surface is a static face the party wades on; check what MM9
  hangs under the surface (Beethoven's shaft walls end 46 LT under it, which walls the party in: they are shortened).
- **Solid faces that stand in for water** seal the air below them; what lies under is still there for the day diving
  lands, and hidden by the opaque surface.
- **Non-solid translucent faces** (webs) are `TRIGGER_nonsolid_*` nodes, which `faces.yml` does not report: a map's
  `scene` hook finds them in the compiled BLV by texture (`parse_blv_file`) and adds `translucent_faces` entries.
- **Ladders in holes.** MM9's ladder volumes float in a hole in the floor; the party cannot stand in front of the rungs.
  Give such a ladder a long `reach` (from the lip) and a `top` above the lip, in the map's `scene` hook: forward takes
  it, the party drifts to the rungs while it climbs a little, back descends.
- **Ladders through floor portals** work: the compiler sets sector flag `0x8` on the room above a floor portal. An
  older BLV stalls a climber about 98 LT under the portal: recompile, do not drop the portal.
- **`evt.SpawnWorldModel(path, x, y, z, scale, yaw, clip)`** spawns a model that loops a clip: a GLB with node animation
  in native units moves a scripted object along any path with no engine work (Beethoven's bottle, 390 s a loop).
  Not saved: spawn it again in the map's load handler. Keys must be strictly increasing.
- **`movement_segment` resets the pose**: it cannot continue a climb; test ladders upward, one segment from the foot.
- **Do not start a walk on a plate**: a plate fires on stepping on. Walk from outside it, and short of a solid decoration
  standing on it (`walk_onto`'s default ends at the centre).
- **Node names ignore case in the compiler**: MM9's `Treasurechest2` and `TreasureChest2` are one node to it.
- **Tour views stuck in culverts**: a party does not fit a 64 LT pipe and is pushed out (black patches at the screen's
  edge); `make_tour.py` here picks room views with line of sight and head room from the compiled BLV.
- **Light colours.** `Light` colours are MM9's: Beethoven's catacombs bake blue and its lower sewers
  green, as the DAT's own lightmaps do (41, 65, 92 near the great door); the old bmodel_world map draws them neutral,
  so compare hues against the DAT lightmaps, not against that capture.

## Lessons from Chasm of the Dead

The Chasm (a 5 800-tall canyon, 18 rotating movers, 73 linear ones, 171 monsters, one ladder) added no package change;
everything below is in its `convert.py`.

- **The outline limit is real.** The compiler stops at 7 000 outlines (`indoor outlines exceed the native 875-byte
  visibility bitset`, a save-format bitset): every edge of an up-facing face counts. The Lich Lab has 6 597, the Chasm
  needed about 8 000. Fix without engine code: move the bevels and trim to a `TRIGGER_detail_<room>` node flagged
  invisible, which the outline pass skips, and clear the bit at load with the scene's
  `initial_state.face_attribute_overrides` (`legacy_attributes`). They keep their collision and lose only minimap clutter.
- **`STATIC_` nodes ignore surface flags; `TRIGGER_` nodes are not in `faces.yml`.** Find a `TRIGGER_` node's faces in the
  compiled BLV (`parse_blv_file`) by their vertex sets.
- **The engine's projected sky** is a scene override too: `legacy_attributes` with `IndoorSky` (0x00400000) on the sky
  faces; a tiled `CLOUVKSJD0` over a 3 000 x 6 500 LT face shows its repeat, a `sky04` projection does not.
- **Canyons cut whole.** A full-height `axis` cut with a large `span` (1 100-1 700) divides an open canyon into sectors:
  no loop runs round a canyon's cross section. The floor check then lists strips 16 LT wide along each cut: harmless.
- **MM9's `Trigger`s as polled boxes.** A four-times-a-second box test in the map Lua fires on any part of the party as
  MM9's do and needs no level floor; a `MoveToFloor` trigger's box sits on the floor under it, not at its DAT height.
- **Dormant actors.** The scene's `dormant: true`, `evt.WakeActor`/`evt.WakeGroup` and "a hit wakes a resting actor" are
  MM9's `awaken` pattern: `MummyAwaken.scr` chains need no group per actor.
- **A rotating object with an object yaw.** `Rotation` on a `RotatingDoor` (only Chasm's pendulums in all of MM9) turns its
  points and its swing axis: the map's `extra_seeds` hook wraps `source.polygons` and `rotation.lt_rotation`.
- **A "cannot walk to the party start" finding needs a look at its border.** The audit's 16-unit floor cells fall into
  gaps narrower than any body: Chasm's spike stair (slots 20 wide, 82 deep across the corridor) read as 154 monsters cut
  off, while real monsters walk over them. Dump the audit's regions, find what borders the start's, and test it with a
  hostile `spawn_actor` and `report_state`, in sight and out of it, against a control (`mm9r_chasmofthedead/work/stairs/`).
  Monsters aggro only on sight: start the party in view, then move it. A voxel flood from the start with plates filled in
  (they are holes in the static air) shows what the player can reach, and says nothing about monsters.
- **Same-map `evt.MoveToMap`** is applied by the frame loop: headless `advance_runtime` never moves the party. Assert the
  request (a map variable) and check the move on the desktop.

## Lessons from Drangheim Prison

Five storeys of cells, 75 rotating movers, five ladders, three NPCs by RUDE dialogue. Package change: `map: {split_retry: true}`
(`rooms.separating_plane`, opt-in): when the widest gap's split fails the purity test it tries the next, so a floor under a
row of three cells splits.

- **Two more false "cut off" causes in the audit.** `check_walkability.Level._add_wall` keeps a wall as a plan segment with
  the face's whole z range, so a doorway notched into one merged wall polygon (a 14-gon here) counts as solid: 23 actors in
  two regions read as cut off behind their door frames. And `HEAD = 160` drops floor under a low passage. Before believing a
  region, test walls as polygons (`mm9r_drangheimprison/reach/true_regions.py`). The audit also counts doors as open: shut,
  they hold monsters.
- **A low lane or narrow gap: check the body before the geometry.** A shared monster row could carry a stand-in's size:
  rows 9081-9083 (spider stand-in, 109 x 64 at every Scale) did not fit the 253-wide lane MM9's `AIRail`s run through.
  Since 2026-10-31 every MM9 row carries MM9's own body (see "Package change: MM9's monster bodies" below), and
  `dungeon.bodies.placed_body` gives a placed actor its body at the DAT's own Scale.
- **`AIRail`s show MM9's walkable graph.** They are not built, but where one crosses an apparent wall there is a way through.
- **Monsters stop short in sight.** A monster closed to about 400 of a party in plain view in every probe: put the party well
  past the border, and let the monster see it first, then move the party (`chase` in `reach/make_probes.py`).
- **`PerceptionBrush` is not always a floor.** Here they outline secret panels and a grate: vertical, several polygons per
  brush, some facing the wall. One cog per brush, every Perception polygon a face, `two_sided: true`, the room from
  `rooms._side_room` with `rooms.owner` for a strip along a floor. `skill set Perception 12 G` in a `menu_input_tour_path`
  input tour shows them in a review; headless, `console: {line: ...}` and a map variable test them.
- **Immobile actors.** Indoor `immobile` was ignored until 2026-10-30, so NPCs drifted out of their cells' middle (Ivsar 240
  units). To trace one, report the actor after every step of the quest scenario; `scenario_immobile.yml`, generated from the
  scene, now holds the 9 that stay put for 30 s. Animals (Move Med, AI Wimp) are not `immobile`.
- **`thin_walls: true`** (`map:` in overrides.yml, opt-in; `rooms.NearestRoom.front`). A wall under a voxel thick has air one voxel
  away on both sides, and the nearest-voxel tie can go to the air behind it: the face is dropped as "no air in front", leaving a
  one-sided wall that bodies walk through from the other side. Here 76 faces, among them the cow pen's west wall, which a
  wandering cow found. To check another map, look for metal or wood partitions in `work/dropped_faces.json`.
- **Mover nodes are per leaf.** `rotate` gives one mover per model: rule keys and `DOORS.<name>` take `RightDoor0`, not the group.


## Lessons from Klusos House

A small two-storey mansion (10 rooms, 13 rotating double doors). No package change; everything is in its `convert.py`.

- **One ceiling over many small rooms.** A face is split only where a second room holds 15 % of its samples: the upper
  floor's single 320 LT ceiling over eight bedrooms and the corridors went whole to the corridor room and drew black in
  every bedroom whose door portal was out of view. `split_at_walls` (map `edit_polygons`) cuts each large ceiling at
  the partitions (48 LT or taller, not beams) whose tops meet it, and each long wall at the partitions whose ends meet
  it, cutting only the pieces a partition reaches (1 259 faces before, 1 535 after). Check a new map's bedrooms or cells
  in `faces.yml`/the BLV: a ceiling's sector should be its room's.
- **A gallery over a hall is a loop.** A two-storey hall open to the upper gallery over handrails and balusters joins
  its rooms above the walls; a door into it cannot close a portal (both sides the same room). Make that door a plain
  mover with its own click event (`mover_events`), not a doorway.
- **Window panes facing out.** A pane whose front looks at the unbuilt outside is dropped as "no air in front" and the
  window becomes a black hole: reverse its ring in `edit_polygons` (opaque, and an `outward` emitter in the bake).
- **The old bake can be wrong.** A MoveToFloor prop (the Blackheart) and a pitched one (a wall shield) were baked at the
  wrong height and lying flat; fit numbers against the bake then measure the old import, not ours. Look at the views.
  A props script that centres models on the bake must leave a model it dropped to its floor alone: the centring put the
  Blackheart back at the bake's 34 LT, upright in the fireplace's opening, until the play-test of 2026-11-06.
- **Scenario door state persists over `load_map`** of the same map: test the shut-door walk before clicking doors open,
  or wait out the auto-close.

## Lessons from Dook's Castle

A castle storey over caverns and a flooded rope-bridge cavern. No package change; everything is in its `convert.py`.

- **A flooded cavern's surface, cut to the cavern.** ClearWater0's box spans the whole cavern and more; its top as one
  quad runs through the rock and draws a rectangle on the minimap. `edit_polygons` tests a 64 LT grid at the surface's
  height (a point is in air when the first polygon above it faces down) and adds one face per run of wet tiles; sample
  each tile at nine points or the air leaks past the sloped walls into the unbuilt bed (`air_voxels` tells).
- **A wading surface needs light to read as water**: the bake leaves it as dark as the cavern. A `liquids.yml` entry
  (the water shader, a brighter colour) and a weak display emitter on its texture make it MM9's blue surface.
- **MM9's player climbs 40-48 LT rock steps; the party's step is 20 LT.** A cavern whose only ways out are such steps is
  a pit (the audit says so). Invisible ramps (`role: invisible` polygons) over the steps, proved with forward-walk
  probes from below; the audit does not follow them.
- **Per-room darkness.** MM9's caverns are lit at a third of its castle (DAT lightmaps); one map ambient makes the caves
  three times too bright once the castle matches. A map can set each room's `min_ambient_light_level` by wrapping
  `build.package.write` in `populate` (the bake's ambient floor follows it).
- **Guards that are friendly until an alarm** keep their row's `hostility_type` with the hostile and aggressor bits
  cleared: with type 0 a group made hostile by `evt.SetMonGroupBit` never engaged. In headless scenarios a hostile
  monster closes to about 400 of a party in view and holds with its targeting flag off; assert that it closed in.
- **MM9 model names with spaces** (`double door left 01`) make the Lua `DOORS` table invalid: key them with underscores.
- **A loop variable shadowing the lake's box** (`x0, x1, z0, z1`) silently shrank the surface to two faces: check
  `lake_faces` and `air_voxels` in the report after every change to `edit_polygons`.

## MM9 visual properties (2026-10-30)

Carry over every visual property MM9 defines (match or gain, lose nothing): brush `Alpha` x texture alpha as
translucent faces, `LIGHTDEFS` texture lights as coloured bake emitters, `DTX_FULLBRITE` alpha as a glow mask,
`DirLight`s as directional bake lights, map fog (scene `fog`, automatic), `.spr` animated surfaces, binary-alpha cut-outs. The inventory, counts per map and
the converter/engine status of each are in [MM9 visual properties](../../../devdocs/mm9_rework/MM9_VISUAL_PROPERTIES.md).

## Lessons from the Ruined Temple

No package change; everything is in `mm9r_ruinedtemple/convert.py`.

- **BLV lights carry no BrightScale.** `lights.py` writes MM9's colour as authored; MM9 weights each Light by its
  `BrightScale`, and a map whose fills (0.2-0.5) and torches (0.6) differ comes out grey and too bright, the fills twice as
  strong as MM9's. The temple writes colour x BrightScale in its `populate` hook (`build.package.metadata["lights"]`) and
  raises `direct_scale`. Check the hue against the DAT lightmaps (`hue_vs_lightmaps.py`) before and after: the blue torches
  (0 / 128 / 255) read cyan until their green was halved to the lightmaps' G/B 0.26.
- **A trigger under a low obstacle** (Trigger1 under the skylight frame's 56 LT lattice): the native party, a 37-unit
  cylinder, is stopped before MM9's party box would reach the box; widen that box (a polled box grows by the party radius
  anyway).
- **Destroyed floor overlays**: `DestructableBrush` slabs coplanar with the floor under them (`DBFloor*`) are skipped, not
  built: they would z-fight and leave the same floor when gone.
- **A hidden actor on a click target**: `scenarios.look_at`'s `avoid` blocks every direction when an invisible actor (the
  genie) stands on the object; leave it out of the list.

## Lessons from Ta'Sar Academy

No package change; everything is in `mm9r_tasaracademy/convert.py` and `overrides.yml`.

- **An empty pen has no air.** Air is seeded by objects; a barred pen with no animal in it stays solid, its gate's rect
  portal reports one side as room 0 and the pen next to it draws black through its bars. Add a `seeds` point in it.
- **Ladders in a hollow tower.** A ladder whose top lands next to the hole it came up through: put `top_exit_lt` well
  away from the hole (and test with a climb that ends at the top): a forward step after the top walks back into the hole.
- **A UserPortal over a trap pit** whose side samples fall in no air: `skip_user_portals` it, put a `rect_portals`
  rectangle just under the floor plane and give the trap doors `owner_lt` in the room above (Anskram Keep's route).
- **White lightmaps.** A map lit by white fills and DirLights has neutral DAT lightmaps (B/R 1.00); Verhoffin's
  bounce 6 made it warm (B/R 0.8). Bounce 1 with direct and ambient 0.9 matched every zone within 0.89-1.21 and 0.08 hue.
- **Desktop runs can fail on another session's asset edit** (`Actor model load failed ... actors.yml`): a private
  hard-linked copy of the review root without that file (`cp -al`, then remove the one link) lets the tours run.

## Lessons from the Training Hall

No converter change; one engine change (`grab_in_air`); everything else is in `mm9r_traininghall/convert.py`.

- **Ladders in the air** (engine, 2026-10-30): a scene ladder's `grab_in_air: true` lets a jumping or falling party take
  hold (MM9's climbing poles; off by default). MM9 wraps thin poles in invisible octagonal prisms: put the strips on the
  prism's faces (four per pole), not on the pole, and end each a party height under what it hangs from.
- **Invisible faces do not stand a party you can climb from**: a party on an invisible floor face did not take a ladder;
  make a wading surface a solid face (drawn translucent) where a ladder starts from it.
- **Missiles pass Invisible faces**, picking passes untouchable ones only in part: MM9's invisible hit shells (target
  rings) become ordinary faces drawn at opacity 0 with `trigger_object`; a visible perception hint in front of a board
  takes the click, so give it the board's event.
- **A face on a voxel centre plane** (a water surface at 200 LT with the grid's centres there) reads as having no air in
  front and is dropped: move it a voxel fraction.
- **Positioned exits test the party's centre**: against a wall (a painted door) the centre stays a radius short of MM9's
  box: grow the row's box into the room (map-local wrapper of `tables.transitions_text`); an exit that starts off is
  gated by an invisible slab riding the mover that turns it on.
- **Bake-only lights' strength**: the shared bake weighs a capped light by BrightScale / the median kept light while BLV
  lights carry colour x BrightScale: write the capped lights' colour x BrightScale too, or big fills come out twice as
  strong. DirLights under a solid water surface are blocked: raise them over it as bake-only point lights.

## Lessons from Lindisfarne Monastery

A monastery with an open courtyard and a hillside seen through its front door (Terrain0 inside MM9's sky box), 27 monks
with RUDE dialogues, a bell puzzle, a playable organ, seven ladders. No package change.

- **A visible hillside costs outlines.** Building Terrain0 (1 531 polygons) put the map over the 7 000-outline bitset;
  its up-facing faces go to `TRIGGER_detail_*` (invisible to the outline pass) and are drawn again at load by
  `face_attribute_overrides` (the Chasm's route, here by position: everything south of the front wall).
- **Sky faces skew the lightmap comparison.** `hue_vs_lightmaps.py` counts an emitter's own faces (shown at `display`);
  measure zones that hold sky faces with the display at a neutral level, then restore it for the install.
- **`evt.SetMapActorPosition` was a no-op indoors** until `IndoorWorldRuntime::setMapActorPosition` (2026-10-31, build
  request from this map): Drangheim Prison's gate guards, Inventa Storca's and the Training Hall's moves did nothing in
  the BLVs. Assert an actor's new place in a scenario (`actor_visible near`) after such a move.
- **`party_attack` against a friendly actor** missed 10 of 10 here; `damage_actor` (the party's melee damage path) fires
  the monster damage hook and proves a hostility switch.
- **An archway cut must stand inside the opening.** A cut through open air (outside a porch) grows to the whole sky box;
  put each point in the wall's thickness (the doorways and windows of one wall share an axis: one cut, several points).

## Lessons from Thjorad Mine

No package change; everything is in `mm9r_thjoradmine/convert.py` and `work/cuts/`.

- **Cuts for a mine of chambers on tunnels, found automatically.** `mm9r_thjoradmine/work/cuts/auto_cuts.py` labels
  chambers from the air voxels (per layer, a 2D opening of radius 7 voxels, joined in 3D) and puts one cut in each tunnel
  mouth of every chamber (tunnel components of 3 000 voxels or more, mouths merged within 16 voxels), across the
  tunnel's direction; `apply_cuts.py` writes them, plus hand cuts and minus the failures, into overrides.yml. 59 cuts,
  6 failed (loops), 6 by hand for a tunnel network: 59 rooms in two plan runs instead of a day of hand cuts.
- **Seeds in the rock.** Relay triggers high in the rock and touch boxes centred under the floor flood the space
  between the shell's surfaces and the outside (`leaked_to_border` with every seed in one 113 M voxel component):
  `seed_exclude` them (`mm9r_thjoradmine/work/leaks.py`).
- **The old map's `_authored` overlay and Lua.** `<stem>_authored.scene.yml` (an outdoor overlay) fails the BLV load and
  `events/maps/<stem>_authored.lua` is appended to the map's Lua, replacing its handlers; `tables.install_map` removes
  both from the review root since 2026-10-31 (`OLD_SIDECARS`, `OLD_EVENT_SIDECARS`; Thjorad Mine's own removal predates it).
- **Thousands of translucent faces** stop the desktop renderer (one render batch each, bgfx has 4 096 buffers): the build
  prints a WARNING over 1 500 (Training Hall's 647 draw fine). Headless runs do not show it; make small translucent
  objects (orbs, gems) decorations, as the Thousand Terrors' candle orbs are.
- **Shared transition rows**: `tables.transitions_text` keeps the other map's end of a shared row from the review root and
  rebuilds this map's own end from the original on every install (2026-10-31), so `exits` settings apply on reruns too.
- **Event ids clash with hook ids.** `RegisterMonsterDamageHook(96, ...)` replaced a click event 96 of the map's own;
  keep hook ids out of the map's event ranges.
- **`sink` on stacked blocks** leaves a block in the space of the one under it (a wall of twelve hard-rock blocks never
  opened): breakables that MM9 destroys `slide` far down out of sight.
- **An invisible only-mover object** (`handletrigger05`, all Invisible.dtx) is only `<name>_INV` in `DOORS`.
- **BrightScale with mixed light kinds.** Lanterns at 0.75 and orange lamps at 0.2-0.5: colour x BrightScale / 0.75 in
  the BLV keeps the lanterns as authored (model lighting `light_scale` 1) and fixed a zone at 1.57 x MM9 and too orange.
- **A fence MM9's player jumps** (72 LT planks; the party jumps 35 LT) shuts a room: invisible ramps with a flat top over
  the fence (the party's body must clear the fence before its front reaches it) and between the posts beside it.
- **Steering a party in a probe** at a narrow spot: a start inside a wall walks 0; check the floor grid at 16 LT first.


## Lessons from Dark Passageway

No package change; everything is in `mm9r_darkpassageway/convert.py`.

- **Worlds joined by teleporters.** MM9 `Teleporter` pairs (TeleportDestination, UseRotation) are polled boxes running
  `evt.MoveToMap` on the same map; the audit then lists every world but the start's as "unreachable": test a few in game
  against a plain-floor control and report them as segments, not cut-offs.
- **Decorations on movers.** Statues standing on moving bridges (MM9 clears DontFollowStandingOn) get one decoration per
  pose, swapped by cog when the mover moves.
- **Sideways lifts do not carry the party.** A linear mover with a horizontal component slides out from under the party
  (only vertical movement carries it): MM9's steered magic carpet became a vertical lift moved to the pit's corner under
  its ledge, with an invisible plank for the last gap.
- **Sector ambient has a floor in the bake.** The bake's sector ambient is max(0.18, (31 - level) / 31 x 0.97): levels 27-31
  all give 0.18 x `ambient_scale`. To light one room's floor more than the rest, give it a level well under 27 (12 gives
  0.6); to darken the whole map lower `ambient_scale`.
- **Bounce from bright floors.** A desert of tan sand under bounce 6 baked orange and 1.5-2x too bright against MM9's
  neutral lightmaps; bounce 1 matched (MM9's lightmaps hold no bounce).
- **MM9's player light.** `PlayerLightOn` corridors have lightmaps near 0: matched exactly they render black (screen luma
  2) and the orchestrator does not accept that. Stand in for the player light with per-room ambient floors (sector levels
  0 / 8 / 15 against 30 here, `ambient_scale` 0.22): every review view at luma 10 or more, the lit zones' lightmap match
  shown with and without the floor in the README. Cut a dark corridor off a lit room first if they share one.
- **Wading surfaces in 32 LT tiles** leave narrower gaps along sloped walls than 64 LT ones (a dropped half-wall row of the
  tube room was 26 LT wide).
- **A scene change makes `stale_bakes.py` list the bake** (the scene is a dependency) though the game keeps using it;
  rebuilding back to the baked scene clears it.

## Lessons from Yanmir's Fort

No package change; everything is in `mm9r_yanmirsfort/convert.py`, `overrides.yml` and `bake.py`.

- **A `LIGHTDEFS` texture over a whole map needs `per_polygon`.** `yanmirsolidice1.dtx` (cyan 16/128/128) lights the
  whole ice fortress in MM9; the default one light per brush put one light at the centre of PhysicsBSP's 600 polygons
  and the bake came out neutral where MM9's lightmaps are B/R 2-3. `texture_lights: {per_polygon: true, scale: 2}`.
- **A sinking mover over 1 024 units is vertex-lit** (it loses its baked light): the trap hall's floor drew near black.
  Keep a trap's travel at 399 LT and script the "fell through" outcome on the fallen floor.
- **Relay triggers outside the walls flood the air** (`seed_exclude`; `tools/leak.py` lists each seed's component).
- **Native monsters do not open doors**: a boss that MM9 lets kick doors (`BD_OnDoor`) gets a poll that opens the
  doorway pairs near him; lure a monster in a scenario by moving the party in short hops in its sight.
- **A DAT name that is a decoration's name** (`Bucket`) must be renamed in props.json (placements.py).

## Lessons from Connecting Tunnels

No converter change; one opt-in bake profile key (`ambient_colour`); everything else is in `mm9r_connectingtunnels/`.

- **A map wider than int16** (39 000 native): `map.offset` works for the geometry, actors, chests and props, but
  `tables.transitions_text` keeps the old frame for the rows' exit volumes and arrivals (no map had an offset before):
  the map's `convert.py` wraps it (`offset_transitions`) and its `make_tour.py --original` adds the offset back. Keep
  `props.json` in the old frame (the props project fits it against the old bake) and shift it in `populate`.
- **Cuts for a tunnel network**, found automatically: `mm9r_connectingtunnels/work/cuts/tunnel_cuts.py` cuts every
  1 400 LT of geodesic distance (top view of the air, from the start) where the distance band is a plain tunnel (one
  piece before and after, no junction, narrower than a chamber): 34 cuts, 2 dropped, 31 rooms in one run.
- **MM9's world ambient is coloured.** WorldInfo `AmbientLight` (here 15/25/35) is the floor of its lightmaps: warm
  lantern pools on a blue floor. A grey bake floor cannot match both level and hue; the profile's `ambient_colour`
  (normalised to luminance 1) does.
- **A breakable that drops more than 1 024 native stays vertex-lit** (devdocs/INDOOR_BAKED_LIGHTING.md, mover faces):
  a rock fall `slide` of 1 000 LT drew as a bright square in a black tunnel; dropping it just under the floor (380 LT)
  bakes it in place.
- **A shared-table race**: two agents writing transition rows that join their two maps overwrite each other's half of
  the row (the shared writer rebuilds each row from the assets_dev original); every game run then fails with "row N:
  source or destination map reference is unresolved". Wait and retry; rerunning one convert flips it the other way.


## Lessons from Thousand Terrors

The largest dungeon (28 009 source polygons, 121 movers, 114 monsters). One package change: `tables.transitions_text`
starts from the review root's current row (2026-10-31, under the converter lock; Lich Lab `--plan` identical): a row two
converted maps share (an exit of one into the other) lost the first map's end when the second rebuilt, and the game
refused the whole table ("row 3: source or destination map reference is unresolved or inconsistent").

Package change (2026-10-31, under the converter lock; `devdocs/mm9_rework/SPIRAL_STAIR_PATHING.md`, option A1):
**floor holes and cracks** (`dungeon/floors.py`, on by default, opt out per map with `map: {restore_floor_holes: false,
weld_floor_cracks: false}`). (1) An up-facing polygon the room assignment drops ("no air in front") is kept when a kept
coplanar polygon of the same model and role shares an edge with it and labelled air lies right above it with no polygon
in between; it takes that polygon's room (`rooms.assign_faces`, `floors.restore_floor_holes`). (2) Two kept horizontal
floors at one height whose facing edges are at most 6 units apart get a strip over the crack where air lies above and no
floor covers it (`floors.weld_floor_cracks`). (3) The build checks what is left: dropped up-facing faces over 20 LT² with
air above beside a kept floor of their height (48 units), and same-height cracks up to 16 units, as two WARNING lines
and `work/floor_holes.json` (with `restored`, `welded`, native rings). The air test looks along the face's normal up to
three voxels and stops at any polygon on the way (without that, a cliff ledge or water quad under a floor slab saw the
room above through the slab: Verhoffin Ruins). Why: a monster's path planner samples the floor every 2 units, so a
dropped 8° tread wedge or a 3-unit crack cut every route up the Thousand Terrors' spiral stair. **Proof:** all 24 built
dungeons scratch-built before and after (`mm9r_1000terrors/work/floor_holes/compare_before_final.txt`): 18 byte-identical
(BLV, doors, faces, scene, Lua); 6 changed, every restored face and weld a hole in the installed BLV
(`mm9r_1000terrors/work/floor_holes/hole_proof.py`): Thousand Terrors 8 tread tops + 2 cracks (the landing's 3-unit crack, a 4-5.5-unit crypt crack),
Temple of Honk 4 floor tiles (21 units over the face below), Lich Lab 3 grate pieces (80 LT², 10 units over the face
below), Verhoffin Ruins 2 crevasse ledges and 1 wading-water quad (nothing below them), Lindisfarne Monastery 38 one-LT
cracks in the upper floors (983 units over the ground), Hall of the Gods 1. Lich Lab with both settings off is
byte-identical to before (`mm9r_1000terrors/work/floor_holes/optout_check.py`). Still reported, not restored (no coplanar neighbour of
their model shares an edge with them): the Chasm's pillar plinth tops (19 pieces, 64-128 LT², a face 21 units below),
Beethoven's marble tiles at -1700 (5, 20 below), Lich Lab's pr_metal at 2560/2642 (2, 10 below), Ruined Temple's
invisible step (1): shallow pockets a body steps through, not falls; a map hook restores them if they show. Cracks of
7-16 units are reported only: Bath House 8 (gaps between its door planks), Ruined Temple 2, Training Hall 2, Inventa
Storca 1.

- **Outlines can be estimated before the compile.** `mm9r_1000terrors/outlines.py` reproduces the compiler's count exactly
  on Lindisfarne and the Chasm (the edges of drawn, non-moving faces that border a floor, normal z >= 0.45, split at every
  non-moving face's vertices, coplanar joins out at 0.01): convert.py moves the fewest smallest up-facing faces to
  `TRIGGER_detail` until the estimate is under 6 300 (binary search; 2 minutes) instead of compiling to find out.
- **Translucent BLV faces are one render batch each.** 9 828 translucent orb faces (117 MM9 WorldObjects, Alpha 0.4) made
  the desktop renderer fail at load (`rebuildAllTexturedBatches failed`) while headless runs passed: a map with many
  translucent brushes builds them as decorations with an alpha-blend material (`mm9_deco_waterorb`).
- **BLV vertex indices are signed in `util/map_export.py`.** Above 32 767 vertices they parse negative: mask them
  (`& 0xFFFF`) in any tool that looks up face vertices (scene hooks, scenario door centres).
- **Click poses by probe.** `make_scenarios.py --probe` runs each door's candidate poses as one-step scenarios and keeps the
  first whose interact picks a target (`work/click_poses.json`); doors with a monster beside them are proved by "opening".

## Lessons from The Arena

One package fix; everything else is in `mm9r_thearena/convert.py`.

- **Glass portals with more than four corners** (package fix, `build.Build.faces`): a glass portal's `ring` (the pane's
  own outline) can have any number of corners, but the portal face was given a 4-row UV array and the build stopped with
  an `IndexError` in `package.face_rings`. Now sized to the ring; a map without such a pane builds byte-identically (Lich
  Lab `--plan --scratch` before and after: identical).
- **Talking through bars.** A counter's bars (MetalBarGrey in an invisible shell, MM9 solid) as glass or a static face
  stop the indoor pick: the NPC behind them cannot be clicked, and a face event cannot open a RUDE dialogue with its
  `OnRudeExit` (the exit needs the actor as the source). Drop the shell and make the bars an untouchable cut-out
  (`edit_polygons`: role `nonsolid`; the scene hook adds the faces to `translucent_faces`); the counter keeps the party out.
- **NPC bodies for picking.** A placed NPC on a stand-in peasant row (height 106) disappears behind a 48 LT counter for
  the pick: give NPCs MM9's body (ABC extents x Scale x 2.56: PeasantMale 12 x 34 LT -> radius 31, height 174).
- **Summoned monsters in a pen do not wake** when the party is in another room unless they sense the party: hostile
  ones run out at once, but two non-hostile monsters set on each other (`SetMonsterRelation`) stand in their pens. Spawn
  them at the pen's mouth on the party's side (same sector as the watching party); there they fight.
- **Two RUDE rows with the same prompt** (430's two "We won!", one for a bet, one for a fight): a scenario's
  `select_topic` must pick the row by its slot, not by the label alone.
- **MM9's arena is not MM6-MM8's.** The shared `ArenaRuntime` is NPC topic 704, 6-20 opponents from a monster id range,
  MM8 awards and a teleport to the floor. MM9's arena is RUDE 430's keys, 1-5 opponents from its own `PICKMON.inc`
  table, pens, locked doors and bets: it is map Lua over the existing evt calls (`SummonMonstersById`, groups, the kill
  hook, `CheckMonstersKilled`), with no engine change.

## Lessons from Dragon Stadium

A boss arena open to the sky (21 breakable pillar levels, the Dragon King). No converter change; one opt-in bake profile
key (`shadowless_faces`); everything else is in `mm9r_dragonstadium/`.

- **Breakables too tall to drop out of sight** (a pillar 2 950 native high: a mover would pass the 1 024 baked-mover
  limit): build them as static faces in one `TRIGGER_` node per piece with a `cog_number` and a click `trigger` in
  `metadata["surfaces"]`, and break them with `evt.SetFacetBit(cog, Invisible/Untouchable, true)`. They keep their bake;
  the face attributes persist in the map delta.
- **A bake shadow outlives the face that cast it.** MM9's world models cast no shadow in its lightmaps; the profile's
  `shadowless_faces` (face indices, rewritten by the map's `convert.py` after each build) makes them transparent to shadow
  rays.
- **`StaticSunLight` is not a `DirLight`.** It is MM9's sun for the lightmap bake only; a point light far above an open
  sky box with a huge radius stands in for it (no inverse-square falloff in the bake). Sky faces set `IndoorSky` by scene
  override drop out of the bake's casters and emitters, so the sun enters through the opening.
- **A sky box with vertical faces streaks** under a planar sky04 mapping: draw it as the projected indoor sky
  (`face_attribute_overrides`).
- **Map timers are not clocks**: a 0.25 s self-re-arming poll ticks about every 0.27 s. Count long waits with a one-shot
  `evt.StartTimer(id, delay)` that re-arms itself, not with ticks.
- **Compare walls as walls.** A zone box mixes vertical walls with slopes, sunlit mounds and faces MM9 does not have in
  PhysicsBSP (its pillars): Dragon Stadium's "arena walls" zone read x1.10 while its vertical walls alone were x0.85.
  `mm9r_dragonstadium/work/walls_vs_lightmaps.py` splits by face normal. Before calling dark walls a bake fault,
  compute MM9's own screen value (texture mean x lightmap x1): its bowl walls render at luma 14, ours at 15-16, the old
  capture at 79-92.
- **Leaning walls** (normal z 0.14-0.27) let the party about 240 units into their foot before inner faces stop it (shared
  collision; recorded, not changed).

## Lessons from the Dungeon of Secrets

No package change; everything is in `mm9r_dungeonofsecrets/convert.py`. A trap course wired only by MM9's object
messages (123 Triggers, 150 doors, 80 Shooters, 23 DamageBrushes, one .scr).

- **MM9 object messaging as data.** One dispatcher in the map Lua (Thousand Terrors' `send(target, message)`) with the
  doors' timings (MoveDist or RotationAngles over Speed / ClosingSpeed), CloseWaitTime, Sticky, Locked, DoubleDoorName
  and Open/CloseTriggers; locks block messages too (a timer lever's lock holds its axe trap: the course's whole clock);
  triggers per `devdocs/mm9/MM9_DAT_TRIGGER_RUNTIME_GOAL.md` (StartOn, SendDelay, ActivationCount, on/off/trigger).
  `Trigger` objects all carry Dims (default 8): relays MM9 parks outside the walls are touch boxes too; `seed_exclude`
  them. A touch fires on entry (MM9 touches only while the party moves).
- **A self-re-arming poll is no clock** (Yanmir's note above): `evt.StartTimer(id, seconds(0.1))` fires about every
  0.17 s headless, and `RegisterMapTimerEvent`'s own repeat does not go under a second. The map's scheduler advances its
  clock by the poll's measured period (ticks per game minute; one game minute is two real seconds).
- **Swept touch boxes.** A running party covers 75 LT between polls: test the segment from the last poll's position
  (slab test), grown by the party's radius, or 4 LT plate triggers are skipped.
- **Scenario map variables with spaces** (`Firedknockback off`) are not found by `state_dump_named_map_var`: key DAT
  names with `[^%w]` -> `_`.
- **Sloped invisible ramps from a floor are walked under**, not up (the party keeps the floor below it): invisible
  steps (a top and a riser each, 12-16 LT) work. Dook's Castle's ramps start above their lower floor.
- **An NPC in a booth** (Chadwick behind a barred window) needs MM9's body (ABC extents x Scale): the row's height hid
  him under the counter and no click reached him.
- **Model lighting off** where capped red fills light the props (the sconces drew black with it).

## Lessons from the Hall of the Gods

An open temple in a sky box, a story map (no monsters, four gods, the end-game cinema). No package change; everything is
in `mm9r_hallofthegods/convert.py`.

- **MM9's own sky box on the sky faces.** A map's `DemoSkyWorldModel` (here `Snow`, a 256 LT double-walled cube) holds
  the six sky textures with their texel axes: give each `skymarker` face the texture of the inner cube face with the same
  normal and carry its mapping over by the per-axis scale between the boxes (`edit_polygons`), then show them at
  `display` 1.0 in the bake. A cloud sea under a blue sky instead of sky04.
- **NPC rows from monster families are hostile.** The NPC replacement table's pictures (565 KnightPlate, 568 BLich, 555
  Guard C) belong to families the relation table sets against the party, aggressor bit or not: the actor refuses talk.
  `actor["ally"] = <a peasant family's type>` (row 352: 118) lends it peaceful relations; assert `hostile_to_party: false`.
- **Model actors take no headless click.** Actors drawn by 3D models (the MM6 world's lich and knight) have no headless
  hit shape: press_interact misses every pose; `interact_actor` runs the click's activation.
- **Headless movement stops at some 8 LT risers** the desktop party climbs (the audit agrees with headless): prove a
  doubtful step on the desktop with `--set logging.collision_trace=true` and an input tour (`action_down: forward`).
- **The shared transitions writer keeps a converted row**: after the 02:45 fix it merges from the review root's row and
  changes only old-map names, so a map's own `exits: bottom_lt` is not reapplied after the first install; a map-local
  wrapper of `tables.transitions_text` writes it.
- **Cross-map `evt.MoveToMap` from a dialogue end** works on the desktop (MM9's AskPlayer question); headless, assert a
  map variable the handler sets.

## Package change: invisible brush bottoms and the Firethrough helper (2026-10-31)

Made under the converter lock by the lightmap rollout (`devdocs/mm9_rework/MM9_LIGHTMAP_TRANSFER.md`), on the x4
texture session's report.

- **Invisible brush bottoms** (`floors.invisible_bottoms`, on by default, `map: {drop_invisible_bottoms: false}` keeps
  them). The down-facing face of an invisible collision brush (role `invisible`: Invisible.dtx, LithTech "Default"
  `DEFAR33VFJ`, Firethrough) whose largest gap to the up-facing static or invisible face under it is at most the party's
  height (192 native, 75 LT) is dropped after face assignment (rooms and voxels unchanged). They are the flat
  undersides of the invisible ramp wedges over stairs: as invisible ceilings 2 units over the treads they stopped the
  party on Temple of Honk's stairs (party at (-3497, 6556, -458), face 5457 at -428; repro
  `level_generation/textures_x4/audit/mm9_shots/honk_stairs/`). No party fits under such a face, so it blocked
  nothing the brush's sides do not. Higher ones are kept as real lids (Klusos House 1568 LT, Thjorad Mine 232-856 LT,
  Lich Lab 580-600 LT, the Training Hall's shaft). Each build writes `work/invisible_bottoms.json` (centre, gap,
  texture). **Proof:** Lich Lab `--plan --scratch` before and after: `dropped_faces.json`, `mixed_faces.json`,
  `floor_holes.json` identical, the stats differ only by `invisible_bottoms_dropped: 46` and 46 fewer faces.
- **Firethrough is a helper texture** (`source.HELPER_TEXTURES`): `Misc\Firethrough.dtx` (the magenta "FIRE
  THROUGH" marker) is invisible whatever its surface flags say, as Invisible.dtx was. Seven Lindisfarne polygons carry
  it with flags 0x109 (solid, no invisible bit) and drew magenta; every other map's Firethrough has the invisible flag
  already, so only Lindisfarne changes.
- **Rollout (2026-10-31, 14:52-15:29).** All 24 dungeons were rebuilt from the current converter
  (`mm9r_common/rebuild_1031/`: `rebuild_map.sh`, `lanes.sh`, one log per map).
  - Bottoms dropped per map: Arena 54, Lich Lab 46, Beethoven 39, Temple of Honk 38, Yanmir's Fort 35, Hall of the
    Gods 30, Lindisfarne 23, Chasm 20, Ta'Sar 15, Thousand Terrors 15, Ruined Temple 9, Klusos 4, Anskram 3, Dragon
    Stadium 3, Bath House 2, Dark Passageway 2, Drangheim 1, Inventa Storca 1, Thjorad 1, Training Hall 1.
  - Four BLVs came out byte-identical: Connecting Tunnels, Dook's Castle, Dungeon of Secrets, Verhoffin Ruins.
  - Every scenario passes, with three exceptions. Training Hall and Dark Passageway each have one failed assert that
    fails identically on the old BLVs. Anskram Keep's `scenario_rotating` (TrapExitDoor1) fails because of that day's
    monster sizes: it passes with the old actor sizes.
  - Temple of Honk's repro now climbs: the party at the user's pose walks 817 / +304, against 0 before.
  - `stair_probes.py`: walks up the invisible ramps over dropped bottoms, from below and from the ramp, and walks into
    helper boxes resting on floors. They run against the pre-rebuild snapshot `output/mm9_rework/lightmap_rollout_before`
    and against the review root. One more blocked stair was found and freed: Ruined Temple at (174, 2068, -2221), 0 ->
    114 / +37. Every other walk is identical before and after, and the boxes' sides still block.
  - Lindisfarne shows 0 visible Firethrough faces (11 before), with no magenta in its five check views.
  - Baked lighting of the changed maps was removed (stale; user decision, `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`).
- **Run this after any rebuild of a map whose BLV changed:** `scenario_stair_probes.yml` and the map's own scenarios.

## Package change: MM9's monster bodies (2026-10-31)

Made under the converter lock by the monster collision session (`devdocs/mm9_rework/MM9_MONSTER_COLLISION_RE.md`).

- **The table carries MM9's bodies.** MM9 sizes a monster by its model's initial animation dims (`static_model`, else
  animation 0) x its scale x 2.56 (radius = the larger horizontal half extent, height = twice the vertical one). All
  158 rows of `worlds/mm9/data_tables/monster_descriptors.txt` now do (`tools/mm9_import_discovery/
  mm9_monster_bodies.py` writes `mm9_monster_body_overrides.tsv`, which `generate_mm9_monster_tables.py` applies after
  copying the stand-in rows; ToHitRadius 0, the actor's own radius). `content.monster_bases()` reads them, so a map
  whose hook keeps the row's body needs nothing else.
- **A DAT `Scale` other than 1.0 replaces the row's `Scale`; it does not multiply.** Use
  `dungeon.bodies.placed_body(base["monster_id"], properties)`: `{}` at Scale 1 (the row's body), else
  `{radius, height}` of the row's model at the DAT Scale. Do not multiply the row's radius by the DAT Scale (a Bone
  Thrasher row at 0.5 placed at 1.001 is a full-size body, not half of one). `half_extents_body` is MM9's rule for a
  map's own constants (an NPC without a row). Converted to it: Anskram Keep, Beethoven, Connecting Tunnels, Dark
  Passageway, Dook's Castle, Dragon Stadium, Drangheim Prison, Inventa Storca, Lich Lab, Ruined Temple (the Genie),
  Thjorad Mine, the Training Hall and Yanmir's Fort; their own `mm9_extents()` helpers are gone (they used the first
  AnimBinding, a row name lookup that picks the last of duplicate names, and `rglob`, where `PROPS/MUMMY.abc` and
  `SAVE/SKELETON.abc` shadow the monster models).
- The body follows the row's model (the one the actor is drawn with), not the DAT `Filename`: 242 placed objects name
  another model there, many impossibly (Chasm's 90 skeletons `zombie.abc`, Drangheim's dwarf guards `sheep.abc`), so
  the class most likely loads the row's model (not traced). The engine draws no per-actor scale, so an actor with its
  own DAT Scale is drawn at the row's size.
- **Proof:** Lich Lab `--plan --scratch` before and after: identical (bodies are not in the plan). Placed actors from
  each converted hook (actors stage only, nothing installed) match the rule; the consequences per map are in the RE
  document's "Applied" section.


## Package changes for the cities (2026-10-31, Sturmford City pilot)

Made under the converter lock; both off unless a map uses them (Lich Lab `--plan --scratch` before and after:
identical outputs). Cities: [CITY_PLAYBOOK.md](CITY_PLAYBOOK.md).

- **`Hooks.extra_portals(build)`** (`build.Build.geometry`): a map's extra portals after the doorways, archway cuts and
  rect portals, before the rooms are labelled; a portal may carry `cells` (its barrier voxels). The city module
  (`city/structure.py`) gives its street cuts and roof-line portals this way.
- **`map: {painted_minimap: true}`** (`package.SourcePackage`): painted map only: the compiler makes no outlines
  (`generate_outlines: false`), so the 7 000-outline save bitset does not limit the map. Since 2026-11-09 every map
  keeps its painted map entry (below); the setting now only decides the outline pass.

## Painted maps (2026-11-09)

User request: MM9's painted maps everywhere, the dungeons included, at 2× with Real-ESRGAN, switching floors as MM9
does, with an option to choose the map style, and tested that the coordinates fit.

- **Catalog** (`tables.catalog_text`): every map's entry from the old import's catalog (`original_tables/catalog.yml`:
  the DAT header's bounds, MM9's floor thresholds from cshell.dll lowered by the player's 33 LT half height), moved by
  the project's offset, its texture the 2× PNG. Width and height stay the native sizes: they set the zoom. The
  variants are MM9's floor images: `minimum_z < party foot z <= maximum_z` picks one (`resolveMapPresentationVariant`).
- **Measured bounds** (`original_tables/map_image_fit.yml`): ten maps whose painting does not match MM9's own bounds
  (Lindisfarne Monastery about 4 % narrow and 11 px off, Yanmir's Fort and Thjorad Mine about 1-3 % short, Dragon
  Stadium, Ruined Temple, Kluso's House, Temple of Honk, Training Hall, Thjorgard City, Thronheim City by 1-5 px) carry
  bounds fitted to the rebuilt walls; MM9 itself places the party with the same error there. Refit with
  `tools/mm9_import_discovery/check_mm9_map_images.py --refine original_tables/map_image_fit.yml <map>`, only for a
  map with drawn walls, and look at its overlay before keeping it.
- **Check**: `python3 -B tools/mm9_import_discovery/check_mm9_map_images.py [maps]` loads each map in the game,
  projects its floors (by floor band) and wall feet through the catalog onto the image and searches the best match:
  FAIL when the entry is wrong (calibrated by moving every entry 8 px and 3 %: all dungeons and inked cities fail),
  check when a small offset may remain (look at `output/mm9_map_image_fit/<map>_<n>.png`). The painted regions
  (Bootcamp, Guberland, Lindisfarne, Sturmford, Yorwick, Frosgard City) have too little ink to judge automatically
  and always show as check; their overlays were looked at on 2026-11-09. Run it after a conversion that moves a map
  (a new offset) or changes its floors.
- **Outlines**: dungeons keep the outline pass (no `painted_minimap`), so their BLVs, lighting bakes and saves are
  unchanged and the Map style setting can show the line map there.
- **Images**: `level_generation/minimaps/mm9_esrgan_20261109/` (54 maps, `realesr-animevideov3` direct 2×, the
  MM7/MM8 minimap recipe), installed as `worlds/mm9/ui/maps/<map>.png` in assets_dev and both review roots.

## Package change: monster barriers and the rail check (2026-11-02)

- **Monster barriers** (`source.classify_models`, `build.Build.actor_barriers`, `build.Build.scene_file`): MM9's
  AIBarrier brushes (294 in 24 maps: ledges, pits, bridges, landings) are kept out of the air, room and floor passes
  and become faces of the room nearest each, invisible and untouchable (`TRIGGER_barrier_<room>`). The compiler now
  lists trigger nodes' faces in faces.yml too (`IndoorSourceGeometryCompiler`), and the scene's
  `actor_barriers: {faces}` names them. Only the monsters' movement and their path map treat them as walls; the party,
  projectiles, sight and the automap ignore them ([monster barriers](../../../devdocs/INDOOR_OPEN_SKY.md)). No
  `AIBarrier: skip` rule is needed any more (the 19 maps' rules were removed); `map: {actor_barriers: false}` turns
  them off, and a brush with `StartOn 0` is skipped (Verhoffin Ruins' saw blade barrier, the Chasm's AIBarrier21:
  nothing switches them on here). Every barrier face takes MM9's invisible helper texture (Yanmir's Fort's "Default"
  has no alias). The compiler's outline pass no longer splits visible edges at invisible faces' corners
  (`IndoorDerivedGeometry`), so barriers cost no outlines. Found on the Isle of Ashes, where skeletons crowding the
  party on a bridge were pushed into the sea.
- **Monster drops** (`build.Build.scene_file`): every MM9 scene takes `actor_movement: {drops: follow}`; MM9's
  monsters walk off any ledge after their target and never climb (devdocs/mm9_rework/MM9_MONSTER_JUMP_RE.md).
- **Rail check** (`rail_check.py <project> [--assets ROOT]`, after convert.py): MM9's AIRail volumes linked by
  RailLink0-3 are its AI's walkable graph; each link is planned for a walking monster on the installed map's path map
  (`openyamm --headless-check-indoor-reachability`), and the links it cannot join are listed with positions in
  `work/rail_reachability.json` with a likely cause each: `door` (closed in the starting pose; monsters open no doors,
  expected), `barrier`, `climb` (over 60 up or down: stairs, ramps, the spiral stairs) or `level` (neither). The
  `climb` and `level` ones are the path map's gaps to look at. Ladder rails are left out; a rail with no floor under it
  is listed apart. It changes nothing. A rail is a thin slab lying on its floor: its point is the highest floor at most
  48 over the slab (a first version looked 256 up, took the storey above and reported Klusos House's balconies as
  stairs it could not climb); a link whose straight walk stops at a door face counts as `door` (rail centres can lie
  a body's radius short of a door). Every unreached link carries the engine's straight-walk verdict (`walk`,
  `walk_face`, `walk_step`).
  Planned as the game plans a monster's path: partial paths allowed, and one that ends a body's reach (80) from the
  target in clear line counts; both ends move off a wall or pillar closer than the body's radius. MM9 links boxes,
  not centres: a failed link (unless a closed door stops it) is tried again between 3 x 3 points over both boxes,
  stopping at the first that connects, at most 2 000 search nodes each, in 8 parallel runs. About 20 s a map.
  Results (2026-11-02, 15 maps): the rest after the closed doors is 0-5 per map (Verhoffin Ruins 11: its crevasse,
  which MM9's monsters climbed out of and swam); every case looked at so far was the check's own error (the storey
  above taken for the rail's floor, a rail centre against a wall or inside a pillar's base or a coffin), now
  corrected, or MM9 movement our monsters do not have (drops over 100, step-ups of 82-123). No path map or converter
  fault found.
- **Outlines after the t-junction repair** (`IndoorDerivedGeometry`, 2026-11-02): the repair inserts vertices into
  edges they lie within a unit of, and the outline pass made one outline per piece, so Drangheim Prison (7 543),
  Lich Lab and the Chasm of the Dead went over the 7 000-outline limit and could not be rebuilt at all. The compiler now
  merges consecutive collinear outlines between the same two faces into one line, treats faces whose normals differ by
  under about 1.8 degrees (a face cut into triangles off its plane) as one surface, and its error states the count:
  the prison compiles with 6 230 (its build before the repair had 6 710). Tests: `openyamm_indoor_source_tests`
  ("indoor outlines merge").

## Package change: corner samples for the face votes (2026-11-06)

- **The fault** (`rooms.NearestRoom.front`). A face's room is the vote of samples over its polygon, laid on the fan
  triangles from its first vertex. A merged polygon keeps the vertices its neighbours share on its edges (T-junction
  keys), and every pair of them on an edge through the first vertex makes a zero-area fan triangle that is sampled like
  a whole one: most votes then lie on the polygon's edges. Sturmford City's magic shop ceiling (16 vertices, running
  out over the walls to the street's outer faces) voted 226 street samples to 124 shop samples and went to the street
  sector whole, so the shop had no ceiling from inside (FINAL_REBUILD_WORK M11; the air was never leaking).
- **The fix, opt-in** (`map: {corner_samples: true}`, `geometry.corner_ring`): the votes sample the polygon over its
  corners only, so evenly. A face that only the plain samples see air in front of keeps them (a shelf board's top a
  voxel under the next board sees the room only from its front edge), so the even samples drop no face the plain ones
  keep. Off, the pass is unchanged.
- **Sturmford City** (the only map with it so far): the ceiling in the shop's sector; faces mixed over 20 % 570 -> 545,
  floor area under other rooms 150 668 -> 142 765 LT², dropped faces 280 -> 280; other houses' ceiling and wall pieces
  move from the street into their house too (e.g. the ceiling at (614, 7968, 7485) LT). Other maps: turn it on at
  their next rebuild and compare `faces_mixed_without_portal_minority_over_20pct`, `floor_area_under_other_rooms_lt2`
  and `faces_without_air_dropped` in `build_report.json` before and after.

## Package changes from Bootcamp's play-test (2026-11-07)

- **Faces two rooms see** (`rooms.shared_rooms`, on by default; `map: {shared_rooms: false}` turns it off). The voxels
  (16-64 LT) cannot tell which side of a wall's thickness a face looks into, so a door jamb, a window reveal, the band
  of wall between a raised floor and the slab under it or a thin tavern wall went to the room whose air was nearest,
  often the outdoor room, and the room it bounds never drew it: white strips along Bootcamp's wall bases and under its
  doors, a sky-blue slit beside a pillar, sky round every window, the tavern open to the night. Such a face now takes a
  second room, the BLV face's room behind (surface metadata `back_room`, compiled by `mm9_compile_indoor_source`;
  `TRIGGER_shared_<back>_<room>` nodes), and the engine draws it when either room is visible
  (`indoorGeometrySectorsVisible`). The second room is that of a face meeting it in a concave corner (an edge of one
  lying on the other, each in front of the other's plane) or going on in its plane, the longest contact winning, else the second room of its
  own votes at 20 % or more. Not for walkable floors (the party's room is its floor's), sky faces or cog faces, and
  never the open-air room (30 % of the faces or more: visible from nearly everywhere).
  First, a wall dropped for want of air in front that goes on in a kept wall's plane (sharing an edge, facing the same
  way) is restored in that wall's room (`rooms.restore_continuations`: the face closing the slot beside a pilaster
  in Bootcamp's west hall); stat `walls_restored_as_continuations`. Stats:
  `faces_shared_by_corner`, `faces_shared_by_votes`; Bootcamp 1 540 and 381 of 14 361.
- **Narrow ramps** (`floors.RAMP_MIN_WIDTH_LT`): a sloped top narrower across its slope than the party (74 units) is a
  beam or a stringer, not a ramp, and no longer cuts the floor under it (Sturmford City's diagonal beam left a strip of
  sky in a house floor).
- **Glass per face from MM9's data** (`rooms.Glass`, `graded_textures`; the user, 2026-11-07: windows exactly as MM9
  has them). A face is glass (translucent, a portal between rooms) only where its surface has MM9's Translucent flag
  and its texture a graded DTX alpha (20 % of texels between 8 and 247): Bootcamp's shop windows (Clouds1, whose legacy
  BMP has no alpha, at its DTX mean 0.31), arched grilles, iron windows. A window without the flag is opaque, and its
  alpha no cut-out (scene `opaque_faces`, `TRIGGER_opaque_` nodes: Bootcamp's stained glass drangheimcityglass showed its
  alpha-0 texels as holes to the sky; window, ice and cloud textures only, with `<first seven>OPQ` variants from
  `../opaque_textures.py`). A flagged face on a brush with Alpha below 1 is glass whatever its texture.
  `overrides.yml glass` only tunes flagged faces; the window boxes (`boxes`,
  `glass_box_panes`, 2026-11-01) are removed. A map's own `translucent_faces` (hooks finding webs, chains or glass by
  texture) win over the shared glass for the same face (`build.merge_face_lists`); a mover's walkable glass (Chasm's
  floor grate) stays in its main part, which the party rides. Per-map counts: `translucent_faces`, `opaque_faces` in
  build_report.json. Glass parts shift later door ids: rerun a map's `make_scenarios.py` after converting it.
- **Double doors** (`source.classify_models` prints a note for DoubleDoorName pairs in different mover groups):
  MM9 moves a door's DoubleDoorName partner with it. `outdoor_blv_draft.py` now groups linear `Door` pairs as it did
  rotating ones; Bootcamp's Door0/1 and Door2/3 and Sturmford's RotatingDoor7/8, 13/14, 15/16 share a group
  (`mm9r_bootcamp_blv/scenario_doors.yml`).

## Package change: portal clipping (2026-11-08, the MM9 portal sweep)

`tools/indoor_portal_sweep.py --world mm9 --map <map>.blv --out output/portal_sweep/<map> [--assets <root>]` stands
the camera in and 24 units either side of every portal (up to three points across it), looks through, diagonally,
along and up and down, renders the hole view (magenta where no face is drawn) and retakes every shot with undrawn
pixels with the portal culling off (`portals culling off`): what the culling-off shot draws and the ordinary one does
not is portal clipping. `output/portal_sweep/run_all.sh` runs every MM9 map; `summarise.py` and `final_table.py` make
the table (poses inside walls or floors left out). The first sweep found 156 of 1 394 portals clipping from a standing
pose, from four causes, all fixed in the package:

- **Portal faces short of their jambs** (`rooms.face_halves`, `face_grow`): a portal's barrier is its rectangle grown
  by a voxel, but its face was the rectangle, and the voxel a jamb touches is solid, so a strip of real air up to a
  voxel wide beside the opening had no face (Thjora Mine's archway: 41 units). Neither room was seen through it, and
  a floor in it took either room. Doorway, door-leaf, rectangle and archway portals now have faces grown by the voxel
  (street cuts are grown by `city/structure.py grow_cut_faces`; glass and top portals have their own rings). Opaque
  windows have no portal and are not touched.
- **City top portals over eave pockets** (`city/structure.py merged_top_portals`): the room over a roof-line cell was
  read at layer h + 2 only, so where eaves or an arcade left air only at h + 1 the cell opened nothing, and the pocket
  (the roof room's, with its ceiling) was cut off from the street: black when looking up from it. Now read at h + 2,
  else h + 1; merged top portals' sides are read one voxel off their layer (`rooms.portal_sides`). Thjorgard City:
  342 uncovered barrier voxels to 0.
- **Duplicate portal names**: MM9 names two of Thronheim City's user portals WallPortal_2; the second's rooms were
  written for both faces, and the doorway at (0, 7700) joined two sectors 5 000 units away. Portal nodes are made
  unique (`build.faces`).
- **A camera taken for the room across a doorway** (engine): the camera's sector comes from the floor under it, and
  near a doorway a floor strip, jamb or wall may be the other room's (a voxel off), so a party standing on it saw
  its own room vanish. Every converted scene now has `portal_visibility: {near_reach: 96}`: a portal of the camera's
  sector within 96 units that the view would drop opens the whole view (`IndoorPortalVisibility.cpp`; MM6-MM8 maps
  have no such key and keep MM8's 9-unit rule).
- **Floors under two rooms**, cut automatically (`build.split_floors_between_rooms`, the shared
  `wall_splits.split_at_walls`): before the faces are assigned, a floor of at least FLOOR_SPLIT_AREA whose air (a
  voxel and a half up) holds FLOOR_SPLIT_MIN_LT2 (8 000 LT²) of a room other than the one holding most of it is cut at
  the walls standing on it; only those floors. Thjorgard's region: `floor_check` 64 600 LT² to 0 (+90 faces); Boot
  Camp 49 874 to 35 061 (+13). Until the evening of 2026-11-08 only rooms with no portal between them counted. A
  player's report then showed that a portal does not help: in Drangheim City's tower the inner room's floor ran under
  the passage round it, so a party in the passage was placed in the inner room, with the passage's doorway behind it,
  and the passage and its door went missing. Stat `floors_split_between_rooms`; `map: {split_floors_between_rooms:
  false}` turns it off (Verhoffin Ruins, whose hook cuts its trap room's floor: the shared rule cut its hall's floor
  148 times for 500 LT²). Found by a follow-up of the portal sweep (BLV sector votes).
- **A flat mover belongs to the room over its top** (`movers.flat_mover_owner`, 2026-11-08): a trap door, hatch or lid
  whose top and underside face different rooms takes the room over it unless overrides.yml sets `owner_lt`. Chasm of
  the Dead's pit hatch had been the pit's: a party standing on it was placed in the pit and saw nothing of the
  corridor (a player's report). Stat `flat_movers_owned_by_room_over_top`: Anskram Keep 3, Chasm, Drangheim Prison and
  Inventa Storca 1 each.

## Package change: a door that locks itself as it opens never auto-closes (2026-11-09)

MM9 refuses to close a locked door: StartClosing returns while `Locked` is set
([MM9_DOOR_OPEN_RE.md](../../../devdocs/mm9_rework/MM9_DOOR_OPEN_RE.md) §3), so its CloseWaitTime never shuts a door
that is locked while open. Our auto-close (`auto_close_seconds`) is the engine's and does not see the map Lua's locks.
Thousand Terrors' MiddleDoor4/5 lock themselves as they open (OpenTrigger `Lock`; TrigSorcStatueOn3 unlocks and uses
them, TrigSorcStatueOff3 unlocks and shuts them again): with the auto-close the door shut 5 s after opening and locked
behind a party in the treasure room beyond, which has no other way out (a player's save, 2026-11-09).

`movers.locks_itself`: a door group whose own OpenTriggers send `Lock` to a member (or a member's DoubleDoorName, which
passes the lock on) gets no auto-close; stat `self_locking_no_auto_close`. In the MM9 DATs that is MiddleDoor4/5,
Beethoven's maze levers Lever5/6 (they now stay pulled), Chasm of the Dead's HSP1/2/7 plates (the map Lua shuts them
after 1.3 s, as before), the Dungeon of Secrets' self-locking gplates (they stay down) and Thjorad Mine's refinery
handle (an invisible part). Rebuilt and installed for those five maps: BLV and Lua unchanged, the scene differs by
the removed `auto_close_seconds` (and the empty `pickup_qbits` lists the converter now writes).

A door locked by *another* object while it is open would need the same rule at run time. The MM9 DATs have no such
case that matters: every other sender closes the door first and then locks it (Verhoffin Ruins' water trap, Wizard's
Lab's super eye, Dark Passageway's forest ambush, the Dungeon of Secrets' entrance), or the door is a trap blade.
`door_trap_audit.py` lists, for every built map, the doorway doors that shut by themselves and that the party may not
reopen with a click, and the doorway doors another object closes or locks, with the rooms they join (a room with one
portal is a dead end) and every sender. Its first run (2026-11-09, 38 and 35 entries, each read against the map's Lua)
found no other room the party can be shut into: the rest are doors kept locked for good, keys that stay unlocked once
used, buttons or levers on both sides, a script's own timers, or MM9's designed trap rooms with their way out. Run it
after a rebuild that touches doors or their wiring.
