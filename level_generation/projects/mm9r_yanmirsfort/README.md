# MM9 rework: Yanmir's Fort (`yanmirsfort.blv`)

MM9's Yanmir's Fort (the ice fortress of the giant Yanmir in Frosgard: Yanmir, immune to every blow, must be lured
onto a floor whose supports the party has broken in the basement under it; the children in his cages; his key and the
teleporter out) converted from its DAT world into a native indoor map (BLV: sectors, portals, rotating and sinking
movers, lights, three exit volumes) on the shared dungeon converter
([`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md)). Built into the isolated review root
`output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's decoration rows and the prop models
([props project](../../props/mm9_yanmirsfort_claude/README.md)). No x4 textures yet.

Status 2026-10-31 (overnight run): geometry, 27 rooms, 79 movers (30 rotating double doors, 7 cages, the secret wall,
the six supports and the trap's four floors), 86 lights, 3 exits, 158 decorations, 11 chests, 73 actors, Yanmir's trap
(supports, lure, fall, keys), his key, the cages and children, the spawners and bug respawns, the perception hints, the
pool, baked lighting (128 samples, MM9's `LIGHTDEFS` ice light). Scenarios pass; the review sheets below were looked
at. The shared converter is unchanged: every map-specific choice is in `overrides.yml`, `convert.py` and `bake.py`.

## Build and review

```sh
python3 level_generation/projects/mm9r_yanmirsfort/convert.py --plan     # rooms only: work/rooms*.png (about 3 min)
python3 level_generation/projects/mm9r_yanmirsfort/convert.py            # build, compile, install (about 3.5 min)
level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_common/dungeon/lighting.py \
    level_generation/projects/mm9r_yanmirsfort                          # about 7 min at 16 samples (611 bake lights)
level_generation/projects/mm9r_yanmirsfort/work/ratios.sh               # lightmap texels ours / MM9's DAT per zone
level_generation/projects/mm9r_yanmirsfort/work/recompose.sh key=value  # profile change + recompose + ratios (seconds)
python3 level_generation/projects/mm9r_yanmirsfort/make_scenarios.py
for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_yanmirsfort/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_yanmirsfort
python3 level_generation/projects/mm9r_yanmirsfort/make_tour.py v01 [--original]   # also v01_unbaked
level_generation/projects/mm9r_yanmirsfort/work/run_tours.sh v01 v01_unbaked:unbaked   # desktop runs, one by one
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated yanmirsfort_v01orig --world mm9 --map yanmirsfort.odm \
    --assets "$PWD/output/mm9_rework/assets_original" --position -8064 -2458 1 --yaw-radians 0 --pitch-degrees 0 \
    --warmup 3 --seconds 300 --set video.view_distance=unlimited \
    --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_yanmirsfort/review_tour_v01_original.yml
python3 level_generation/projects/mm9r_yanmirsfort/work/pages.py review/v01_pages review/v01_original \
    review/v01_unbaked review/v01                                                  # compare pages, 6 views each
python3 level_generation/projects/mm9r_yanmirsfort/work/brightness.py review/v01_original review/v01_unbaked review/v01
```

`tools/dump_objects.py` (every DAT object with its properties: `work/objects.txt`), `tools/leak.py` (which seeds flood
the outside; found the relay triggers below).

## Numbers

- Frame: `native = (LT.x, LT.z, LT.y) * 2.56`, no offset (the old map's frame, int16). Storeys (LT): the ground halls
  and caves 0 (-16 to 64), the upper wings and the hall's north galleries 320-512, Yanmir's quarters (the throne) 256,
  the trap's basement on Planks0 at -376 (reached by the spiral stair south of it), the shaft under the trap to -3520.
- DAT: 9 264 source polygons (PhysicsBSP and the world objects) -> 8 775 merged; 333 faces dropped as having no air
  in front (the ice walls' and floors' outsides 271, the burlap curtains' backs against the walls 15, the outward faces
  of the invisible `Firethrough` brushes 32 and InvisibleBrush0's 5, a few metal trims).
- BLV: **10 667 faces**, 17 733 vertices, **28 sectors** (27 rooms), **31 portal faces** (30 MM9 UserPortals, the
  secret wall's leaves), **79 movers** (69 rotating: the 60 leaves of 30 double doors, the 7 cage doors, the secret wall and its
  invisible shell; 10 sinking: the six supports, YanDstruct0, FallingFloor0, Planks0, Xbeams0), **86 lights**, faces per
  sector max 1 157 / median 349. The outline limit is not reached (the compile passes).
- Content: **158 decorations** (props.json: 122 props, 24 claw lamps and torches, 11 chests, Yanmir's key), **11
  chests** (loot from the shared MM9 item sources), **73 actors**, 0 pads (MM9's touch triggers are polled boxes), 36
  wading faces (the west cave's pool) and the two exit gates' water sheets as translucent faces, 15 perception faces.
- Lights: 87 MM9 `Light` objects, 86 in the BLV (colour x BrightScale), 1 (Light2, the great hall's 3 932-unit fill)
  over the four-per-point cap bake-only; no DirLights; the cyan `LIGHTDEFS` of `yanmirsolidice1.dtx` (16/128/128,
  radius 640 LT) as 610 bake-only lights, one per polygon; no fog (WorldProperties has none on).

## What each DAT object became

| DAT | Native |
| --- | --- |
| `PhysicsBSP` | the static world; `VisBSP`'s 30 UserPortals are the door portals |
| 30 `RotatingDoor` pairs with a PortalName (`Door1a*/1b*`, `Door1-12`, `DoorTeleportLeft/Right`) | one `rotate` mover per leaf (MM9's 90° swing at 50-240 °/s, open-away, auto-close after CloseWaitTime 1-20 s, reopen on contact); a click swings the pair; each closes its UserPortal. `DoorTeleportLeft/Right` (Locked) open only with Yanmir's key |
| `RotatingDoor61-67` (Locked) | the children's cage doors: `rotate` movers, a click opens them once the party has key 7001 |
| `Secretdoor` (RotatingDoor, OpenTrigger `lock`) | `rotate` mover with a doorway portal from its leaves; a click opens it for good |
| `DestructableBrush0-5` (HitPoints 1, DeathTriggerTarget Trigger0-5) | the six wooden supports under the trap hall: scene destructibles (`motion: break`, 2026-11-06: static faces with cogs 20759-20764, HitPoints 1): a weapon hit breaks one, a click still does (the shared event 38000 + index, or its hint's click) (Scripted objects) |
| `YanDstruct0`, `FallingFloor0`, `Planks0`, `Xbeams0` (DestructableBrush) | the trap hall's floor and the basement's plank floor and ice beams: `sink` movers that drop when the trap fires (built shut; mover faces are solid, so the hall, basement and shaft are one room, room 11, drawn whole) |
| `InvisibleBrush0-15` | invisible collision faces (`Firethrough.dtx` and `Invisible.dtx`) |
| `WavySurface4/5` (WorldObject, `Water115.spr`) | the two exit gates' shimmering water sheets: non-solid translucent faces (0.85), animated |
| `BlueWater0` (ShowSurface, `Water115.spr`, SurfaceAlpha 0.7) | its top at -16 LT as 36 non-solid translucent faces (0.7) cut to the west cave on a 64 LT grid: the party wades to the bed under it (at most 62 LT deep) |
| `AIBarrier0-19` | not built: AI-only blockers (Default texture) |
| 87 `Light`, 1 `ObjectLight` | BLV point lights or bake-only; the ObjectLight (Light29, a model light) not built |
| `Prop`, `CandleProp` (ClawLamp, ClawTorch), `DestructableProp` (barrels, ice blocks, benches), `TreasureChest` | 3D decorations ([props project](../../props/mm9_yanmirsfort_claude/README.md)); the claws' ice orbs glow blue (their MM9 flames sit inside the opaque orbs); the chests open containers 0-10 (events 41-51) |
| `Yeti` x27, `Thrall` x15, `ThrallMaster` x4, `IceLobber` x9, `IceLobbercicle` x6, `ForestGiant` x4, `Yanmir` | actors at their DAT positions, facing 90 − ry, MM9 bodies (ABC extents x Scale x 2.56: Yeti 59 x 277 (one at Scale 0.85: 51 x 241), Thrall 31 x 174, Ice Lobber 38 x 159, Ice Lobbercicle 77 x 123, Forest Giant 154 x 845, Yanmir 154 x 957); MM9 hangs six Ice Lobbers from the ceilings (MoveToFloor 0): they stand on the floor under them (IceLobbercicle6 moved 32 LT to the nearest floor); IceLobbercicle2 stands on the trap hall's floor (a mover) |
| `CommonerChild*` x7 (`YanmirChild.scr`) | friendly, immobile children in the cages (row 367 Peasant, body 26 x 133 from PeasantChildBoy.abc); a click runs their use event (Scripted objects) |
| `StartPoint0` | start 0 at the west gate, facing east into the fort; the arrival from Frosgard's `TPS1` |
| `ExitTrigger TPS1`, `TPS2`, `PlayerExit` | MM9 positioned transition volumes: TPS1 (west gate) and TPS2 (the teleporter behind the locked doors) to Frosgard `YanmirsMainExit`; PlayerExit to Frosgard City `FallingStart` (and the shaft's floor, below) |
| `Trigger` x18 | boxes polled four times a second by the map script (Scripted objects); the relay triggers Trigger0-5 and TriggerTrapForReal (outside the walls) are `seed_exclude`d |
| `Spawner0-6`, `ScriptObject Respawn0-3` | spawn points of the map script (Scripted objects) |
| `PerceptionBrush0-7` | untouchable translucent faces (Perception.spr, Alpha 0.5, two-sided) with cogs 450-457 |
| `Camera YanmirCamera` | the cinematic `yanmir_death` (Cinematics) |
| `Fire` x15 (dust), `EarthQuake` x10, `AIRail` x228, `Marker` x51, `AmbientSound` x21, `OutsideDef`, `Skybox`, `WorldProperties0` | not built (dust and camera quakes, AI helpers, ambient sound later) |

## Scripted objects (`worlds/mm9/events/maps/yanmirsfort.lua`, written by `convert.py`)

| MM9 script | Objects | Native |
| --- | --- | --- |
| `YanmirBase.scr` `:Main` (DisableWandering, `AddTrigger Squish, Begin`), `:Reset` (CanDamage FALSE, TELP 1.3) | `Yanmir0`, `SquishTrigger0/1` | Yanmir is a `dormant` actor until the party enters either Squish box (the entrance corridor, the upper west hall), then `evt.WakeActor`; a monster damage hook sets every blow on him to 0 |
| `YanmirBase.scr` `:BD_OnDoor`/`:KickDoor`/`:OpenDoor` | the 29 doorway pairs (not the teleporter's) | while Yanmir is awake, any shut door within 700 of him is opened (MM9: he kicks it open with `stonedoorslam.wav`); native monsters do not open doors |
| `YanmirTrap.scr` (`SupportBroken` x6 -> `Trigger TriggerYanmirTrap on`, `:Init` removes the hints of broken supports) | `DestructableBrush0-5`, relays `Trigger0-5`, `PerceptionBrush2-7`, `YanmirTrap` | events 200-205, each support's `destroyed_event`: a weapon hit or a click breaks it (the destructible's wood sound and splinters; run any other way the event destroys it, `evt.DestroyDestructible`) and its hint goes; at six the trap is armed (map variable `TrapArmed`) |
| `YanmirBase.scr` `:OnTimeToDie`, `:DestroyFloor`, `:GiveEeps`; `YF_ExplodingFloor.scr`, `YF_FallingFloor.scr`; `TriggerTrapForReal` | `TriggerYanmirTrap` (AIOnly), `YanDstruct0`, `FallingFloor0`, `Planks0`, `Xbeams0` | the poll tests Yanmir's position against TriggerYanmirTrap's box once armed: the hall's floor, the basement's planks and beams drop (`stonecrumble.wav`, a status line), key 69 and 8 000 experience on the quest (key 68), else key 173 and 8 000; Yanmir falls into the shaft and is removed 2.5 s later (`Yanmir_EndOfWorld.scr` `:HandleYanmir`). `:OnDeath` (any other death, 5 000) is kept in the killed hook |
| `Yanmir_EndOfWorld.scr` `:HandlePlayer` -> `PlayerExit` | `EndOfWorldTrigger` | a party at the shaft's bottom goes to Frosgard City at `FallingStart` (`evt.MoveToMap`, map transition row 612's arrival; since 2026-10-31 `frosgardcity.blv`, FallingStart on the harbour's ice as the Frosgard City BLV builds it: `convert.py` `city_arrival`) |
| `YanmirHidden.scr` (`:InitYanmirHidden` on OnPostStartWorld) | `ForestGiant0-3` | hidden actors (group 2) while Yanmir lives; on the first load after his fall they appear (MM9 runs `titan.scr` on them then) |
| `YanmirKey.scr` (`:GiveKeyToPlayer`: GiveItem 570, GiveKey 7001, `:UnlockCages`) | `Yanmir'sKey` (in the east wing's north room, 236 LT), `DoorTeleportRight/Left`, `RotatingDoor61-67` | event 212: item 570 to the packs, key 7001 (QBit 97001), the key is gone (cog 420); with the key the teleporter doors (event 211) and cages (220-226) open on a click, without it "locked" |
| `YanmirChild.scr` (`:ShoutForHelp` once, RolloverText 200/201; `:OnUse` with key 7001: follow the party to TPS2 and escape) | `ChildFar0-3`, `ChildNear0-2` | the first child within its SightDistance (600 LT) of the party calls for help once per visit (MM9's RolloverText 201 with key 7001, else 200, from MMIXSCRIPTTEXT.csv: `mm9r_common/script_text.py`); a click (use event 53000 + object) with key 7001 sends the child to the teleporter: it is gone (`Escaped<name>`) |
| `writ.scr` (TELP 1.3 hijack) | `DoorTeleportLeft` | nothing to carry: it only sets the pair's DoubleDoorName (the converter pairs the leaves) |
| Spawner `DefaultSpawn` | `Spawner0-6`; `Trigger6-10`; the DeathTriggerTarget of nine Yetis | each of Trigger6/7/8/9/10 sends its spawner's monster once (Spawner0/1/2/4 a Yeti, Spawner6 a Thrall: `evt.SummonMonstersById`); each of the nine Yetis sends one more Yeti from its spawner when it dies (killed hook) |
| `YanmirFort_BugSpawn.scr` (`:OnRespawnMe`, `:DoSpawn`) | `Respawn0-3`; `SquishVictim`, `IceLobbercicle1-4` | when one of these Ice Lobbercicles (or one they sent) dies, another comes at its Respawn point 600-900 s later, once the party is more than 2 000 units away (MM9: out of sight) |
| `PropAnim.scr "onside"` | 7 beds | posed in the props project (lying on their side) |
| `Yanmir.scr` | `Givekey` | nothing (its Use and Trigger do nothing; YanmirBase gives the key) |
| PerceptionBrushes | `PerceptionBrush0` (the secret wall), `PerceptionBrush1` (the trap hall's floor), 2-7 (the supports) | 0 and 1 shown at Perception 10 (`evt.CheckSkill`, checked on load and every 3 s), 2-7 always (no PerceptionValue) until their support breaks; 0 goes when the wall opens, 1 when the trap fires |

**Unmatched** (not carried, with reasons): Yanmir's wandering along `YanmirPathA` (30 markers) and `:LookForBugsTick`
(he hunts and squishes the Ice Lobbercicles and wipes his shoe): no marker paths or monster-on-monster scripts; the
`PlayerRanAway`/`PlayerRanAway0` triggers (send him back to his path marker 18); the dust (`YanmirDust`, `FrostDust*`,
`CaveInDust*`) and camera quakes (`DoorQuake0-9`, Yanmir's `smalleq` footsteps); the children following the party
(`FollowPlayer.inc`): they leave at once; `AmbientSound` (21, a later pass).

## Cinematics

`yanmir_death` (`cutscene.py`, the shared `../mm9r_common/cutscenes.py`; devdocs/mm9_rework/MM9_CUTSCENES.md):
YanmirBase.scr :OnTimeToDie and Yanmir_Camera.scr. TriggerYanmirTrap (six supports broken, Yanmir in it) runs
`trapFires`, which starts the cinematic, unless the party stands on one of the six AIRails tagged UserData 555
(AITrk95-98, 233-234: the trap hall, its side room and basement, :DoCamera): then no camera, the same steps run on the
`T_FALL` timer and Yanmir plays StartDie/Fall from Lua. Timeline (9.3 s, one fixed shot from YanmirCamera's DAT pose,
fov 73.7, letterbox): 0 s :GiveEeps (step); 0-2 s face, Running, move to YanmirPathA4 (Wait 21 2); 2 s StartDie
(`Yanmir.abc` startDie 1.8 s); 3.536 s its DestroyFloor key: TrapFloor opens (step) and stonecrumble.wav (cue); 3.8 s
TrapPlanks (step, FallingFloor0 reaches Planks0), Fall looped and a 2.5 s drop to z -1800 (cues); 6.3 s removed at the
end of the world (step); the camera off 3 s later (:OnLinkBroken). Event ids: 36000 done, 36001-36004 the steps
(experience, floor, planks, gone). A map load with the trap fired and Yanmir not gone finishes the steps.

Tests (no conversion): `python3 cinematics_pilot.py` writes the scratch root's yanmirsfort.cinematics.yml and Lua;
`make_cinematic_scenarios.py` writes `cinematic_yanmir_death_play.yml` (console start, the fixed timeline: playing, key
173, a save refused, the floor down at 4.7 s, Yanmir gone at 6.7 s, a save allowed at 9.7 s), `_skip.yml` (skipped at
1 s: every step), `_trigger.yml` (the real trigger: supports, wake, lure, the party beyond DPortal20; the cinematic's
started var, all steps) and `_watch.yml` (the party in the hall: no cinematic, the timer path). The moment Yanmir's
chase reaches the trap varies by frames between runs, so the timeline is checked from the console start. All four pass
(2026-11-06), run from output/mm9_rework/cinematics_pilot_run (`build/game/openyamm --world mm9 --headless-run-scenario
<yml>`).
Captures: output/mm9_rework/cinematics_pilot_run/captures_yanmir_death/ (tour.yml: `cinematic play` from the south
door; Yanmir glides from his bed in the first 2 s there, as the console start has him elsewhere): 01 the empty trap hall down YanmirCamera's
line, 02 Yanmir's startDie at YanmirPathA4, 03 the floor down and Yanmir dropping into the pit, 04 the pit, 05 the
party's view again (sheet.jpg). The cave-in dust
(CaveInDust0-4, Fire) is not shown: there is no dust effect cue.

## Checks

1. **Every DAT world model has a rule** (the build stops otherwise); the skipped ones: `Skybox`, `BlueWater0` (its
   surface is our own faces), `AIBarrier0-19` (AI only), the `AITrk*` rails, `VisBSP`, `PerceptionBrush*` (our hint faces).
2. **Sealed air**: `leaked_to_border` false, one seeded air component (5.4 M voxels). The first plan leaked: MM9 parks
   the supports' relay triggers `Trigger0-5` beside the basement's walls, `TriggerTrapForReal` 1 500 LT over the roof and
   `Light63` in the rock under the treasure halls; they are `seed_exclude`d (`tools/leak.py` lists each seed's air
   component and whether it touches the grid's border). Dropped faces (`work/dropped_faces.json`, 333): outsides,
   curtain backs against walls, the invisible brushes' outward faces; `thin_walls: true` is on.
3. **Portals**: 31, each joins two rooms (`portals_without_two_rooms` 0): MM9's 30 UserPortals and the secret wall's
   leaves. No archway cuts were needed: MM9's double doors close every hall. The trap hall, its basement, the spiral
   stair and the shaft are one room (room 11): the trap's floors are movers, which the voxel pass does not count as
   solid, and the room draws whole from any of them.
4. **No holes**: the 69 views of v01 were looked at, original and native side by side (below): every room's geometry
   matches MM9's. Floor check: 1 192 LT² of floor under another room's air, all door sills (48 LT² each) and the spiral
   stair's foot at the dormitory (314 + 204 LT²). Mixed faces (`work/mixed_faces.json`): 642 with a minority over 20 %,
   ice walls along thin partitions; no fault seen in the views.
5. **Review sheets**: below.
6. **Walkability** (`work/walkability.json`, `audit.py`): 415 steps (172 of 33-40, 115 of 41-64, 128 of 65-127) and 80
   flights: the west ice cave's rough floor (sector 10: 185 steps, its ledges and the pool's rim) and the spiral stair
   down to the basement (sector 11: 159 steps and 79 of the flights, the narrow inner ends of its treads), the east
   wing's and the great hall's stairs (sectors 24, 17, 22). 17 mover notes: the seven cage doors' 56-unit sills and the
   trap's fallen floor (a 38 recess once down). 9 unreachable regions, no actor in any: the cages' raised floors (41
   above the room floor, 0.06 M units² each: the children stand in them, immobile) and a 123-high platform in the near
   cage hall (0.13 M units²). The basement is reached (the audit does not list it; the scripted scenario stands the
   party there and clicks the supports).
7. **Scenarios pass** (headless, real clicks for the doors, cage, key, secret wall, supports, chests and a child):
   - `scenario_doors_exits.yml` (53 steps): TPS1 raises its transition (object 777); Door1a8/1b8 stops the party, opens
     on a click and is walked through; the teleporter doors and a cage stay locked without the key; Yanmir's key (a
     click) gives item 570 and QBit 97001; the cage and the teleporter doors open; walking into TPS2 raises its
     transition (599); the secret wall opens on a click and is still open 20 s later.
   - `scenario_chests.yml`: the 11 chests open from in front of their models.
   - `scenario_scripted.yml` (126 steps): the perception hints at Perception 1 and 10; Yanmir asleep until
     SquishTrigger0 and unhurt by five party attacks (945/945); Trigger6 spawns Spawner0's Yeti; a Yeti's death spawns
     from Spawner2; an Ice Lobbercicle's death queues its respawn and it comes back after 920 s with the party away; the
     six supports broken (scene destructibles: one by 1 point of damage, five by clicks from the basement's planks; 2026-11-06; TrapArmed); Yanmir sees the party in his hall, follows
     it (with his door kicks) through DPortal19 and down the trap hall: the floor gives way under him (TrapFired, key
     173 without the quest), he is removed (hidden) and the floor stays down; after a reload the Forest Giants are
     visible; ChildFar0 with the key is clicked and leaves; a party on the fallen floor is sent to Frosgard City
     (FellToCity).
8. **Starts**: StartPoint0 on the floor at the west gate facing east (v01's first view); the arrival from Frosgard's TPS1
   is the start's floor (`map_transitions.txt` row frosgard/17).
9. **Compiler unit tests** (`build/tools/openyamm_indoor_source_tests`): 21 test cases, 205 assertions pass.
10. **Lights**: 86 BLV lights, no floor point under more than four (`content.json` `light_coverage`).

## Can the monsters reach the party

The audit lists no actor in a cut-off region (`actor` 0). Yanmir, the biggest body (154 x 957), was followed in the
scripted scenario (`report_state` every 4 s): from his hall (native -3277, -2294) through the great hall and the open
DPortal19 into the trap hall (863, -7460), where he fell with the floor; he keeps targeting the party while it stays in
his sight and stops when it leaves it (the "monsters stop short in sight" pattern of other maps). Yanmir's door
kicks are scripted (above): native monsters are not known to open doors; whether the Yetis, Thralls and
Lobbers get through MM9's AITriggerable doors in game was not tested (Not checked). Their regions are all reachable
by the audit's floor rules.

## Deviations from MM9 and why

- **The trap's floor drops 399 LT, not into the abyss.** MM9 destroys YanDstruct0 and FallingFloor0 (the hall's floor)
  and drops Planks0 and Xbeams0 into a 3 000 LT shaft, at whose bottom Yanmir (and a falling party) leaves the world. A
  native mover that travels more than 1 024 units is vertex-lit instead of keeping its baked light, and drew the hall's
  floor near black in the first tour; the four trap movers slide 399 LT (1 021 units) instead, so the fallen floor
  rests just under the basement's old plank level and covers the shaft. A party that comes to stand there after the trap
  fired has fallen through: it goes to Frosgard City at `FallingStart`, as MM9's EndOfWorldTrigger sends it. Yanmir
  lands on the fallen floor and is removed 2.5 s later. The shaft's geometry is still built (MM9's), unreached.
- **Supports also break on a click** (MM9: any weapon hit, which works too since they became scene destructibles).
- **Yanmir does not walk his path.** MM9 sets him wandering along `YanmirPathA` (30 markers) once woken, hunting the
  Ice Lobbercicles; here he stands until he sees the party and then hunts it, so the party lures him onto the broken
  floor (the scenario does exactly that). His door kicks are kept (scripted); his bug squishing, shoe wiping and
  return to the path (`PlayerRanAway`) are not.
- **The children leave at once.** With the key, MM9's children follow the party to the teleporter and run into it; here
  a click sends a child away (it vanishes), as if it ran for the teleporter. Their calls for help are MM9's
  RolloverText 200/201 (MMIXSCRIPTTEXT.csv) as status text and reach through walls (a distance test).
- **The Forest Giants appear on the next load** after Yanmir's fall, as MM9's OnPostStartWorld does (not at once).
- **Ice Lobbercicles hung from the ceilings** (MoveToFloor 0) stand on the floor under them.
- **Bug respawns** are timed while the map is loaded (map variables count the seconds; they keep across saves), and
  "out of sight" is "more than 2 000 units away" (no line-of-sight test).
- **The pool is a scene water volume** (the shared water rule, 2026-11-06: `water_volumes`, BlueWater0 with MM9's fog
  and tint; rebuilt 20:00, room mismatches 0, bed holes 0; `scenario_swim_check.yml` from
  `../mm9r_common/dungeon/swim_check.py` passes with the other scenarios and the four cinematic ones). The party
  wades it and its eye dips under only at the deepest spot. Before: a wading surface (no swimming, PLAN.md):
  non-solid, the party walks on the bed under it (at most 62 LT
  deep). Since 2026-10-31 its 36 faces draw with the liquid shader (`water115_mm9`, `depth: shallow`, opaque, no longer
  translucent; [shared helper](../mm9r_common/liquids.py)); the exit gates' vertical sheets (`WavySurface4/5`) keep their
  animated Water115 bitmap at 0.85. Sheets: `review/liquid/before_after_p1-3.jpg`.
- **See-through water (2026-10-31)** ([shared helper](../mm9r_common/liquids.py): MM9 opacity = the surface's alpha x
  its sprite's mean alpha, see-through where a floor of its room lies under it; engine: `liquids.yml` `opacity`,
  devdocs/INDOOR_TRANSLUCENT_FACES.md)): the west cave's pool is see-through (`BlueWater0`: 0.7 x Water115.spr 0.42 =
  0.29, `lqw115o29`, 36 faces); the gate sheets are unchanged (MM9: Alpha 1 x 0.42, not the 0.85 `PORTAL_OPACITY`).
  Sheets `review/liquid/see_through_p*.jpg`.
- **Brightness** follows MM9's lightmaps at x1 (below); MM9's dynamic `Fire` flicker (here only dust objects) is not
  added.

## Map-local converter changes (`convert.py`; the shared package unchanged)

- `edit_polygons`: BlueWater0's surface tiles (Dook's Castle's lake route, non-solid here).
- `populate`: props.json with Yanmir's key's event and cog, `scale_lights` (BLV colour x BrightScale), the perception
  hints (Ta'Sar's route), the polled boxes, the spawners and respawn points.
- `actors`: MM9 bodies by MONSTERS.txt row (Thjorad Mine's `mm9_extents`), the children's rows and use events, Yanmir
  `dormant`, the giants hidden, `on_floor` for the hanging Lobbercicles and the one on the trap's floor.
- `scene`: the translucent faces (perception hints 0.5, the pool 0.7, the exit gates' sheets 0.85).
- overrides.yml: `seed_exclude` (the relay triggers), the trap movers as 399 LT `slide`s, sector ambient 31 (the
  AGENT_BRIEF decoration workaround), `model_lighting: false`, `water:pool` texture. Prop lighting (AGENT_BRIEF
  "Prop lighting", revised 01:38): one light is over the four-per-point cap (Light2, the great hall's fill), so both
  paths were compared on six props (`work/prop_crops.py`, `work/model_lighting_props.txt`; crop mean luminance against
  the MM9 capture: v01 had `model_lighting: {light_scale: 1.4}` on, v02 the old path with sector light 31):
  dresser 0.96 old / 0.63 model, black chest 0.99 / 0.70, cabinet 0.71 / 0.53, bench 0.89 / 0.69, stove 0.83 / 0.68,
  bookcase 0.54 / 0.50; median **0.86 old, 0.66 model**. Neither draws a prop black here; the old path keeps the props
  brighter, as MM9 draws them, so it stays (`model_lighting: false`). The switch is scene-only: the BLV is
  byte-identical (md5 c8964fd9...).
- Props project (`../../props/mm9_yanmirsfort_claude/scripts/placements.py`): the entity `Bucket` (a DAT name that is
  also a decoration's) becomes `Bucket_173`, as the playbook's "Entity names" requires.

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

`bake.py` (the shared `../mm9r_common/dungeon/lighting.py` plus four bake-only fills in the basement corridor) with
`tools/lighting/baked_indoors/profiles/mm9_yanmirsfort.yml`: **128 samples**, 3 bounces, **direct 2.6, bounce 1.5,
ambient 0.2** (on sector light 31), `max_lighting: 1` (MM9 clips at x1), `texture_lights: {per_polygon: true, scale:
2.0, offset_lt: 8}`, `dirlights: true` (the map has no DirLight; the switch only passes the corridor fills). Bake-only
lights: Light2 (over the four-per-point cap), 610 `LIGHTDEFS` lights (one in front of each `yanmirsolidice1` polygon:
16/128/128, radius 640 LT), the 4 corridor fills. About 45 min at 128 samples through `bake_slot.sh`;
`tools/lighting/stale_bakes.py --assets output/mm9_rework/assets_dev --check` does not list the map.

**Where the colour comes from.** MM9's lightmaps here are strongly cyan (per zone R 0.18-0.31, G 0.32-0.89, B 0.32-0.90:
B/R 2.0-2.9, G/R 1.7-2.9). The first bake (direct 0.9, ambient 1.725, the sector-31 workaround's numbers of Ta'Sar)
came out neutral (B/R 1.1-1.6) and its trap hall at 0.43 of MM9: the ice texture `yanmirsolidice1.dtx` carries a
`LIGHTDEFS` cyan light that lights every surface near it in MM9, and the default one-light-per-brush put a single light
at the centre of PhysicsBSP's 600 polygons spread over the whole map. One light per polygon (the Lich Lab's route) at
2x and a weak neutral ambient give MM9's hue. The pure-blue `Light`s (0/0/255, BrightScale 1) make the rooms around
them deep blue, as MM9's lightmaps (B/R up to 3.2 in the children's room). The draft bakes at 16 samples were blotchy
(611 lights); 128 samples leave a little texel noise on the floors of the blue rooms.

**Calibrated to MM9's own DAT lightmaps** (AGENT_BRIEF "How MM9 draws light": texture x lightmap x1), per zone
(`hue_zones.py`, `../mm9r_common/hue_vs_lightmaps.py`, `work/ratios.sh`, `work/ratios_final.txt`), lightmap texel
luminance ours / MM9's and hue (B/R ours, MM9's in brackets):

| Zone | MM9 | ours | ratio | B/R |
| --- | --- | --- | --- | --- |
| entrance corridor | 0.408 | 0.457 | 1.12 | 2.10 (2.71) |
| great hall | 0.579 | 0.671 | 1.16 | 2.18 (2.56) |
| great hall, north galleries | 0.460 | 0.510 | 1.11 | 1.90 (2.29) |
| west wing | 0.477 | 0.459 | 0.96 | 2.00 (2.40) |
| north quarters (the throne) | 0.420 | 0.589 | 1.40 | 1.87 (2.21) |
| east wing | 0.444 | 0.428 | 0.96 | 2.05 (2.34) |
| near cage hall | 0.595 | 0.526 | 0.88 | 2.19 (2.68) |
| west ice cave (pool) | 0.465 | 0.483 | 1.04 | 3.56 (2.03) |
| trap hall | 0.770 | 0.488 | 0.63 | 1.98 (2.89) |
| basement (supports) | 0.646 | 0.787 | 1.22 | 2.93 |
| basement corridor and spiral stair | 0.489 | 0.271 | 0.56 | 2.15 |
| dormitory | 0.306 | 0.312 | 1.02 | 2.72 |
| east ice cave | 0.335 | 0.420 | 1.25 | 3.20 |
| treasury | 0.559 | 0.453 | 0.81 | 1.94 |
| east barracks | 0.412 | 0.360 | 0.87 | 2.46 |
| children's room | 0.227 | 0.284 | 1.25 | 3.24 |

Mean of the zone ratios 1.02. Off by more than 10 %: the trap hall (0.63: MM9's cyan lightmaps there are saturated near
full, ours clip at x1 in blue first), the basement corridor (0.56, after the four fills of `bake.py`; 0.47 without), the
north quarters (1.40), the east cave and children's room (1.25), the basement (1.22), the treasury (0.81), the near cage
hall (0.88), the east barracks (0.87), the great hall and entrance (1.12-1.16). Our hue stays a little less blue than
MM9's in the halls (B/R 1.9-2.2 against 2.2-2.9) and bluer in the caves. No real MM9 screenshot of this map exists in
`devdocs/mm9_rework/overnight/real_mm9/`. Profiles of the steps: `work/profile_v1.yml` (first, neutral),
`profile_v2.yml`/`profile_v3.yml` (texture lights x1, x2), `profile_final.yml`.

**No pitch-black rooms** (AGENT_BRIEF, MM9's player light): the darkest final view is r20_a at luma 20.7 (a curtained
room by the west wing), then r26_a 30.6 and r14_b 33.0; none is under 12, so no extra floor was added (the sector
ambient floor stays the profile's `ambient_scale` 0.2 on sector light 31; raise it to add one).

## Brightness

For information (the capture is the old import drawn nearly unlit, AGENT_BRIEF): screen means of the 71 tour views
(centre crop, Rec. 709, `work/brightness.py`, `review/brightness_v03.txt`): **capture 122.5, native unbaked 50.0,
native baked 90.0 (x0.73 of the capture)**. The views furthest under the capture are the blue-lit rooms (r20_a x0.21,
f12_key x0.24, r14_b x0.26, f10 x0.27 where half the frame is a wall the camera stands in); the cyan corridors and halls
read x0.9-0.95 (r01, r24, r27, r07).

## Sheets (looked at)

- `review/v03_pages_p01-p12.jpg`: MM9 original | native unbaked | native baked, 71 views (21 features, 2 per room, 2
  flame views), 6 per page.
- `review/v03_compare.jpg` (original | baked) and `review/lighting_v03_compare.jpg` (original | unbaked | baked at the
  13 lighting views).
- `review/flames01/`, `review/flames01_sheet.jpg`: a claw torch from the side and the front, a hanging claw lamp: the
  orbs glow blue, the torch's flame card sits on the orb (small from below).
- `review/v01*` and `review/v02` are the earlier rounds (v01: model lighting on and the long trap sink that drew the
  hall's floor black; v02: the 128-sample bake before the corridor fills).

## Not checked

- Yanmir's fall and the floor's drop seen in a running game (the scenario proves the states, the key and the removal).
- The children's call for help and their click in a desktop run (the tours show the call; the scenario clicks one).
- Arrival from Frosgard by walking its TPS1 (the transition row's arrival is the start's floor); Frosgard City's
  `FallingStart` arrival.
- Combat beyond Yanmir's chase; whether ordinary monsters get through doors.
- The bug respawn and spawners in a desktop run (headless only).
- The pool's wading depth in a desktop walk (the deepest bed is 62 LT under the surface).
- Real MM9 screenshots of this map (none exist).


## Open items

- MM9 models for the Yeti, Thrall, Lobbers, giants and Yanmir draw what the review root's actors.yml gives them (another
  session builds the MM9 creatures); the children use a peasant row's body.
- Yanmir's path walking and bug hunting, the children's following, the dust and quakes, ambient
  sounds (Unmatched above).
- Whether native Yetis, Thralls and Lobbers pass the doors in game (AITriggerable in MM9).
- The rough bake in the rooms lit by the pure-blue lights (some texel noise is left on their floors at 128 samples).
- A density and pack pass (PLAN.md: later); x4 textures last.

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 14:52:25 (convert.py from the current shared converter, end 14:56:12): 35 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV now has 10632 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_chests.yml` pass, `scenario_doors_exits.yml` pass, `scenario_scripted.yml` pass.
Blocker probes: 8 walks into helper brushes resting on the floor stop short of them, 8 identical before and after (their sides still block).
