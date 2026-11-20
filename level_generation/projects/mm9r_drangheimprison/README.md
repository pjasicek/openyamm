# MM9 rework: Drangheim Prison (`drangheimprison.blv`)

MM9's Drangheim Prison (front door and secret well in Drangheim) converted from its DAT world into a native indoor map
(BLV: sectors, portals, rotating and linear movers, ladders, lights, exit volumes) on the shared dungeon converter
([`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md)). Built into the isolated review root
`output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's decoration rows and the prop models
([props project](../../props/mm9_drangheimprison_claude/README.md)). No x4 textures yet: that is the project's last step.

Status 2026-10-30: geometry, 90 rooms, 105 movers, 5 ladders, 125 lights, two exits, 261 decorations, 6 chests, 80
actors, the prison's quests and scripted objects, the six perception hints, and baked lighting. Guards, the Dwarven Guard,
prisoners and commoners have no MM9 3D models yet (below).

## Build and review

```sh
cmake --build build --target mm9_compile_indoor_source openyamm -j25   # inside locks/cmake_build.lock
python3 level_generation/projects/mm9r_drangheimprison/convert.py --plan   # rooms only: work/rooms_<storey>.png
python3 level_generation/projects/mm9r_drangheimprison/convert.py          # build, compile, install
python3 level_generation/projects/mm9r_common/dungeon/lighting.py level_generation/projects/mm9r_drangheimprison
python3 level_generation/projects/mm9r_drangheimprison/make_scenarios.py
for s in doors_exits chests scripted quests immobile; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_drangheimprison/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_drangheimprison
python3 level_generation/projects/mm9r_drangheimprison/make_tour.py v03 [--original]
./tools/run_game.sh --isolated dp --world mm9 --map drangheimprison.blv --assets "$PWD/output/mm9_rework/assets_dev" \
    --position -2171 -7148 -2231 --yaw-radians 1.5708 --pitch-degrees 0 --warmup 3 --seconds 280 \
    --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_drangheimprison/review_tour_v03.yml
./tools/run_game.sh --isolated dporig --world mm9 --map drangheimprison.odm \
    --assets "$PWD/output/mm9_rework/assets_original" ... --set video.view_distance=unlimited \
    --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_drangheimprison/review_tour_v01_original.yml
```

The original-map tour must run at `video.view_distance=unlimited`: the old scene's `view_distance_scale: 0.4` fades
distant geometry, which is our renderer, not MM9 (Drangheim Prison has no MM9 fog).

## Numbers

- Frame: `native = (LT.x, LT.z, LT.y) * 2.56`, no offset (the old map's frame). Storeys: cave -1768 (secret way in),
  lower hall -1528, lower level -1400, gate and interrogation block -872, main -744, middle cells -616, smithy -160, top
  cells -32.
- 8 858 source polygons (PhysicsBSP and static world models) -> **12 844 native faces**, 19 833 vertices (241 polygons
  triangulated); 577 faces with no air in front dropped (between brushes).
- **90 rooms** (+ sector 0), one sealed air component, no leak, median 85 faces, largest 638.
- **96 portal faces**: 22 MM9 UserPortals, 44 from door leaves, 24 archway cuts, 6 `rect_portals` (four booth windows,
  the hatch over Ladder0, the grate over Ladder3). Every portal joins two rooms.
- **106 movers**: 75 `rotate` (MM9's own swing: double doors, cells, booth doors, levers, the well's lid and wheel, the
  hatch), 24 `dat` (MM9's linear doors), 6 fixed coop gates (`slide`, nothing moves them; each is a doorway portal).
- **5 ladders** (scene `ladders`): Ladder0 (cave to storeroom, under the hatch), Ladder1 (cave into ExitTrigger0), Ladder2
  and Ladder3 (cow pen passage to smithy), Ladder5 (well shaft).
- **125 lights** of MM9's 133; 8 over the four-per-point cap light the bake only. No floor point under more than four.
- **261 decorations**, **6 chests** (loot from the shared MM9 item sources), **3 pads**, **80 actors**.

## What each DAT object became

| MM9 | Native |
| --- | --- |
| `PhysicsBSP` + `WorldObject*`, `InvisibleBrush*`, `Lava0` (Kato volume) | static world, invisible collision; `VisBSP` only for its UserPortals |
| `RotatingDoor` doors, `Celldoor*`, `guardstation1door*` | `rotate` movers, one per leaf, MM9 pivot, angle, speed, auto-close (`CloseWaitTime`) |
| `Door` `DDoor3-11`, `ElevatorDoorL/R`, `Door0`, `Door1`, `Door2`, `SecretDoor0` | `dat`: MoveDir, MoveDist, Speed; doorway portals |
| `Celldoor18` | `rotate` with `authored_open` (2026-11-06): MM9 authors it standing open (StartOpen), so it is built swung shut and starts open; lever17 swings it (event 214), a click says locked (230) |
| `RotatingDoor6-11` | the coops' gates, RotationAngles 0: fixed, each a doorway portal so the coop shows through its bars |
| `lever*`, `blever*` | `rotate` (15 degrees), click events |
| `Lid1`, `LidWheel1`, `RotatingDoor3` | `rotate`: the lid swings flat over the well while its wheel turns; the hatch rises over Ladder0 |
| `Ladder0-3`, `Ladder5` | scene `ladders` |
| `ExitTrigger1` | MM9 positioned transition volume to Drangheim (front door) |
| `ExitTrigger0` | the same; Ladder1 climbs into it (the secret way out) |
| `StartPoint` `DPFrontDoor`, `DPSecretStart` | starts 0 and 1 |
| `Prop`, `Brazier`, `Barrel`, `BonePile`, `DestructableProp`, `TreasureChest` | 3D decorations (props project) |
| 13 monster classes | placed actors; `DwarvenSmith1` omitted (its script removes it at start) |
| `Trigger` (3) | 3 pressure pads |
| `PerceptionBrush0-5` | 12 untouchable translucent faces (Perception.spr, 20 frames at 15 fps, brush `Alpha` 0.35, two-sided) with cogs 300-305: the outlines MM9 draws on secret panels and the grate, shown at Perception 12 (`PerceptionValue`), checked on load and every 3 s. A click or the use key passes through them (`indoorFacePassesPicks`): Door2, the cook's secret door, stands between the two faces of its outline and could not be opened before 2026-11-08 |
| `PortalZone7`, `AIBarrier0`, `AIRail`, `Marker`, `ObjectLight`, `SinkWater0`, `BlueWater0` | not built; the markers' positions are used by the map's Lua, the sink's surface is a face |

## Scripted objects (`worlds/mm9/events/maps/drangheimprison.lua`, written by `convert.py`)

| MM9 | Native |
| --- | --- |
| **Pass and alarm**: `DrangheimHostility.inc`, `AlarmControl.scr`, `Guardhelp.scr`, `GuardToNegate.scr` | keys 5007 (pass) and 5006 (alarm). Inner guards are hostile unless the party holds the pass without the alarm; the gate guards mind only the alarm. The party hurting or killing a guard (damage/killed hooks, `context.byParty`: MM9's `IsPlayer`; a Nagate's blow does not) rings `alarmbell.wav` and sets 5006. The smith is no guard (his script has no hostility) |
| **Gate guards**: `GuardRude.scr` (dialogues 425, 426, ScriptParams) | `OnRude` (events 51033-51035): the alarm given in the talk goes off; Guard2 hands over item 446; Guard0/1 stand at PassMarker1/2. 1 in 20 sleeps from the map's start (`LoopAnim sleep`) until clicked or the alarm (2026-11-11) |
| **The cook**: `NPC419.scr` (419) | `OnRude` (51039): with key 5004 gives 5005, which lets `Celldoor29` open on a click; any other end of the talk raises the alarm. Quest markers: MM9 keeps the deal in keys only (no journal entry), so the cook and Antoni carry authored key-state markers (`mm9_quest_interaction_overrides.yml` `key_interactions`) |
| **His brother**: `NPC427.scr` (427) | `OnRude` (51044): key 369 gives 370, 4000 experience, the quest sound; he is gone, also on later loads |
| **Ivsar Forktooth**: `NPC90.scr` (90) | `OnRude` (50068): takes key 194, reopens the dialogue when 194 stands without 242, else raises the alarm (`:FollowPlayer`); with key 17 he is gone and meets the party outside |
| **Prisoners**: `DrangheimPrisoner.scr` (431) | Use events (54067-54069): without the pass, 500 experience once each, then dialogue 431 |
| **Cell levers**: the levers' Open/CloseTriggers | each lever (events 200-222) toggles itself and its cell (lever17: Celldoor18, which starts open); locked cells say so (event 230) |
| **Interrogation**: `DrangheimInterrogator.scr`, `DrangheimWarden.scr`, `DrangheimDoorman.scr`, `TriggerBeatings0/1` | either pad, once: for each of three prisoners the interrogator walks to the cell's MarkerBeating, the warden (`aware`) works the lever, the prisoner comes out and cowers, follows him along MarkerBeating to 9 (`evt.MoveActorTo`), the doorman's `RightDoor0/LeftDoor0` open and shut, `beatdownmix8bit.wav` plays, and they walk back and he is sent into his cell (2026-11-11; it teleported them before). It stops when one of the three is dead or the alarm is up |
| **Smith**: `DrangheimSmith.scr` | his round is a marker path (`smith_round`): hammering at MarkerAnvil (attack clip looped, 30-35 s, a clang every 3 s while he is there), the sword cooled 5 s at MarkerWater, put on the WeaponRack; `Door1`'s click stops him where he is and restarts him (its Open/CloseTriggers). He holds MM9's hammer (`held_items`, `Socket_RHand1`) and swaps it for Kira's sword from leaving the anvil to the rack (`:AttachHammer`/`:AttachSword`, Lua timer 263) |
| **Barracks guards**: `GuardToNegate.scr`, `NagGuardTrigger0` | only the three barracks guards (group 4) and the Nagate are enemies (`SetMonsterRelation({group = 4}, ...)`: GuardToNegate.scr's own `AddEnemy Nagate`; giving it every guard row made all guards fight the pen's Nagate at load and relay alerts about them across the prison); the pad plays the guard's call once |
| **Well lid**, **hatch** | click events (240, 241) |

The dialogues are MM9's own RUDE rows; a click on an indoor NPC opens them through the shared
`GameplayDialogController::activateMm9ActorDialogue` (2026-10-30), with the actor as the source so `OnRudeExit` runs.
`tools/mm9_import_discovery/mm9_scr_to_lua.py` rejects these scripts (`wait`, `trigger`, objects that are no generated
actors), so their callbacks are written here, each citing its routine.

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

**Installed: lightmap-matched (re-lit 2026-10-31, the user's decision of 2026-10-30: dungeon lighting follows MM9's DAT
lightmaps for brightness and hue; MM9 draws walls as texture x lightmap x1, `devdocs/mm9_rework/MM9_RENDER_LIGHTING_RE.md`).**
`../mm9r_common/dungeon/lighting.py` with `tools/lighting/baked_indoors/profiles/mm9_drangheimprison.yml`: one 4096 page,
125 BLV lights + 8 bake-only lights over the four-per-point cap + MM9's 3 `DirLight`s (`dirlights: true`), 64 samples,
3 bounces, **`direct_scale` 0.41, `bounce_scale` 6, `ambient_scale` 0.58, `ambient_colour` (0.8, 1, 1), `max_lighting`
1**. Sector minimum light 20 (unchanged). Passes in `output/mm9_rework/bakes/drangheimprison`; the re-light was a
`--recompose` through `../mm9r_common/bake_slot.sh` (no Cycles run). `tools/lighting/stale_bakes.py --assets
output/mm9_rework/assets_dev --check` does not list the map.

**The floor's tint.** MM9's lower storey reads (41, 61-66, 75-84) in every zone: its red never drops under 41, the
WorldInfo `AmbientLight 40 50 50` that MM9's preprocessor put under the lightmaps. A neutral floor left our lower storey
too warm (B/R 1.6-1.8 against 1.8-2.0) and the upper levels too warm as well (0.76-0.85 against 0.99-1.10). The
profile's `ambient_colour` (0.8, 1, 1) is that ratio; with it the fit's error fell from 0.058 to 0.011.

**Method.** `../mm9r_common/relight_fit.py --grid --max 1 --ambient-colour 0.8 1 1` (the saved passes composed per zone
without Blender, fitted to the zones' mean, B/R, G/R and MM9's map-wide texel quantiles 0.19 / 0.24 / 0.39). Zones:
`hue_zones.py`, ten k-d boxes (`../mm9r_common/relight_zones.py`). Per room (`work/relight/fit_after.txt`) no room is
near black: MM9's darkest texels here are about 0.15 (the ambient floor).

Lightmap texel luminance ours / MM9's DAT lightmaps per zone (`../mm9r_common/hue_vs_lightmaps.py`,
`work/relight/hue_before.txt`, `hue_after.txt`):

| Zone | MM9 luma | before | after | ratio before -> after | B/R MM9 / after | G/R MM9 / after |
| --- | --- | --- | --- | --- | --- | --- |
| z01_low_west_s | 0.280 | 0.351 | 0.280 | 1.25 -> **1.00** | 1.27 / 1.19 | 1.19 / 1.20 |
| z02_low_west_n | 0.280 | 0.362 | 0.286 | 1.29 -> **1.02** | 1.02 / 0.99 | 1.07 / 1.07 |
| z03_low_mid_s | 0.228 | 0.254 | 0.227 | 1.12 -> **1.00** | 1.83 / 1.69 | 1.50 / 1.52 |
| z04_low_mid_n | 0.235 | 0.254 | 0.226 | 1.08 -> **0.96** | 1.91 / 1.66 | 1.55 / 1.51 |
| z05_low_east_s | 0.242 | 0.264 | 0.232 | 1.09 -> **0.96** | 2.03 / 1.76 | 1.60 / 1.56 |
| z06_low_east_n | 0.234 | 0.261 | 0.231 | 1.12 -> **0.99** | 1.92 / 1.74 | 1.54 / 1.54 |
| z07_upper_east_s | 0.260 | 0.344 | 0.276 | 1.33 -> **1.06** | 1.44 / 1.22 | 1.29 / 1.22 |
| z08_upper_east_n | 0.279 | 0.357 | 0.283 | 1.28 -> **1.01** | 1.09 / 1.03 | 1.10 / 1.11 |
| z09_upper_west_s | 0.264 | 0.333 | 0.270 | 1.26 -> **1.02** | 0.99 / 0.97 | 1.07 / 1.07 |
| z10_upper_west_n | 0.266 | 0.338 | 0.272 | 1.27 -> **1.02** | 1.00 / 0.97 | 1.06 / 1.06 |

The cold blue-teal lower storey (B/R 1.66-1.76) and the neutral, faintly teal upper levels now follow MM9; the lower
storey stays a little less blue than MM9 (x0.87-0.92 in B/R).

**Screen brightness** (the 52 v06 views, `work/relight/views.txt`, centre crop luma): capture 33.5 (information only;
here the old import is dark too), unbaked 57.5, old bake 32.1, **lightmap bake 25.0 (x0.75)**. Darkest baked views: the
lower stairs (l01) 15.4, the cave ladder 16.2, the cow pen 16.2, the east room 17.4: none under luma 12, so no
player-light floor. No real MM9 screenshot of this map exists.

**Props: `model_lighting: true`** (`overrides.yml`; the scene's block: AmbientLight 40 50 50, ModelAdd 30). Same bake both
ways (`../mm9r_common/relight_props.py`, `work/relight/model_lighting_props.txt`): relative brightness of the props to
their view, capture 1.07, old path 1.81, **model lighting 1.40**; views with props under x0.6 of their view: old 4, model
0. The old path overlights the lamp-lit rooms (the warden's booth, the coops and the kitchen at x3-4 of their view: pale
tables in the interrogation room) and draws the guards at the front door and in the entrance hall nearly black; model
lighting keeps both near the capture (`review/lighting_v07_props_compare.jpg`, capture | old | model). Seen on the
sheet: the Nagate beetles turn from green to a warm brown under model lighting near the orange lamps. The 8 capped
lights do not reach the models. The rebuild left the BLV byte-identical (the scene gained the block); the five
scenarios (chests, doors_exits, immobile, quests, scripted) pass.

Sheets (looked at): `review/lighting_v07_compare.jpg`, `review/lighting_v07_p01-p09.jpg` (capture | unbaked | old bake |
lightmap bake with model lighting); `review/lighting_v07_baked` holds the same bake with the old prop path.

**Documented alternative: the capture-matched bake** (installed until 2026-10-31): `work/profile_capture_matched.yml`
(direct 0.75, bounce 6, ambient 0.55, neutral floor, no ceiling): lightmap ratios 1.08-1.33, screen mean 32.1 against
the capture's 33.5. To switch back: copy it over the profile, `model_lighting: false` in `overrides.yml`, `convert.py`,
then `--recompose` as above and the scenarios.

### History: capture-matched brightness (2026-10-30)

Mean of the 52 tour views, centre crop, MM9 at `view_distance=unlimited`: MM9 31.9, native unbaked 56.0, baked 30.3
(`direct_scale` 0.75, `ambient_scale` 0.55). 43 of the 52 views lay within 0.8-1.4 of MM9; the rest were bodies in
front of the camera, `c04_well_shaft` (blue in the old capture, dark here) and the rooms round a hanging brazier or the
forge (1.4-1.65). Sheets: `review/v06_compare.jpg` (52 views, MM9 | native), `review/lighting_v05_compare.jpg`,
`review/hints/` (the glow at Perception 12).

## Checks

- Scenarios (all pass, real clicks throughout): `scenario_doors_exits.yml` (the front door raises ExitTrigger1; RightDoor1a stops the party, opens
  and is walked through; Celldoor6 stays locked, lever5 opens and shuts it; the shut hatch stops a climb up Ladder0, the
  open hatch lets the party out on top), `scenario_chests.yml` (the 6 chests), `scenario_scripted.yml` (the inner guards
  hostile without a pass, the gate guards not; grate and smith; the interrogation's steps), `scenario_quests.yml` (a real
  click on Guard2 opens RUDE 426; its rows give the pass, `OnRudeExit` hands over the item and the guards stand down;
  the cook's deal unlocks Celldoor29; Antoni's reward; Ivsar's alarm), `scenario_immobile.yml` (the 9 immobile actors, guards at the gate
  and the NPCs, hold their places for 30 s; generated from the scene). `scenario_scripted.yml` also checks the hints off at Perception 1 and on at 12.
- Walkability (`work/walkability.json`): 2 steps (a 41 edge in the smithy, the hatch's rim), 128 mover notes (door and
  lever frames; a door's lip reads the same open and shut), 6 actor notes (the four coop animals on their shelves, two
  guards near walls). Its nine "unreachable" entries: four regions holding actors (next section) and 5 small ledges (the
  smithy's raised forge, the kitchen's counters).
- Floor check: 111 598 LT² listed; most of it is door-sill sample rows (`5->17`, `14->20` are one row of samples across a
  whole floor polygon's area), the remainder sills.
- Swings: `review/v02_open` shows the doors, cells, lid and hatch open.

## Can the monsters reach the party

The audit reports four regions with 63 actors as cut off from the party start. Probes on the final map:
`reach/true_regions.py` (the audit's graph with walls tested as polygons) and `reach/make_probes.py`, `reach/run_probes.sh`
(hostile monster, `report_state` every 2 s; `reach/` holds them, logs stay local).

| Audit region | Actors | Border | Verdict |
| --- | --- | --- | --- |
| Sector 12 (28.2 M units²), sector 38 (14.7 M) | 7 + 16 | Door frames: `Level._add_wall` keeps a wall as a plan segment with the face's whole z range, so a doorway notched into one merged wall polygon (DDoor7's is a 14-gon) counts as solid | **False.** With polygon walls both join the start's region (196 635 cells, 36 actors). `gate_door_open3`: a monster runs through the opened DDoor7 pair from y -4202 to -3550 |
| Sector 17, `112453` (0.54 M, the hatchlings' room) | 6 | A lane 253 wide and 102-123 high between `InvisibleBrush1/2`, under the audit's 160 headroom limit. MM9's `AITrk362-365` run through it | **Real, fixed.** Rows 9081-9083 carry the spider stand-in's radius 109: the body did not fit (a spawned monster with that radius stays in the room or at the lane's mouth). `convert.py` now sets MM9's own body (nagate.abc 18 x 20 LT x Scale: 46 x 51, 69 x 77, 138 x 154). Placed hatchling 3: in the lane in 2 s with the party in sight (`h3_out_seen`), out through the lane to (1312, -3348) with the party out of sight (`h3_out_hidden`) |
| Sector 1, `407982` (32 M, the lower levels) | 34 | No floor joins them to the upper storeys; the only ways are ladders, and MM9's DAT has no stair either (no drop within 600 either way) | **Real and faithful.** `ladder5_top`: a monster stands at the foot of Ladder5 with the party at its top. Inside the region monsters hunt normally: `plain_seen` closes 1 000 units; `plain_hidden` follows 2 300 units out of sight and ends about 600 from the party, the far side of a wall or shut door |

Against that control: a shut door holds a monster on either side (`gate_door_shut`, `hall_door_shut`); the audit counts doors
as open. The four coop actors (`NO NODE`: shelves under its headroom limit) stand behind fixed gates, as in MM9.

The animals are not `immobile`: rows 9267-9273, 9293-9295, 9297, 9299 (Move Med, AI Wimp, Hst 0) wander. Idle runs
(`reach/probe_animals.yml`, `reach/probe_cow.yml`, 2 minutes each, party near them): Cat0 and Rooster1 walked 1 601 and
1 669 units and stayed in their coops (sectors 71, 72), Cow0 walked 5 246 and stayed in its pen (sector 63, x 460-923, y -442 to
-140). Actors far from the party do not idle: Cow0 stood still with the party 690 away.

The first cow run found a real hole: it walked out through the pen's west wall. That wall is 4 LT thick and the voxel pass
had dropped its pen-side face, so a one-sided face was left, facing the corridor, and nothing stopped a body from the pen.
`thin_walls: true` (below) keeps those faces: 76 more, among them the coops' partitions.

## Deviations from MM9 and why

- **lever17 toggles `Celldoor18`** like the other levers (a Trigger each pull): MM9's lever sends `unlock`+`use` on open
  (the open cell shuts) and `close`+`lock` on close, so MM9 keeps it shut on the way back; here the second pull reopens it.
- **No walking NPCs.** Native actors have no marker paths: the patrols stand, the cook does not run up to the party (he
  answers a click), Guard0/1 are placed at their markers, Antoni and Ivsar vanish (the smith does walk his round), the interrogator and prisoner are moved
  while the room's door is shut, and the barracks guards do not run to the Nagate.
- **Ivsar does not follow.** MM9 has him walk with the party; he goes ahead, as his dialogue allows.
- **Water volumes** (the shared water rule, 2026-11-06, rebuilt 21:08): the sink (`SinkWater0`, 54 deep), the
  quenching trough (`BlueWater0`, 15) and the forge's lava (`Lava0`, 8) are scene `water_volumes`, all decorative
  (wading; nothing swims). Their surfaces are non-solid: the party stands in the lava on the forge floor 18 under
  its top, as MM9's. Room mismatches 0, bed holes 0; all six scenarios and `scenario_swim_check.yml` pass.
- **Lava0 does no damage** (MM9: 10) and is opaque; the sink's water is the liquid shader (2026-10-31, `water115_mm9`,
  [shared helper](../mm9r_common/liquids.py), opaque; sheet `review/liquid/before_after_p1-2.jpg`); the
  quenching trough's `Ocean4` animates (19 frames) but is opaque (its texture has no alpha).
- **See-through water (2026-10-31)** ([shared helper](../mm9r_common/liquids.py): MM9 opacity = the surface's alpha x
  its sprite's mean alpha, see-through where a floor of its room lies under it; engine: `liquids.yml` `opacity`,
  devdocs/INDOOR_TRANSLUCENT_FACES.md)): the sink is see-through (`SinkWater0`: 0.7 x 0.42 = 0.29, `lqw115o29`); the
  quenching trough (Ocean4 brush, Alpha 1, no alpha in the texture) stays opaque. Sheet
  `review/liquid/see_through.jpg`.
- **Not built**: `ObjectLight` (38), `MarkerWater`'s steam, ambient sounds, door sounds per mover.
- **The party cannot enter the hatchlings' room** (192 high, the lane 123). Whether MM9's party fits was not checked; the room holds only the six
  hatchlings, which come out.
- Barrels and bone piles are decorations only (no drinks or searches), as in the other dungeons.

## Shared converter changes

- `rooms.separating_plane` with map setting `split_retry` (opt-in): when the widest gap's split fails the purity test it
  tries the next, so a floor under a row of three cells splits. Results are unchanged without it.
- `rooms.NearestRoom.front` with map setting `thin_walls` (opt-in): a wall thinner than a voxel has air one voxel away on both
  sides and the nearest-voxel tie can go to the air behind it, which dropped the face. The setting also looks straight ahead.
  Results are unchanged without it; other maps with thin walls may want it.

## Open items

- MM9 models for the Guard family (9111-9113), the Dwarven Guard (9120) and the prisoners and commoners (rows 358, 367):
  24 + 5 + 3 actors draw stand-ins. The animals are on their own MM9 rows (Cat 9294, Cow 9267, Rooster 9270).
- `check_walkability.py`: walls as polygons and a monster-sized headroom, so a notched doorway and a low lane stop reading as cuts.
- Two soft light patches on the wall at the well head (`c03_well_head`, also before the `DirLight`s): compare with the DAT's lightmaps.
- A density and pack pass (PLAN.md: later); x4 textures last.

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 15:14:32 (convert.py from the current shared converter, end 15:18:15): 1 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV now has 12843 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_chests.yml` pass, `scenario_doors_exits.yml` pass, `scenario_immobile.yml` pass, `scenario_quests.yml` pass, `scenario_scripted.yml` pass.

## Scripted ambient behaviour (2026-11-11)

The interrogation walks (above): the interrogator and each prisoner in turn along MarkerBeating0-9 with
`evt.MoveActorTo` (a walk not done in 25 s, or under way at a save, ends at its point), the warden's `aware` at the
levers. The smith's hammer and sword, the gate guards' sleep (above). Headless: the whole interrogation runs in about
330 s, all three prisoners back in their cells, `Beatings` 2. Desktop captures (`output/held_items_check/drangheimprison/`):
the smith hammers with the hammer in his right hand and carries the sword to the trough. Scenarios: chests, immobile,
quests, scripted, swim_check pass; `scenario_doors_exits.yml` fails at step 38 (the hatch drop, z 46 off) with this
map's scene and Lua from HEAD too, so not from this change; playthrough segment 13 passes.
Not done: the warden and doorman do not walk to the levers and doors (they play `aware` where they stand); the smith's
water stop puts him at the trough's rim (the path from before).
