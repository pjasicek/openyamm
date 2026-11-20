# MM9 rework: Dungeon of Secrets (`dungeonofsecrets.blv`)

MM9's Dungeon of Secrets (off Frosgard: Chadwick Boorsley's Ranger trial, a trap course with no monsters and no chests)
converted from its DAT world into a native indoor map (BLV: sectors, portals, linear and rotating movers, lights, an
exit volume) on the shared dungeon converter ([`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md)).
Built into the isolated review root `output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's
decoration rows and the one new prop model ([props project](../../props/mm9_dungeonofsecrets_claude/README.md)).
Status 2026-10-31 (overnight run): geometry, 10 rooms, every mover, the whole course's MM9 object wiring as native Lua,
Chadwick and his RUDE dialogue, the flooded pool room's water, 55 decorations, baked lighting matched to MM9's DAT
lightmaps. No engine change, no shared converter change.

The course: the party arrives from Frosgard at the east end of the hub, where Chadwick Boorsley sits in a ticket booth
(talk to him through the bars: RUDE 417 starts the trial). The entrance button opens the gate to the first lever.
"The Dungeon of Secrets is divided into nine sections, each starts with a lever, and ends with a door. You must throw
the lever, and make it to the door without setting off the traps, and before the time expires": each section's timer
lever locks its axe trap while it creeps back shut (2-9 s, MM9's ClosingSpeed); the end door opened in time stays
harmless, opened late it swings the axe through the doorway and Chadwick marks a trap. Section 10 (the lever corner
behind the gate), 9 and 8 (two rooms west of the hub), 1 (the hall of fire-bolt floor plates, 61 plates each firing its
shooter), 2 (the corridor and the stair over a hidden spinning blade), 3 (the lever room: 22 levers on its walls, one
real, one twin on the far wall, 2.9 s to the door), 4 (the upper corridor over the flooded pool room: a double-axe trap
under a floor plate; the lower corridor and a submerged tunnel under it), 5 (the octagon and its elevator down), 6 (a
gauntlet of ten plates springing swinging bars, a crusher, a ram, scythes, spinning wheels and saws); past axe door 6
the exit gate opens and tells Chadwick "done": with no trap set off, key 245 and the reward (10 000 experience).

## Build and review

```sh
python3 level_generation/projects/mm9r_dungeonofsecrets/analyse.py           # DAT survey: work/analysis.json, dat_objects.json
python3 level_generation/projects/mm9r_dungeonofsecrets/tools/objects.py      # work/objects.txt: every object, non-default properties
python3 level_generation/projects/mm9r_dungeonofsecrets/convert.py --plan    # rooms only (15 s)
python3 level_generation/projects/mm9r_dungeonofsecrets/convert.py           # build, compile, install (30 s)
python3 level_generation/projects/mm9r_dungeonofsecrets/convert.py --lua     # the map Lua only, from the last build
level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_common/dungeon/lighting.py \
    level_generation/projects/mm9r_dungeonofsecrets                          # bake (64 samples, about 5 min)
python3 level_generation/projects/mm9r_common/hue_vs_lightmaps.py level_generation/projects/mm9r_dungeonofsecrets   # zones
python3 level_generation/projects/mm9r_dungeonofsecrets/make_scenarios.py
bash level_generation/projects/mm9r_dungeonofsecrets/work/run_scenarios.sh   # trial traps doors_exits
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_dungeonofsecrets
python3 level_generation/projects/mm9r_dungeonofsecrets/make_tour.py v02 [--original]   # 43 eye-level views
bash level_generation/projects/mm9r_dungeonofsecrets/work/run_tours.sh v02 [--set video.lightmaps=false]   # SDL_AUDIODRIVER=dummy
bash level_generation/projects/mm9r_dungeonofsecrets/work/run_tour_original.sh v02     # view_distance=unlimited
cd level_generation/projects/mm9r_common && python3 -m dungeon.sheet ../mm9r_dungeonofsecrets/review/v02 ../mm9r_dungeonofsecrets/review/v02_original
```

Review: [`review/v02_compare.jpg`](review/v02_compare.jpg) (43 views, MM9 original | native baked),
[`review/lighting_v02_compare.jpg`](review/lighting_v02_compare.jpg) (MM9 original | native unbaked | native baked),
[`review/v02_unbaked_compare.jpg`](review/v02_unbaked_compare.jpg) (geometry, unbaked),
[`review/props_compare.jpg`](review/props_compare.jpg) (model lighting off | on, six prop views),
[`review/v01_original_sheet.jpg`](review/v01_original_sheet.jpg) (the first look at the old map).

## Files

- `overrides.yml`: every DAT world model's rule (200), `seed_exclude` (the relay triggers MM9 parks outside the walls,
  the blade's pocket under the stair, Chadwick's booth), the sky and water textures, `thin_walls`, `model_lighting`;
  `convert.py`: the population, the perception hints, the water surface, the invisible steps, the double axes' carrier,
  the light colours and zone gains, the MM9 message dispatcher (a `dungeon.Hooks` subclass); `analyse.py`,
  `make_scenarios.py`, `make_tour.py`, `hue_zones.py`, `tools/` (`objects.py`, `floors.py`, `heights.py`, `leak.py`),
  `scenario_*.yml`, `review_tour_*.yml`, `review/`.
- `props.json`: 55 placements from the props project; `work/`: `build_report.json`, `doors.json`, `lights.json`,
  `content.json`, `walkability.json`, `rooms*.png`, `h_*.png` (floor heights), `runtime/`, `hue.txt`,
  `hue_summary.txt`, `brightness_v02.txt`, scenario logs, `run_*.sh`.

## Numbers

| | |
| --- | --- |
| Frame | `native = (LT.x, LT.z, LT.y) x 2.56`, no offset (the old map's frame) |
| Geometry | 2 082 source polygons -> 1 984 merged (+ 16 water runs, 32 invisible step faces) -> **5 096 native faces**, 7 545 vertices; 72 faces with no air in front dropped (backs against the rock, the tops and bottoms of the Firethrough fence and the Clouds pane box, the pool room's outer walls) |
| Air | sealed (`leaked_to_border` 0) once the 39 relay triggers MM9 parks outside the walls, the blade's pocket under the stair (Trigger (BUS), Timer (BUS)) and Chadwick's booth are out of the seeds; 2 seeded components: the course, and the lever room's sealed twin behind its Clouds window (seeded by its torch's lights; no party reaches it, MM9's neither) |
| Rooms | **10 + sector 0**: the hub with the entrance stair and Chadwick's booth, the lever corner and section 9's room, section 8's U room, the gauntlet, the exit corridor, the shaft's foot and the octagon, the ground floor (north and west corridors, the flooded pool room and its lower corridor, section 1's plate room), section 2's corridor and stair, the upper corridors and the lever room, the lever room's twin; faces per sector median 279, largest 1 462 |
| Portals | **10 faces**, all from door leaves (the axe doors, the exit gate); every portal joins two rooms; floor check 0 LT² |
| Movers | **155 mechanisms**: 9 axe doors and 9 axe traps, 11 timer levers, 21 fake levers, 61 fire plates, the gauntlet's 10 plates and 13 traps (saws in their carriers), the double axe's 7, the blade and its panels, the gates, the button, the elevator, the water grate, invisible parts |
| Lights | 164 `Light` -> **139 BLV lights** (colour x BrightScale x zone gain); 25 over the four-per-point cap bake only; `DirLight0` a bake spot; at most 4 per floor point (`content.json`) |
| Decorations | **55**: 34 claw torches, the claw lamp, 20 sconces with flames (props project; rows `mm9_clawtorch` 2386, `mm9_clawlampp180_x100` 2436, `mm9_sconce2` 2437) |
| Actors | **1**: Chadwick Boorsley (RUDE 417, MM9's body) |
| Translucent faces | 142: perception hints (122 at 0.5), the water (16 at 0.3), the Clouds faces (4, two-sided) |
| Exits | `ExitTrigger0` (object 362) to Frosgard (DungeonOfSecretsExit); arrival from Frosgard's ExitTrigger0 on StartPoint0 (facing west) |

## What each DAT object became

| MM9 | Native |
| --- | --- |
| `PhysicsBSP` | static world; `VisBSP` has no UserPortals here (the axe doors' `PortalName` Doorportal5 names none): every doorway comes from a door's leaves |
| `axe door 01-06, 08-10` (RotatingDoor 90 deg, PushOpen, CloseWaitTime 4) | rotating doors with doorway portals; a click is MM9's push ("use") |
| `axe trap 01-06, 08-10` (RotatingDoor 180 deg at 650/s, Solid 0) | rotating movers drawn untouchable (MM9's blades pass through; their DamageBrush throws) |
| `timer lever 01-10, 03a` (Door 18 LT, PushOpen, ClosingSpeed 2-9) | linear movers; a click opens; MM9's slow close is the section's clock |
| `fake lever 1-21` (Door, no triggers) | linear movers; a click moves them, nothing else |
| `floor01-61` (Door 6 LT down, CloseWaitTime 1) | linear plates, pressed by `trigger01-61` |
| `gplate1-10`, `gtrap1-10` (the gauntlet) | plates and traps: rotating bars (`gtrap1/2`, 120 deg), the crusher (`gtrap3`, 80 LT down), the ram (`gtrap4`, 120 LT), scythes (`gtrap5/6/10`, 75 deg), spinning wheels (`gtrap7a/b`, 360 deg, untouchable), the saw rails (`gtrap8a/b` with `saw8a/b` riding them) and the saw arm (`gtrap9` with `saw9`) |
| `saw8a/b`, `saw9` (RotatingBrush, AttachTo the gtraps) | built into their carrier's mover (one node); their spin is not carried |
| `Side Door`, `Top Door`, `Bottom Door`, `Axe Mover`, `Top Axe`, `Bottom Axe`, `Panel Mover` (the double axe) | movers; `Panel Mover` (all Invisible.dtx) has no faces and is a door in the Lua only; the axes are built where their carrier slides them (88 LT) and swing about their moved pivots (Deviations) |
| `doubleaxe upper/lower trigger` (Door, TouchToOpen) | linear plates opened by a polled box over them |
| `Sliding Panels`, `Blade` (the blade under the stair, 1080 deg) | a linear mover and a rotating one (one turn: Deviations) |
| `entrance gate`, `entrance button`, `exit gate`, `elevator` (TouchToOpen, 320 LT), `water grate` (+ its invisible `water grate opener`) | movers; the button and the grate take a click; the elevator opens when the party stands on its column |
| `ratdoortrigger` (an invisible relay Door) | an invisible mover in the Lua (its `_INV` part) |
| `knockback01-24` (DamageBrush: Damage, Current) | polled boxes: while on, the party in the box takes Damage once and is pushed along Current (`evt.PushParty`) |
| `Trigger` (123) | polled boxes (any part of the party in the box, on entry) or relays, with StartOn, SendDelay, ActivationCount and their messages 1-10 |
| `Shooter` (80: FireBolt, 5 damage, every 4 s) | `evt.FireMissile` from the object along its rotation, while on |
| `ClearWater0` (Water115.spr, SurfaceAlpha 0.3) | its top as non-solid translucent faces at 0.3 over the flooded pool room (16 runs of 32 LT tiles): the party wades |
| `PerceptionBrush0-16` (PerceptionValue 15-17) | untouchable translucent faces at 0.5 with a cog each, shown to a party with that Perception; those over a lever take its click |
| `WorldObject0` (Clouds1 strip in the lever room), the 3 `skymarker` faces | static, drawn with MM9's Clouds1 (`CLOUVKSJD0`) and a weak emitter in the bake |
| `WorldObject1` (Firethrough.dtx, the lever corner's fence) | static |
| `CommonerHuman2MaleA` CHADWICK (NPC417.scr, RUDE 417) | Chadwick Boorsley: friendly, immobile, row 367 (Peasant Human2 MaleA, MM9's PeasantM1) at MM9's body (12 x 34 LT half extents x Scale 1.2: radius 37, height 209), `mm9_rude_id` 417 |
| `Prop` (35 claw torches and the claw lamp), `Torch` (20 sconces with flames) | 3D decorations (props project) |
| `Light` (164) | 139 BLV lights (colour x BrightScale x zone gain); 25 over the four-per-point cap bake only |
| `DirLight0` | a bake spot (`dirlights: true`) |
| `ExitTrigger0` (to Frosgard, DungeonOfSecretsExit, AskPlayer) | MM9 positioned transition volume |
| `StartPoint0` | `party_start_points` (facing west into the hub); Frosgard's ExitTrigger0 arrives on it |
| `TOD_Sky0`, `SkyBox0`, `SkyPointer0`, `OutsideDef0`, `ObjectLight0`, `AmbientSound` (31) | not built (sky box, model-only light, sounds) |

## Scripted objects (`worlds/mm9/events/maps/dungeonofsecrets.lua`, written by `convert.py`)

The map has one script (NPC417.scr); the course is MM9's object messaging. The Lua carries the DAT links as data:
`DOOR` (each mover group's open and close seconds from MoveDist or RotationAngles over Speed and ClosingSpeed,
CloseWaitTime, Sticky, Locked, DoubleDoorName, Open/CloseTriggers), `TRIGGER` (box, StartOn, PlayerTriggerable,
SendDelay, ActivationCount, messages 1-10), `SHOOTER`, `DAMAGE`, `TOUCH`, and one dispatcher `send(target, message)`.

| MM9 | Native |
| --- | --- |
| Door / RotatingDoor messages `open`, `close`, `toggle`, `lock`, `unlock` | a locked door ignores open and close (from messages and clicks: the timer lever's lock holds its axe trap); Open/CloseTriggers go out when the door has finished moving; a door that is not Sticky closes CloseWaitTime after it opened unless locked then; the DoubleDoorName partner moves with it |
| Trigger messages `on`, `off`, `trigger`; touches | `on` enables and resets the count, `off` disables, `trigger` fires an enabled trigger (resets the count); a touch fires an enabled trigger with no activation pending and under its ActivationCount, on entry; SendDelay delays the messages (devdocs/mm9/MM9_DAT_TRIGGER_RUNTIME_GOAL.md semantics) |
| Shooter `on`, `off` | a fire bolt at once and one every ShootInterval |
| DamageBrush `on`, `off` | the knockback box above |
| RotatingBrush `on`, `off` (saws) | recorded (the saws do not spin) |
| **NPC417.scr** `DoTrap`, `RemoveTrap`, `done`, `:OnRude`, `:Init` | with key 243 (the trial started, RUDE 417 node 3): DoTrap gives key 244, RemoveTrap (the entrance button) takes it, `done` (the exit gate) gives key 245 and the quest sound when no trap went off; Chadwick's dialogue exit (event 50636) with key 246 and without 247 gives 10 000 experience, the quest sound and key 247; every map load takes keys 243 and 244 (`:Init`: a fresh trial on each visit) |
| The timer clock | MM9's lever closing times as they are (lever 01 9.5 s ... lever 03 3.0 s); the native party runs 768 units a second, MM9-like: the scenario runs every section within its time |
| **Unmatched** | the rat cameo's targets (`rat`, `rat0-2`, `rat door`, `ratnormal`, `ratmocking`, `ratscared`, `ratdead`: no such objects in the DAT, MM9 ignores the messages too) and `knockback25-29` (none in the DAT); the saws' and the blade's spin; NPC417.scr `:OnUse` (a voice line on a click: the click opens the dialogue instead); `AmbientSound` (31) |

All MM9 Trigger volumes are boxes polled about six to ten times a second against the party's path since the last
poll (a running party crosses a 4-LT plate trigger in one step), grown by the party's radius. The scheduler's clock
advances by the poll's real period, measured against the game minutes (a timer re-armed every 0.1 s fires on a frame:
about 0.17 s headless).

## Deviations from MM9 and why

- **The flooded pool room's water** (`ClearWater0`, 16 runs) draws with the liquid shader (2026-10-31, `water115_mm9`,
  `depth: shallow`, [shared helper](../mm9r_common/liquids.py)), opaque instead of MM9's SurfaceAlpha 0.3; the party still wades
  to the floor under it, and the sink-in teleport is unchanged. Sheet: `review/liquid/before_after_p1.jpg`.
- **See-through water (2026-10-31)** ([shared helper](../mm9r_common/liquids.py): MM9 opacity = the surface's alpha x
  its sprite's mean alpha, see-through where a floor of its room lies under it; engine: `liquids.yml` `opacity`,
  devdocs/INDOOR_TRANSLUCENT_FACES.md)): the flooded pool room is see-through (`ClearWater0`: SurfaceAlpha 0.3 x
  Water115.spr 0.42 = 0.12, `lqw115o12`, 16 faces): mostly clear, its ripples drawn light (MM9's real capture of the
  room shows the same caustic network). Sheet `review/liquid/see_through.jpg`.

- **Invisible steps** where MM9's player jumps or climbs out of water higher than the party can (the party steps 20
  LT, jumps about 35): onto the elevator's box and column in the octagon (5 steps of 16 LT; MM9's player jumps 60 LT
  onto the box) and out of the flooded pool room onto the west (2 x 12 LT) and east (3 x 10.7 LT) corridors. A sloped
  invisible ramp (Dook's Castle's route) was walked under, not up, from a floor at its foot: steps with risers work.
- **The submerged tunnel** under section 4's corridor (two 232 LT shafts joined at -256 LT, the east one under the
  water grate): MM9 swims it. No swimming: a party that sinks in comes up beside the west shaft (or the east one with
  the grate open), `evt.MoveToMap` on the same map. MM9's lower route around the double axe is not built as a swim.
- **The double axes** ride their carrier in MM9 (AttachTo Axe Mover, 88 LT out, then they swing): native movers do
  not ride movers, so the axes are built in the carrier's open pose (out of sight under the corridor floor) and swing
  about the moved pivots; the floor panels open on their own (their carrier `Panel Mover` has no faces).
- **The blade under the stair** turns one turn at MM9's speed (MM9: three; a rotating mover turns at most 360).
- **Non-solid MM9 movers** (axe traps, the blade, the axes and their carrier, the spinning wheels) are untouchable faces
  (scene `face_attribute_overrides`); MM9's DamageBrush knockbacks do the hitting.
- **Knockbacks** hit once per on-period with MM9's Damage and push the party along Current: Current's speed (at most
  1200 native units a second) for 0.25 s, so about 300 units for the axes' 2048, through `evt.PushParty` (a dash
  against the world's collision). Until 2026-11-09 they were an `evt.Jump` hop, whose horizontal speed a grounded
  party lost after one movement step: the throw moved it 9 units.
- **Chadwick's body** is MM9's size (209 tall) on the peasant row: the row's 120 would hide him under the booth's counter.
- **The trial resets on every map load** (NPC417.scr :Init runs on world start and mini-save load in MM9; :Init2 on a
  full save load keeps it). A save loaded mid-trial would restart it here, so **saving is forbidden in the dungeon**
  (the user, 2026-11-09, as in the Arena): the scene's `runtime_restrictions` (`tests/scenarios/mm9/no_save_maps.yml`).
- **Light colours**: x BrightScale and zone gains fitted to MM9's lightmaps (Baked lighting).

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

`../mm9r_common/dungeon/lighting.py` with `tools/lighting/baked_indoors/profiles/mm9_dungeonofsecrets.yml`: 64 samples,
3 bounces, **direct 2.2, bounce 1.0, ambient 0.45**, `dirlights: true` (DirLight0 over the entrance stair),
`max_lighting: 1`, the Clouds faces (`CLOUVKSJD0`: the window pane and the three skymarker faces by the exit) a weak
emitter (strength 0.3, display 1.0). 25 bake-only lights (over the four-per-point cap). One 4096 x 443 page.
`stale_bakes.py --assets output/mm9_rework/assets_dev --check` does not list the map.

Light colours (`convert.py` `scale_lights`): MM9 colour x BrightScale (0.2-1.0 here: Ruined Temple lesson), the
bake-only lights the same, times **zone gains fitted to MM9's DAT lightmaps** in two rounds (`LIGHT_GAINS`; the first on
a 16-sample draft, the second on the 64-sample bake: gain x MM9 / ours per channel). The ground floor's big room (the
pool room, the plate room, the north and west corridors) has the sector minimum light level 20 (`ROOM_LEVELS`): the
flooded pool room stayed at half of MM9 whatever its lights' gains (its blue fills are capped, bake only) and two of its
views read luma 10 (the player-light stand-in rule: no baked view under 10-12). Revert: `ROOM_LEVELS = []`.

**Brightness and hue: calibrated to MM9's DAT lightmaps** (walls are texture x lightmap x1). Per zone (`hue_zones.py`,
`../mm9r_common/hue_vs_lightmaps.py`, `work/hue.txt`, `work/hue_summary.txt`), ours / MM9 per channel and B/R:

| Zone | R / G / B ours/MM9 | B/R MM9 / ours |
| --- | --- | --- |
| hub | 1.03 / 1.06 / 1.06 | 0.76 / 0.78 |
| entrance stair | 0.71 / 0.77 / 0.77 | 0.88 / 0.95 |
| s10 s09 room | 1.00 / 1.06 / 1.05 | 0.77 / 0.81 |
| s08 room | 1.09 / 1.13 / 1.14 | 0.74 / 0.77 |
| north corridor | 1.01 / 1.14 / 1.14 | 0.74 / 0.84 |
| pool room | 0.82 / 1.03 / 1.19 | 1.19 / 1.74 |
| plate room | 1.00 / 0.99 / 0.99 | 0.38 / 0.37 |
| s02 corridor | 0.97 / 1.03 / 1.02 | 0.74 / 0.77 |
| s02 stair | 0.97 / 1.00 / 1.00 | 0.76 / 0.79 |
| lever room | 0.92 / 0.97 / 0.97 | 0.75 / 0.80 |
| s04 corridor | 1.11 / 1.27 / 1.25 | 1.04 / 1.16 |
| octagon | 1.03 / 1.05 / 1.06 | 0.69 / 0.71 |
| shaft foot | 0.89 / 0.67 / 0.67 | 0.33 / 0.25 |
| gauntlet | 0.79 / 0.71 / 0.71 | 0.38 / 0.35 |
| exit corridor | 0.69 / 0.85 / 0.86 | 0.76 / 0.95 |

Off by more than 10 %: the exit corridor (R 0.69, G 0.85) and the gauntlet (0.79 / 0.71) and the shaft's foot (G 0.67)
under; the upper corridor of section 4 (1.11-1.27: light from the pool room below through the floor slot and the bounce),
the north corridor and section 8's room (1.13-1.14) over. The entrance stair reads 0.71-0.77 because its zone holds the
three skymarker faces, which MM9's lightmaps count dark and ours at their display level (Lindisfarne's caveat); its
walls read like the hub's. Hue: ours a little cooler than MM9 throughout (B/R +0.02-0.06); the pool room bluer (1.74
against 1.19: its blue fills).

No real MM9 screenshot of this map exists (`devdocs/mm9_rework/overnight/real_mm9/`). Screen means against the "MM9
original" capture (information only, `work/brightness_v02.txt`, 43 views, centre crop): capture 80.7, native unbaked
47.3, **native baked 38.7 (x0.48)**; the capture is the old import drawn fullbright by our outdoor renderer. No baked
view is under luma 12 (darkest: the axe door 3 view 14.0, the pool room 15.6-15.9).

**Prop lighting.** 25 lights are over the four-per-point cap, so both paths were compared on six prop views
(`review/props_compare.jpg`): with `model_lighting` (light_scale 1.8) the plate room's twenty sconces drew black (their
red fills are among the capped lights, which model lighting never sees: Klusos House's lesson); the old path draws them
red like their walls; the claw torches read alike. `model_lighting` stays off.

## Checks

- `scenario_trial.yml` **passes** (201 steps): the whole trial clean, by real clicks. RUDE 417's 'Yes' as key 243; the
  entrance button (a click from its push side) opens the gate, clears the trap mark, and the party at it is in
  'knockback off' (every knockback goes off, as MM9's course starts); then every section: a click on the timer lever
  (its axe trap locked), the run to the end door as a wait of the path's time at the party's run (768 units a
  second over the plan's path: 0.6 s for section 10 ... 6.5 s for the gauntlet; the party is then set in front of the
  door, the route itself is not walked), a click on the axe door: the door opens, the axe trap stays shut, no trap;
  section 5's elevator by walking up the invisible steps onto its column (it carries the party down 320 LT); past axe
  door 6 a walk through the exit gate's open trigger: the gate opens, key 245 (finished clean), no trap.
- `scenario_traps.yml` **passes** (233 steps): the perception hints hidden at Perception 1 and shown at 30; section 10
  run late: the axe swings, DoTrap gives key 244, knockback10 throws the party, the axe trap goes back; a fire plate
  (trigger01 presses floor01, shooter1 fires, the plate rises and turns it off); the rat cameo's volley at the plate
  room's entrance (the shoottrigger chain, every ratshooter); six of the gauntlet's ten plates (bars, crusher, ram,
  wheels, saws, the saw arm): each springs its trap, stays locked down until the trap goes back, then rises; the double
  axe from its upper plate (side door, panels, the carrier, both axes; the side door shuts and re-arms the plates); the
  blade under the stair (its box, the panels 1.5 s later, Timer (BUS) re-arming the box); a fake lever moves and locks
  nothing; the water grate opens on a click and locks open; a party sunk in the submerged tunnel comes up (requested).
- `scenario_doors_exits.yml` **passes** (35 steps): axe door 10 shut stops the party walking at it, a click opens it,
  the party walks through; section 2's stair walked up (256 LT); out of the flooded pool room west (floor 0) and east
  (floor 8) by the invisible steps; Chadwick through the booth's bars: the RUDE 417 dialogue opens, and with key 246 its
  exit gives key 247 (and the experience); ExitTrigger0 raises `mm9_exit_trigger:362` (Frosgard).
- Walkability (`work/walkability.json`): 22 steps, 0 flights, 1 unreachable, 1 pit, 149 mover notes, 0 actor notes.
  The pit (2.0 M units², the flooded pool room and its lower corridor, floor -24 LT): **false**, the invisible steps lead
  out (the audit does not follow invisible faces; proved by the scenario walks). Steps: the pool room's edges (24-32 LT,
  the steps above), the shafts' rims, the stair past the exit (behind ExitTrigger0), plate pits. Unreachable: a 0.24 M
  ledge over the gauntlet's saw rail (118 above the floor; no monster in this map).
- Thin walls: `thin_walls: true`; dropped faces (`work/dropped_faces.json`, 72): backs against rock, the Firethrough
  fence's and the Clouds pane box's tops and bottoms, the pool room's outer wall backs: none is a partition.
- Floor check: 0 LT² of floor under another room's air. Mixed faces: 46 (31 with a minority over 20 %), door jambs.
- Every review view inspected (`review/v02_compare.jpg`, `review/lighting_v02_compare.jpg`): the geometry matches
  MM9's in all 43; no holes.
- Starts: StartPoint0 on the hub's floor facing west (view h01); Frosgard's ExitTrigger0 arrives on it (map_transitions
  row mm9:transition/frosgard/2, z -40 on the floor).
- Compiler unit tests: not rerun (no compiler change).

## Open items

- MM9 art for Chadwick (row 367's sprite stands in); swimming (the submerged tunnel and its grate route); the saws'
  and blade's spin; ambient sounds; MM6-MM8 density (PLAN.md: later).

## Not checked

- A desktop playthrough with real input: the course run by hand against each lever's clock (headless runs at 768 units
  a second; the scenario waits the path's time and clicks), the jump over the double axe's upper plate (no jump input
  in scenarios: the trial teleports past it), the knockbacks' throw on the desktop, the fire bolts hitting, the elevator
  ride seen, the surfacing move (same-map moves are applied by the frame loop), save and load mid-trial.
- The sconce flames from the side in game (the props project checked them in Blender only); the gauntlet's remaining
  four plates (gplate2, 5, 6, 10: same wiring as the six tested); the lower plate of the double axe; the water grate's
  route through the tunnel; arrival seen in Frosgard; Android.

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 15:00:13 (convert.py from the current shared converter, end 15:00:39): 0 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV is byte-identical to before (no face of this map met the rule); its baked lighting was removed for the scene file's water change of the same day, not for this rebuild; it has 5096 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_doors_exits.yml` pass, `scenario_traps.yml` pass, `scenario_trial.yml` pass.

## The poll's clock and two scenario timings (2026-10-31, after the engine timer fix)

The engine now keeps a self-restarting timer's period (`updateScriptedEventTimers`: a handler's restart of its own
timer counts from the alarm that ran it; see Training Hall's README). This map's 0.1 s poll used to tick about every
0.17-0.3 s, which the Lua compensated by measuring its period against the game minutes; that calibration counted a
partial first minute and ran the clock about 13 % fast. Now `clock = tick * 0.1` (`convert.py`, Lua only:
`convert.py --lua`, which now also applies the blade's single turn: before, `--lua` timed MM9's 1080 degrees, 3.6 s;
`adjust_source`). With the poll at its true rate two scenario expectations that relied on slow ticks failed:
- `scenario_doors_exits.yml`: knockback02 (MM9 `StartOn`) threw the party back down section 2's stair at axe door 2.
  MM9's party turns the axe doors' knockbacks off on arrival by crossing `knockback off` at the hub's east end; the
  scenario's walks start west of it and never crossed it (the slow poll looked at the party only after the walk had
  ended). The scenario now crosses it first (`Firedknockback_off` 1).
- `scenario_traps.yml`, section 6: a gauntlet plate is checked down and locked 0.5 s after the pose (was 1.2 s);
  gtrap3, the quickest trap, is back 0.53 s after its plate, which then lifts.
All three scenarios pass. No BLV or scene change.
