# MM9 rework: Chasm of the Dead (`chasmofthedead.blv`)

MM9's Chasm of the Dead (off Drangheim, monsters L10-40) converted from its DAT world into a native indoor map (BLV:
sectors, portals, linear and rotating movers, a ladder, lights, exit volume) on the shared dungeon converter
([`../mm9r_common/dungeon`](../mm9r_common/DUNGEON_PLAYBOOK.md)). Built into the isolated review root
`output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's decoration rows and the prop models
([props project](../../props/mm9_chasmofthedead_claude/README.md)). Status 2026-10-30: geometry, rooms, doors, every trap,
lights, exit, 314 decorations, 16 chests, 171 monsters, the scripted objects as native events, baked lighting. All 171
monsters draw as untextured placeholders until the humanoid batch (Skeleton, Skeleton Warrior, Skeleton Master, Zombie,
Mummy, Imp art is not done).

## Build and review

```sh
python3 level_generation/projects/mm9r_chasmofthedead/analyse.py           # DAT survey: work/analysis.json, dat_objects.json
python3 level_generation/projects/mm9r_chasmofthedead/dat_lightmaps.py     # MM9's lightmap colours per zone (hue reference)
python3 level_generation/projects/mm9r_chasmofthedead/convert.py --plan    # rooms only (3 min)
python3 level_generation/projects/mm9r_chasmofthedead/convert.py           # build, compile, install (5 min)
python3 level_generation/projects/mm9r_common/dungeon/lighting.py level_generation/projects/mm9r_chasmofthedead   # bake
python3 level_generation/projects/mm9r_chasmofthedead/make_scenarios.py
for s in doors_exits pivot scripted chests; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_chasmofthedead/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_chasmofthedead
python3 level_generation/projects/mm9r_chasmofthedead/make_tour.py v04 [--original]       # 56 eye-level views
./tools/run_game.sh --isolated chasm --world mm9 --map chasmofthedead.blv --assets "$PWD/output/mm9_rework/assets_dev" \
    --position -13189 27904 1578 --yaw-radians -1.5708 --pitch-degrees 0 --warmup 3 --seconds 170 \
    --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_chasmofthedead/review_tour_v04.yml
./tools/run_game.sh --isolated chasmo --world mm9 --map chasmofthedead.odm --assets "$PWD/output/mm9_rework/assets_original" \
    ... --set debug.screenshot_tour_path=.../review_tour_v02_original.yml --set video.view_distance=unlimited
cd level_generation/projects/mm9r_common && python3 -m dungeon.sheet ../mm9r_chasmofthedead/review/v04 ../mm9r_chasmofthedead/review/v02_original
```

`--set video.view_distance=unlimited` matters on the original tour: the outdoor renderer otherwise fades distant
geometry into the sky, which is not MM9 (this map has no fog).

Review: [`review/v04_compare.jpg`](review/v04_compare.jpg) (56 views, MM9's bmodel_world map left, native BLV right),
lighting [`review/lighting_compare.jpg`](review/lighting_compare.jpg) (MM9 | unbaked | baked).

## Files

- `overrides.yml`: every DAT world model's rule, 29 archway cuts, 2 rectangle portals, the ladder, seeds, texture
  substitutes; `convert.py`: the population, liquids, detail faces and every trap and script (a `dungeon.Hooks` subclass);
  `analyse.py`, `dat_lightmaps.py`, `make_scenarios.py`, `make_tour.py`, `scenario_*.yml`, `review_tour_*.yml`, `review/`.
- `props.json`: 313 placements from the props project; `work/`: `build_report.json`, `doors.json`, `lights.json`,
  `content.json`, `population.json`, `walkability.json`, `rooms_<level>.png`, `runtime/`.

## Numbers

| | |
| --- | --- |
| Frame | `native = (LT.x, LT.z, LT.y) x 2.56`, no offset (the old map's frame: x -17162..11633, y -19333..28672, z -6021..2028 fit int16) |
| Geometry | 9 097 source polygons (PhysicsBSP + static models) -> 8 885 merged -> **11 971 native faces**, 18 857 vertices; 284 faces with no air in front dropped |
| Air | sealed (`leaked_to_border` 0), 2 seeded components: the map and the sealed treasure alcove |
| Rooms | **62 + sector 0**; median 117 faces, largest 948 (the canyon's south end with the bridge); before the 29 cuts the canyon alone was 2 225 |
| Portals | **65 faces**: 20 UserPortals, 13 from door leaves, 30 archway openings (five full-height canyon sections), 2 trap rectangles; every portal joins two rooms |
| Movers | **93**: 33 tomb doors (MM9 Door, a click), 18 plates, 14 spike rows, 4 closing wall panels, 2 crushers, the grate, the treasure panel and button; **18 rotating**: 12 shutter flaps, 2 pendulums + their invisible shells, the pivot cross, the hatch |
| Lights | 93 `Light` -> **89 BLV lights**; the 4 over the four-per-point cap (three of the pool hall's torches and `Light33`) light the bake only; at most 4 per floor point |
| Decorations | **314**: 213 props, 82 fires, 16 chests, the 2 quest objects, Spikes2 |
| Actors | **171**, all of MM9's: Skeleton Warrior 48, Skeleton Master 42, Embalmed Mummy 20, Petrified Mummy 19, Skeleton 14, Zombie 11, Dripper 10, Imp Elder 7. 39 dormant, 21 hidden. 13 Apparitions spawn on top |
| Outlines | under the 7 000 limit only with 457 detail faces compiled invisible (`detail_faces`) |
| Exit | `ExitTrigger0` (object 1114) to Drangheim; arrival facing south (270) |

## What each DAT object became

| MM9 | Native |
| --- | --- |
| `PhysicsBSP` | static world; `VisBSP` only for its 20 UserPortals |
| `Door1-6`, `8-12`, `14-35` | tomb doors, MM9's linear motion and speed, a click each. MM9's auto-close after 5 s is not carried (linear doors toggle) |
| `ShooterPlate1-10`, `HSP1/2/6/7`, `CWPlate1`, `SpikeRowPlate1`, `CeilingCrushPlate3/4` | MM9 Door motion (4 LT down), pressure events |
| `SDU/SDL1-4,6,7` (`RotatingDoor`) | **rotating** flaps at MM9's angle and speed |
| `Pendulum1/2` (`RotatingDoor`) | **rotating**, 210 degrees at 100, sine, ignoring bodies (MM9 Solid 0); object yaw applied to points and axis |
| `PivotWallTrap1`, `TrapExitDoor1` | **rotating** cross (`bodies: push`, `carry`) and hatch |
| `Ladder4`, `LadderBlocker3` | a real ladder out of the pit; invisible collision |
| `CWR/L1`, `CWR/L2` | MM9 Door 80 LT at 300 |
| `CeilingCrush3/4` (`Lift`) | MM9 motion, 160 LT at 500, back at 100 |
| `SpikeRow1-14` | MM9 motion, untouchable (Solid 0) |
| `Gratetrap0`, `Door0` | one mover, 120 LT aside at 250; the grill is `Grill3` |
| `PivotTreasurePanel1`, `PivotButton1` | MM9 Door, click events |
| `WorldObject*` chains, `Terrain0-8` sand heaps, `InvisibleBrush*` | static; invisible collision |
| `H2OSurface`, `BlueWater1`, `Acid0` | the top face as an untouchable translucent face at MM9's `SurfaceAlpha` 0.7 (Water115 and slime, first frame) |
| `Light`, `StaticSunLight0`, sky | BLV lights; the sky face as the engine's projected indoor sky and bake emitter |
| `Prop`, `CandleProp`, `TreasureChest` | 3D decorations; every `CandleProp` is `Blue 1`: blue flames |
| `Spikes2` (`PropDamager`) | `mm9_spikepit` on the pit floor, 20 a second |
| `Spikes3-8` | not built (they ride moving walls and crushers; deviations) |
| `AITrk`, `AIRail`, `AIBarrier`, `Marker`, `AmbientSound`, `Dripper`-class script holders, `HidingPlace` | not built; `AmbientSound` (18) is a later pass |
| `PerceptionBrush0-17` | not built (open items) |

## Scripted objects (`worlds/mm9/events/maps/chasmofthedead.lua`, written by `convert.py`)

| MM9 | Native |
| --- | --- |
| **Shooter plates**: `ShooterPlate1-10`, `TriggerPlate*`, `SPTrigger*`, `Shooter1-3`, `CeilingShooter1-3` (DAT wiring) | the plate sinks, its Shooter fires one FireBolt (DamageAmt 20), the plate rises after 1 s |
| **Hidden shooters**: `HSP1/2/6/7`, `SDU/SDL`, `HS1-4,6,7` | the plate sinks, the shutters swing open, a bolt comes out of each, they shut after 1 s |
| **Closing walls**: `TriggerCWPlate1`, `CWPlate1`, `CWR/L1-2`, `Spikes3/4/7/8` | the plate sinks, both pairs slam in, a party between takes 20; 3 s later they draw back |
| **Spike wave**: `SpikeRowTrigger1`, `SpikeRowPlate1`, `SpikeRow1-14` | a wave runs the stair's length (0.16 s a row, MM9's 96 LT at 600), each row hits a party under it for 10, the plate resets |
| **Ceiling crushers**: `CeilingCrushTrigger3/4` and plates, `CeilingCrush3/4`, `Spikes5/6` | the plate sinks, the ceiling drops, a party under it takes 20, it rises after 3 s |
| **Pendulums**: `PendulumTrigger1/2`, `Pendulum1/2` | a touch swings both blades through; a party in the band takes 30; the next touch swings them back (Sticky) |
| **Acid grate**: `GratetrapTrigger0`, `Gratetrap0`, `Acid0` | the grate slides away, the party falls into the acid, 10 a second; no swimming yet, so every third second lifts it to the rim; the grate shuts after 5 s |
| **Pivot trap**: `PivotWallTrapTrigger1`, `PivotWallTrap1`, `PivotButton1`, `PivotTreasurePanel1`, `Spikes2`, `Ladder4`, `TrapExitDoor1` | the floor half tips the party into the spike pit (20 a second); the cross turns back after 5 s; the ladder climbs to the hatch, opened by a click; the panel shows TreasureChest1 |
| **Mummies**: `MummyAwaken.scr` on 39 mummies, `Trigger0/1/7`, `CKTrigger` | dormant in their coffins until an awaken message or a hit; each then wakes the next, at once or at its death (p0, p1 from ScriptParams) |
| **Buried zombies**: `AutoResurrect.Scr` on 21, `Trigger2-6` (`Trigger6` armed by `Trigger5`, StartOn 0) | hidden until their volume's RESURRECT; five groups |
| **Apparitions**: `Chasm_GhostSpawner.scr`, `ghost.scr`, `Apparition0-12` markers, `Apparition13-25` volumes | each touched volume spawns an Apparition (9139) at the next marker; thirteen in all |
| **Lich Instructions**: `LichInstructions.scr` | a world item (`dungeon/pickups.py`, item 447), hidden with key 296; picked up, it gives key 296 (the Lich Lab's key) |
| **Crona Kiga**: `CronaKiga.scr` | a world item (item 390), hidden with key 48 or 169; its pickup awakens `PetrifiedMummy16` (the crypt's chain of 14), gives 10 000 experience and key 48 (Ludwig's quest, key 46) or 169 |
| **Dais shooter**: `Shooter0`, `OffRailTrigger.scr` | PurpleThingy (35) once, when the party first leaves MM9's AI rails; the rails' one gap is the dais under it: a one-shot pad |

All of MM9's Trigger volumes are boxes polled four times a second, except the plates, whose surfaces are pressure faces.
Map variables keep the state; one-shot timers are armed by a variable (playbook).

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

**Installed: lightmap-matched (re-lit 2026-10-31, the user's decision of 2026-10-30: dungeon lighting follows MM9's DAT
lightmaps for brightness and hue; MM9 draws walls as texture x lightmap x1, `devdocs/mm9_rework/MM9_RENDER_LIGHTING_RE.md`).**
`../mm9r_common/dungeon/lighting.py` with `tools/lighting/baked_indoors/profiles/mm9_chasmofthedead.yml`: the 89 BLV
lights and the 4 over the four-per-point cap, 64 samples, 3 bounces, **`direct_scale` 0.41, `bounce_scale` 6,
`ambient_scale` 0.46, `sky_scale` 0.12, `max_lighting` 1**; the 6 sky faces (`sky04`) stay area lights drawn at 1.1.
Sector minimum light 20 (unchanged). One 12.9 M-texel page, passes in `output/mm9_rework/bakes/chasmofthedead`; the
re-light was a `--recompose` through `../mm9r_common/bake_slot.sh` (no Cycles run). `tools/lighting/stale_bakes.py
--assets output/mm9_rework/assets_dev --check` does not list the map. Bake again after any `convert.py` that changes the
BLV.

**Method.** `../mm9r_common/relight_fit.py --grid --max 1` (the saved passes composed per zone and room without Blender,
fitted to the zones' mean, B/R, G/R and MM9's map-wide texel quantiles 0.16 / 0.19 / 0.35). Zones: `dat_lightmaps.py`
(ten named boxes). MM9's tombs sit on a neutral floor of 41/255 (AmbientLight 40) with blue pools round each lamp; the
fit's ambient 0.46 x the sector floor 0.345 is that 0.16. Per room (`work/relight/fit_after.txt`) every room lies within
x0.79-1.22 of MM9.

Lightmap texel luminance ours / MM9's DAT lightmaps per zone (`../mm9r_common/hue_vs_lightmaps.py`,
`work/relight/hue_before.txt`, `hue_after.txt`):

| Zone | MM9 luma | before | after | ratio before -> after | B/R MM9 / after | G/R MM9 / after |
| --- | --- | --- | --- | --- | --- | --- |
| entry_tomb | 0.186 | 0.886 | 0.185 | 4.77 -> **1.00** | 1.39 / 1.33 | 1.17 / 1.19 |
| pillar_hall | 0.211 | 0.920 | 0.201 | 4.37 -> **0.95** | 1.77 / 1.52 | 1.35 / 1.31 |
| hall2 | 0.166 | 0.892 | 0.188 | 5.37 -> **1.13** | 1.08 / 1.36 | 1.04 / 1.22 |
| canyon_floor | 0.281 | 1.243 | 0.310 | 4.42 -> **1.10** | 1.00 / 0.97 | 1.00 / 0.96 |
| canyon_rim | 0.398 | 1.164 | 0.599 | 2.93 -> **1.50** | 1.00 / 1.13 | 1.00 / 1.05 |
| pool_hall | 0.219 | 0.924 | 0.203 | 4.23 -> **0.93** | 1.81 / 1.55 | 1.36 / 1.33 |
| octagon | 0.206 | 0.897 | 0.190 | 4.35 -> **0.92** | 1.66 / 1.40 | 1.31 / 1.23 |
| mummy_hall | 0.188 | 0.878 | 0.182 | 4.67 -> **0.96** | 1.43 / 1.28 | 1.19 / 1.17 |
| south_corridor | 0.195 | 0.927 | 0.204 | 4.75 -> **1.05** | 1.52 / 1.54 | 1.24 / 1.34 |
| crypt | 0.218 | 0.943 | 0.211 | 4.33 -> **0.97** | 1.86 / 1.64 | 1.40 / 1.39 |

The canyon rim's 1.50 is the sky faces themselves (drawn at 1.1, inside the box); its walls predict x0.78 without them.
Hue: the tombs keep MM9's blue (B/R 1.28-1.64 against 1.39-1.87, a little less blue than MM9; before 1.12-1.27), the
canyon neutral; hall2 is a little bluer than MM9 (1.36 against 1.08).

**Screen brightness** (the 56 v04 views, `work/relight/views.txt`, centre crop luma): capture 101.4 (information only:
the old import drawn nearly unlit), unbaked 52.2, old bake 98.7, **lightmap bake 24.9 (x0.25)**. Darkest baked views: the
two tunnels between the tombs and the canyon (m09 15.3, m10 15.5), the entrance stair, the acid grate and the diagonal arm
17.6; the canyon 19-38 on its floor and ledges, 73 looking at the sky. No view is under luma 12, so no player-light floor
was added; the tunnels read nearly black by eye, and a per-room floor (`mm9r_darkpassageway` `ROOM_LEVELS`) is the next
step if they should read lighter. No real MM9 screenshot of this map exists.

**Props: `model_lighting: true`** (`overrides.yml`; the scene's block: AmbientLight 40, ModelAdd 30). Same bake both
ways (`../mm9r_common/relight_props.py`, `work/relight/model_lighting_props.txt`): relative brightness of the props to
their view, capture 1.17, old path 1.58, **model lighting 1.43**; views with props under x0.6 of their view: **old 8,
model 0** (under this dark bake the old path's frame-ambient subtraction draws the dais, the chest chamber's sarcophagus,
the tomb hall's urns and the gallery's props black: luma 0-11). The 4 capped lights do not reach the models. The rebuild
left the BLV byte-identical (the scene gained the block); the four scenarios (chests, doors_exits, pivot, scripted) pass.

Sheets (looked at): `review/lighting_v05_compare.jpg`, `review/lighting_v05_p01-p10.jpg` (capture | unbaked | old bake |
lightmap bake with model lighting); `review/lighting_v05_baked` holds the same bake with the old prop path. The tombs are
dark with blue pools round their lamps, the white sarcophagi and urns no longer glow, the canyon is dim under a lit sky.

**Documented alternative: the capture-matched bake** (installed until 2026-10-31): `work/profile_capture_matched.yml`
(direct 0.9, bounce 6, ambient 2.4, sky 0.7, no ceiling): lightmap ratios 2.9-5.4, screen mean 98.7 against the
capture's 101.4. To switch back: copy it over the profile, `model_lighting: false` in `overrides.yml`, `convert.py`, then
`--recompose` as above and the scenarios.

### History: capture-matched calibration (2026-10-30)

`../mm9r_common/dungeon/lighting.py` bakes `chasmofthedead.lighting` / `.bake.json` from the 89 BLV lights and the 4 lights
over the four-per-point cap (profile `tools/lighting/baked_indoors/profiles/mm9_chasmofthedead.yml`: 64 samples, 3 bounces,
direct 0.9, bounce 6, ambient 2.4, sky 0.7; passes in `output/mm9_rework/bakes/chasmofthedead`, installed through
`review_root`). One 12.9 M-texel page, 9 788 charts for 11 638 of 11 971 faces (1 616 mover faces), a 20.6 MB file,
about 16 minutes of Cycles. The 6 sky faces are area lights (`sky04`, colour 0.85 / 0.92 / 1.0, display 1.1): they had
to stay ordinary faces, since `bake_indoor.py` takes `IndoorSky` faces out of emitters and casters.

Mean brightness of the 56 views (centre crop, `python3 -m dungeon.sheet --brightness`, the original captured with
`video.view_distance=unlimited`): **MM9 97.2, native unbaked 51.8, native baked 95.5**. Mean RGB: MM9 104 / 101 / 87, baked
95 / 100 / 91. The old map draws MM9's light colours neutral, so hue is calibrated on the DAT's own lightmaps
(`dat_lightmaps.py`): a neutral floor of 41 in every tomb with a moderate blue lift (pillar hall 41 / 54 / 69, pool hall
42 / 56 / 74, crypt 41 / 56 / 72, the plainest halls 41 / 45 / 49) and a neutral canyon (64 on the floor, 100 at the rim).
The native map has the same structure: neutral floors with blue pools round each lamp, a neutral canyon.

Per view: the torch-less corridors match within 10-15 (t01 86/85/75 against 103/101/88; m10 80/76/65 against 95/91/78;
s07 90/99/88 against 104/102/86); the canyon floor stays above MM9's capture (c05 130/108/91 against 99/88/80, c10
122/115/119 against 66/60/58), since MM9's original shows a navy void where this map has a lit sky: `sky_scale` 0.7 is as low
as keeps the canyon brighter than its tombs, as the lightmaps have it. Bright props read hot in the lit rooms (the white
sarcophagi, urns, statues): a decoration's ambient is the sector's actor ambient, which `ambient_scale` raises with the
walls; there is no separate control. The sand heaps read green under blue lamps (yellow DIRT2 x blue), which the DAT's
colours also give. Sheets: `review/lighting_compare.jpg`, `review/v04_compare.jpg`. Rebake after any `convert.py` that
changes the BLV (the game ignores a stale bake), including a rebuild with a newer compiler.

## Checks

- `scenario_doors_exits.yml` passes: the exit raises `mm9_exit_trigger:1114`; Door15 and Door35 stop the party shut, open on
  their events, the party walks through; the long stair is walked upward (risers 41).
- `scenario_chests.yml` passes: the 16 chests open (15 by interact from in front of their models, TreasureChest1 by its
  event, behind the panel).
- `scenario_pivot.yml` passes: stepping on the floor half swings the cross open and drops the party into the pit, the cross
  turns back, the hatch opens on its click, the party climbs Ladder4 out, the hatch shuts itself.
- `scenario_scripted.yml` passes (78 steps): shooter plate and its reset, HSP1 with shutters and two bolts, closing walls,
  spike wave, crusher, pendulums (rotating, a hit), the grate, Trigger7's four mummies, the Crona Kiga's chain of 14 (18
  awake), Trigger2, Trigger6 staying off until Trigger5, an Apparition, the Lich Instructions given once.
- Party reach: a voxel flood from the start (step one voxel, 66 LT head room, plates filled in) reaches every monster,
  chest and door, down the ledges to the canyon floor and every deep room, except the sealed alcove (deviations).
- Walkability (`work/walkability.json`): 283 steps, 1 flight, 21 mover notes, 43 actor notes, 2 pits: sand heaps and
  altar sides (8 wide), altar tops 82 above their floor (out of reach as in MM9), plates and spike rows, mummies in
  their coffins beside walls.
- The audit's "154 monsters cannot walk to the party start" is a false positive of its 16-unit floor grid, not stairs: the
  spike stair's floor is 82-wide slabs with 13 slots 20 wide and 82 deep across the whole corridor (MM9's slots for
  `SpikeRow1-14`), and a grid cell falls into each. With the slots lidded in a scratch copy of the audit's graph, all 171
  actors reach the start at step 40. Real monsters are not affected: headless runs (`work/stairs/`) walk a Skeleton and a
  Mummy over every slot at floor height, in sight and out of sight, both ways, as on the no-slot control; the party
  crosses too. The 41 edges (16 of them) are the sunken tiers of the entry tomb and crypt and pillar bases in sector 50, off
  every route, with no actor on them; a Skeleton climbs them to reach the party (-5530 to -5448, 1167 to 1208).
- Floor check: 24 669 LT² of floor under another room's air: 16 LT strips along the five canyon sections and door sills.
- Mixed faces: 148 with a minority over 20 %: walls running below stair floors, whose buried samples see the next room.
  Every review view inspected: no holes.
- Desktop: the acid lift puts the party on the corridor floor beside the grate; a pendulum swings out of its ceiling
  slot down the corridor's length (sign and plane as MM9's trigger strips and slot imply); no Lua errors, bake current.
- Load: 171 actors. Compiler unit tests not run: no compiler change here.

## Deviations from MM9 and why

- **The treasure alcove.** MM9's cross is a revolving wall: its quarter turn carries the pit's west half to the alcove and
  the alcove to the corridor, but its trigger stands on the corridor half and the springing button inside the alcove, so
  no MM9 route reaches TreasureChest1. Here the pit's west half (MM9's `Hide0`) springs the trap and carries the party
  up (`evt.MoveToMap` at the quarter turn), and the button carries it back out.
- **Acid** (the shared water rule, 2026-11-06): `Acid0` is a scene water volume (CorrosiveFluid's tint), the channel
  (`BlueWater0`, under H2OSurface) and the pool (`BlueWater1`) too (20 and 41 deep: wading); the party falling
  through the grate swims in the 573-deep pit, takes 10 a second, and every third second is still lifted to the rim
  (`AcidLifts`): the rim is 102 over the surface, beyond the surface jump (59). Room mismatches 0, bed holes 0.
- **Spikes on moving parts** (`Spikes3-8`): decorations do not move; `SpikePit` has 896 triangles, too many as mover
  faces. The walls and crushers strike by script without them.
- **Tomb doors** do not close themselves after 5 s; monsters do not open them (MM9 `AITriggerable`).
- **Closing walls, crushers, spike rows** hurt once per strike or row, not per second of contact.
- **Sky**: MM9 draws a SnowMtns sky box; the native canyon has the engine's projected sky (`sky04`), which scrolls.
- **Water and acid** draw with the liquid shader (2026-10-31, [shared helper](../mm9r_common/liquids.py)): the channel and pool
  (Water115, `water115_mm9`) and the acid pit (slime, `slime_mm9`), opaque instead of MM9's 0.7 alpha; `depth: shallow`.
  Sheets: `review/liquid/before_after_p1-2.jpg`.
- **See-through water (2026-10-31)** ([shared helper](../mm9r_common/liquids.py): MM9 opacity = the surface's alpha x
  its sprite's mean alpha, see-through where a floor of its room lies under it; engine: `liquids.yml` `opacity`,
  devdocs/INDOOR_TRANSLUCENT_FACES.md)): all three are see-through: `H2OSurface` (Alpha 1 x water115_0000 0.42,
  `lqw115o42`), `BlueWater1` (0.7 x 0.42 = 0.29, `lqw115o29`) and the acid (`Acid0`, 0.7 x slime.spr (no alpha) = 0.7,
  `lqslmo70`). Sheets `review/liquid/see_through_p*.jpg` (opaque | see-through).
- **Mummies** stand dormant, not in MM9's `coffin` idle; **zombies** appear instead of rising (no resurrect clip yet).
- **`Dripper35`**: `Trigger4` names `Dripper33` twice, a slip that buries Dripper35 for ever; here it rises with them.
- **`CronaKiga.scr`** tests the wrong variable at start; here taken keys hide it, as its comments intend.
- **Minimap**: 457 faces of column bevels and trim draw no map lines (the 7 000 outline limit).
- `TreasureShooterTrigger1` (each chest's `TriggerTarget`) names no object: nothing fires, as in MM9.

## Open items

- MM9 art for all eight monster families (humanoid batch).
- `PerceptionBrush0-17` (the glowing trap marks a party with Perception 8 sees): 18 brushes, `Perception.spr` at Alpha 0.3-0.75;
  they need a per-face visibility switch on translucent faces.
- 18 `AmbientSound`s (spooky interior, canyon wind, falling sand).
- MM6-MM8 density (PLAN.md: later). No x4 textures (the project's last step).

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 15:04:57 (convert.py from the current shared converter, end 15:10:11): 20 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV now has 11951 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_chests.yml` pass, `scenario_doors_exits.yml` pass, `scenario_pivot.yml` pass, `scenario_scripted.yml` pass.
Blocker probes: 3 walks into helper brushes resting on the floor stop short of them, 3 identical before and after (their sides still block).
