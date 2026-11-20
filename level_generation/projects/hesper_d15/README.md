# D15: The Undercroft — `hes_d15.blv`, map 9136

Built from [D15 BUILD-READY](../../../design/kreegan_world/zone4/dungeons/D15_UNDERCROFT.md#21-build-ready),
`plans_zone4.py:d15`, D1/D2's shared indoor kit, D9's sector splitting and D0's linear mechanisms.
Installs only through the Hesper stage. This builder did not edit or rebuild the Undervault project.

## Walkability and room shapes — 2026-10-24

The west freight-line bed and both platform beds are now 24 below their walkways. The platform gate and
Maintenance threshold can be crossed directly, and neither tram-side pocket traps monsters. Pressure plates
follow their floor patches. Cabin floors stay at −64, with the existing two 32-unit boarding steps.
The Service, Cut and Junction stairs have 32 risers of 16 beneath sloped ceilings, with flat landings.

The chamfered, hipped Junction is the signature hall. Twelve room footprints have clipped outer corners;
nine base rooms have hipped roofs, and the Maintenance passage widens through 45-degree wall bends while
preserving its doorway positions. The native survey counts 21/38 non-orthogonal room parts, 89% axis-aligned
wall area and 18 sloped ceilings (before: 0/38, 95%, 0). The three 256-high Junction ramparts have 512-wide railed
ramps: a 1,024 run on the west, 768 on the north/south (14°/18°), with no floor underneath.
The author checks controls, fixtures and pickups against the new corners. Placement keeps actors clear of
corners, ramps and the Sentinel platform edge; actors 58–64 move, preserving all 72 IDs, indices and groups.
All 20 pickup positions/events, 14 door IDs, six chests and arrival records are unchanged.

The build has 7,500 faces, 38 occupied sectors (130–290 non-portal faces each), 43 portal apertures,
35 planned lights, 97 decorations and zero compiler warnings. The audit has 15 documented exceptions:
six passenger seats, six inactive drone cradles, two broken ceramic panels and the east line, which is reached
by the scripted tram ride across the collapsed tunnel. No new stand-ins or shared kit changes.
`d15_walkability.yml` contains 14 pursuit fights; `review_tour_walkability.yml` covers the fixes and rooms for
the integrator's capture. The staged audit has zero live findings; all four scenarios pass (109 main-route,
72 side-route, 42 pickup and 221 pursuit steps). D15 is in the shared walkability gate and scenario queue.
The current evidence is in `review/walkability/`; these results supersede the historical counts below.

Final shared regression: `rebuild_all.sh --scenarios-only` passes **103/103** (exit 0). Actor-size and
decoration-ID audits have zero mismatches; the design audit has zero findings. Logs:
`output/hesper_stage/logs/scenarios_141329_8/`; batch summary:
`output/hesper_stage/logs/walkability_batch_c_20261024/validation_summary.json`.

## Status — 2026-10-23

Built and staged: 20 rooms, three levels, 38 occupied sectors plus empty sector 0, 6,854 faces,
43 two-sided portal apertures, 14 movers, 72 actors, six chests, two supply shelves, 20 clickable supply satchels/bundles and
32 lights (25 fixtures and seven explicit lights). Compilation has zero warnings; sectors have 122–252
non-portal faces. All required texture masters exist; no texture stand-ins are used.

The breaker restores the platform lamps, route board, cabinet and first tram door. Three tram trips, both stair
flights to the cut, harmless water, the Grandmaster lock's 30-second timer across save/load, the revealed Lancer
wave, the Engram Core, the D12 lift round trip and the Undervault return are covered by `d15_main_path.yml`.
`d15_side_paths.yml` covers side-room doors and chests, Master versus Grandmaster access, both caches,
water in both directions without injury, the inside release and a return tram trip with west power still off.
The geometry/mechanism checks use a level-1000 test party and disable actors during geometry traversals; they do not establish
combat balance. The main test defeats the revealed Lancers through `damage_actor` before looting the locker. A separate fresh
Grandmaster party checks the Undervault entrance and immediate return after the long dungeon route.

The integrator's original `review/build01/sheet.jpg` was inspected for this revision and is preserved.
New screenshots, `review/build02/sheet.jpg`, Wizard Eye/automap review and visual sign-off are **deferred to the
integrator at the user's request**. The revised tours and sheet assembler are ready.

## Review fixes — 2026-10-23

Applied the shared second-round findings and the integrator's D15 answer in P3:

- Sector ambient is now 27 at the arrival/stair/lock/lift, 28 in the Breach/Burrow/Junction, and 29 elsewhere
  (higher means darker). Native MM8 sector bytes are checked against the source values. All 32 light positions
  and groups remain; D15-only fixture aliases increase lamp/vent radii by 50%, and the explicit lamp, board, cabin
  and lock glows use the same increase. The black-water reflection remains at radius 900. The maximum floor-point
  overlap is three, below the limit of four. Tram 1's powered cabin changes from cool white to amber (255/190/105).
  Other maps' fixtures retain their original radii and colours.
- The Breach and Junction have 128-high K3 lower bands, 96-high crown bands, ten resin buttresses, two broken
  ceramic panels beside the breach mouth, and raised rims on the three existing rampart runs. The buttresses follow
  room edges and avoid every wall opening by at least 64 units; actor placement avoids their solid bounds.
  The Signal Room door remains reachable, as checked by the side-path scenario.
- Window textures are confined to the tram/wreck bodies: sides have one vertical window row, ends are fitted once,
  seats and passenger doors use plain ceramic. Native UV spans and carriage bounds are verified. The old line
  camera faced a nearby wreck end; the revised camera looks along the north walkway. The east-platform camera
  now faces along the platform instead of into its west wall.
- The three dark shots use `dark_` prefixes and the six powered shots use `power_`. Both tours write under
  `review/build02/`; the assembler reads the exact nine filenames from the tours, so the original captures remain
  intact and duplicate sequence numbers cannot lose one lighting state.

The accepted furnishing positions, plan-mark decisions, maintenance reveal, stair clearance, open east tram,
non-colliding water and H3 fallback remain. No further workaround was added for queued engine needs. Light
contrast and composition still require the integrator's native visual review; source checks are not visual approval.
Revision logs and refreshed capture saves are under `review/fixes/`.

Validation: `d15_main_path.yml` **108/108** and `d15_side_paths.yml` **72/72**, including both external round trips.
Compilation reports zero warnings; native/static verification passes and the design audit has zero findings.
The complete `rebuild_all.sh --scenarios-only` run records **67 PASS / 4 FAIL** across all 71 scenarios. D15 passes
in that run. `crown_entrances` step 44 and `d12_round_trips` step 11 fail at the Crown's Spire Gate pose, which picks
the distant D16 door instead. `crown_edges` and `scour_edges` each fail their step-22 return-boundary assertion,
but both pass all 24 steps on immediate isolated, locked reruns without changes. The global suite is not green;
these other-map failures remain for the integrator. Logs: `review/fixes/regression.log`, the two `*_recheck.log`
files, and `output/hesper_stage/logs/scenarios_153154_3/`.

One staging attempt encountered the Scour's temporarily absent `source/hes_out2.terrain.yml` while its builder
was working. The source returned and the full restage passed; the failed attempt is preserved in
`review/fixes/stage_dependency_failure.log`. The Undervault project, Git index and existing assets_dev diff match
the pre-task snapshots. No engine code/build, Vulkan, performance run or git staging was used.

## Build and test

From the repository root, using the existing compiler and game:

```sh
# On a fresh stage, register the D15-only fixture aliases before authoring their decoration ids.
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py
flock -s output/hesper_stage/locks/stage.lock \
  blender --background --factory-startup --python level_generation/projects/hesper_d15/author_d15_blender.py
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
  python3 level_generation/projects/hesper_d15/build_d15.py
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py
flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_d15/verify_d15.py
```

On this sandbox the snap launcher fails and headless Blender hangs during audio teardown. The successful equivalent
was `/snap/blender/current/blender --background --factory-startup --python <author> --python-expr
'import sys,os;sys.stdout.flush();sys.stderr.flush();os._exit(0)'`, with `XDG_CACHE_HOME` under `/tmp`.
Check its log for errors and the GLB/Blend export before compiling; the forced exit is a host workaround.

```sh
flock -s output/hesper_stage/locks/engine_build.lock \
  flock -s output/hesper_stage/locks/stage.lock env OPENYAMM_START_MINIMIZED=1 bash -c '
  cd output/hesper_stage/scenario_run &&
  ../../../build/game/openyamm --world hesper --headless-run-scenario \
    ../../../level_generation/projects/hesper_d15/d15_main_path.yml --scenario-no-color'
```

Run `d15_side_paths.yml` the same way. Both scenarios and `d15` are registered in `hesper_stage/rebuild_all.sh`.
Regression command: `level_generation/projects/hesper_stage/rebuild_all.sh --scenarios-only`.
**Never run the full rebuild while parallel builders work:** it rewrites their maps, including the protected
Undervault. No engine build was needed.

`source/` contains the editable Blend, GLB, compiler metadata, arrivals and authored handlers.
`build_d15.py` calls `blv_build.build`, checks counts, places the encounter packs and loot, and creates
`runtime/worlds/hesper`. Edit the authored handlers, never generated runtime Lua. The source export keeps semantic
room order equal to the GLB's name order, so actor sector IDs agree with the compiled geometry.

## Original build validation record

- Final staged D15: `d15_main_path.yml` **108/108**, `d15_side_paths.yml` **72/72**.
  Both external round trips pass, with the return bound to the Undervault's existing `deep_stair_bulkhead` record.
- Compiler: zero warnings. `verify_d15.py`: source/native counts, actor sectors, fixtures, textures and staged
  payloads pass. Design audit: **zero findings**.
- The separately run shared-scenario snapshot contains 31 scenarios: 29 initially passed, D10's key pickup failed,
  and D5 had its known non-gating WIP failure. D10's builder corrected its handler; the focused rerun passes.
  After another builder rebuilt the Undervault, its old `bulkhead_open` expectation fails because event 17 now
  transitions to D15. See `review/shared_scenarios.log`, its snapshot, `d10_recheck.log` and
  `undervault_bulkhead_recheck.log`. This is not a claim that the continuously changing shared suite is all green.
- Full `rebuild_all.sh` was not run by this builder because it would rebuild the protected Undervault.
  The Git index and existing `assets_dev` diff match the pre-build snapshots.

## Integration

Both destinations come from their owning semantic records:

- Exit 50: `hesper_undervault/source/hes_undervault.semantic.json:arrivals.deep_stair_bulkhead`.
- Exit 51: `hesper_d12/source/hes_d12.semantic.json:arrivals.service_lift`. D12 became available during this build;
  its real exit and return are tested. A build without D12's compiled map reports the missing dependency instead
  of inventing a destination.

D15 exports `deep_stair`, `service_lift`, `tram_west` and `tram_east`. The staged Undervault's event 17 reaches D15;
the integrator subsequently corrected its old `bulkhead_open.yml` expectation. Both external D15 round trips pass.
This revision leaves the Undervault project untouched.

No QBits are written. Map variables 1, 3, 4 and 5 follow the document; 2 stays unused. Named variables preserve
first visit, whether the lock wave was revealed, and each cache's partial collection. Cache delivery uses
`evt.GivePartyMemberItem`: successful items are remembered individually, so full packs cannot consume or duplicate
the remaining supplies.

## Stand-ins and remaining work

| Required asset/feature | Current implementation |
|---|---|
| Tunnel lamps | Existing amber/off colony wall-light bodies; D15-only reviewed radius 960, RGB 255/165/70 |
| Graft lights and resin vents | Existing colony wall-light bodies; D15-only reviewed radius 768, original colours |
| Line lever | D4's idle/pulled greybox lever, swapped on power; no bespoke lever animation |
| Drudge Hulks / Crown Lancers | Existing Trooper C body; authoritative Hesper stats and Lancer post tactics |
| Crown Sentinels | Existing Ward turret body with Crown Sentinel stats and stationary placement |
| Reaver Drones | Actual Reaver C model, skin and shield-ring attachments |
| Random H3 lockers/pod | Existing shared-kit fallback: native T6 gear, 9,000 gold; locked shed locker 13,500. Hesper's weighted H3 pool is still pending |
| Dedicated rail rush, dripping and lock sounds | Not authored: no bound D15-specific sound assets. The normal same-map move sound stands in for the ride; the stage supplies Undercroft music |
| Slow water | Harmless wading geometry is verified; the current indoor movement path supplies no separate speed reduction |

The six creep pods reuse the existing model through `hes_creep_pod_static`, without extra dynamic lights beyond
the 32-light plan. There are no newly generated decoration meshes.

## Accepted authored decisions

The integrator accepted the original furnishing positions and the following adjustments on 2026-10-23:

- Two line wrecks: `(3300,200)`–`(5700,800)`, on its side, and `(4900,-60)`–`(7300,580)`, slewed 4°;
  a third siding carriage spans `(4100,1640)`–`(6500,2280)`. The north walk and maintenance approach remain clear.
  The maintenance threshold has four 32-unit steps out of the sunk track bed.
- Ten containers/crates line the maintenance and siding edges, four drone wrecks sit at room margins,
  six pods line the Breach, and twenty dead housings line the freight tunnel. Pumps, conduits, six charging
  cradles, tram seats and the three rampart runs are geometry; their coordinates are in the author script.
- The Maintenance Bay is **464 units** from the line in the plan, so its connecting reveal spans that gap.
  Other ordinary walls are 64 thick. The Junction Ramp's ceiling is raised from world Z 256 to 512 to retain
  512 clearance at its upper landing. Room footprints and the 38-sector budget are preserved.
- Tram interiors retain the exact plan footprints. Their exterior bodies extend 64 beyond the interior walls,
  with two 32-unit boarding steps. Tram 2 starts open so a party arriving from D12 can return before west power
  is restored. Both consoles follow the plan's **west-end** marks (section 7 says east end).
- The hidden Lancers follow the plan's **north-west** mark `(13000,12200)`; BUILD-READY calls it north-east.
  The two lift Sentinels follow `(14292,13400)`, which is in Root Lock, although the prose places them beyond it.
- Black water remains at −384 over the −512 track bed. Its surface is explicitly noncolliding and matched by
  `liquids.yml`; both traversal directions stay at foot Z −512, with no injury. There is no swimming transition.
- The route board is 256 wide to clear the shed approach. The wall opening under the jammed flood leaf retains
  384 clearance. Closed lock-room leaves are 384 high, travelling the specified 512 into the void.

## Native capture handoff

The tours use the refreshed unpowered and powered test-party saves made by the revised main scenario in
`review/fixes/`. Tour coordinates are
**foot positions** (the document's eye heights minus 160). Both launches remain minimized and hold shared locks.

```sh
flock -s output/hesper_stage/locks/engine_build.lock \
  flock -s output/hesper_stage/locks/stage.lock ./tools/run_game.sh --isolated d15_before \
  --world hesper --save "$PWD/level_generation/projects/hesper_d15/review/fixes/hes_d15_dark.oysav" \
  --assets "$PWD/output/hesper_stage/assets_editor_dev" \
  --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d15/review_tour_01.yml" --seconds 0
flock -s output/hesper_stage/locks/engine_build.lock \
  flock -s output/hesper_stage/locks/stage.lock ./tools/run_game.sh --isolated d15_after \
  --world hesper --save "$PWD/level_generation/projects/hesper_d15/review/fixes/hes_d15_power.oysav" \
  --assets "$PWD/output/hesper_stage/assets_editor_dev" \
  --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d15/review_tour_01_powered.yml" --seconds 0
python3 level_generation/projects/hesper_d15/make_contact_sheet.py
```

The assembler requires all nine real captures before it writes `review/build02/sheet.jpg`.

## Brightness B — 2026-10-23

Powered main rooms now use ambient 14 and stairs/transit rooms 16. The explicitly dark freight line and abandoned
siding use 20, six levels darker than the powered rooms. The existing group-1 breaker still switches Platform West
and Tram 1's lamps; it cannot change sector ambient. **An exact six-level ambient change in those same rooms between
power states remains unbuilt:** the event API has no sector-ambient setter, and this pass forbids engine changes.
The integrator must judge the existing lamp-driven contrast in the two captures.

The plan now owns D15's larger radii (960 tunnel lamps, 768 graft/vent lights). Three new wall lamps cover the siding
and both ramps. The two floating cabin light sources are now wall-mounted fixtures; Tram 1 uses the same warm amber
and off binding as Platform West. The freight line's two existing geometric lamps retain their explicit light sources.
Every room has a visible light source of radius at least 640. The 35-light plan (30 fixtures, five explicit lights)
passes ceiling checks and peaks at three overlaps on a 32-unit floor grid.

Authoring/building held the shared stage lock; the compiler reports zero warnings, the exclusive stage passes,
and native/staged-payload verification passes. Both scenarios pass: **108/108** main, **72/72** side paths.
Logs and fixture checks are in `review/brightness_b/`; the final shared regression is recorded in P3.
The retained nine-shot sheet's baseline is mean 40.5, darkest 25.0. No new capture was attempted; the integrator
captures both lighting states and re-measures. No new art stand-ins were required.

The saved-state check also exposed a stale breaker fixture reference: the handler used 10001 while the exported
lamps use 121. The handler now addresses 121; all three switched fixtures (two platform lamps and the cabin lamp)
share it. Native save records verify the dark/on names at that exact key. Both scenarios were rerun and pass, and
`review/fixes/hes_d15_{dark,power}.oysav` now contains the corrected states.


## Pickup placement — 2026-10-24

No stat containers, as PICKUPS.md specifies. 16 colony satchels and 4 scrap bundles in the breach/burrow. The
Maintenance Bay storeroom view shows satchels. All positions are authored in `author_d15_blender.py` and
exported under `pickups` in the semantic record. Stat containers occupy wall-side storage groups; satchels
avoid boss rooms and central routes.

The authored handlers call `HesperPickups.setup` with explicit treasure level **6 (H3)**. The shared automatic
map-name lookup failed at the first satchel click; the documented treasure override gives the correct dungeon
loot level. Stage installation supplies `hes_d15_pickups.lua` with every colour/empty model. No new art or
stand-ins were needed.

Removed 3 fixed floor-gold piles, as PICKUPS.md requires. Chest/event rewards and themed supply items remain.

`d15_pickups.yml` clicks every placed pickup; all stat containers reach the empty state.
`review_tour_pickups.yml` contains the storeroom and two satchel views for the integrator; captures were not
run in this sandbox.

Placement checks (counts, boss-room exclusion, floor support, furniture/actor clearance, native event/cog IDs,
stage equality and swap overlays):

```sh
flock -s output/hesper_stage/locks/stage.lock python3 -B level_generation/projects/hesper_d11/check_pickups_batch_d.py
```

Author, compiler and pickup-scenario logs are in `review/pickups/`. The batch regression record is
`hesper_d11/review/pickups/regression.log`.

Validation: all pickup clicks and existing map scenarios pass; `rebuild_all.sh --scenarios-only` passed
93/93 (exit 0), with decoration-ID and actor-size audits clean. Run logs: `output/hesper_stage/logs/scenarios_082229_4/`.

## R5 Gloam Elders — 2026-10-26

Replaced all 43 Reaver Drones with Gloam Elders (10322), preserving their actor indices and every Kreegan record.
Eleven physical packs occupy broad floor: four packs of four in western Freight Line (z=0), six of four and one
of three in the eastern Flooded Cut (z=-512). The cut packs sit beyond x=14500 so they cannot acquire the
Drudges through the intervening walls. All are mobile. Slot 1 is `hes_gloamer`, difficulty 4, count [0,0].

The tram note now describes pale freight-line creatures. Inactive cradles and drone wreck decorations are retained
as architecture; they are not live drone spawns. The isolated walkability pursuits clear all residents first,
keeping their spawned index 72 and original routes. Static walkability has zero findings; standard scenarios pass.
`d15_gloamers.yml` advances one minute with a distant invisible observer: all 72 residents retain full HP, and
all 43 elders remain near their dens with no target. This catches Psychic Shock reaching Kreegans through walls.

`review_tour_gloamers.yml` captures all three final pack poses on NVIDIA OpenGL, minimized. The
[Freight Line](review/gloamers/01-freight_line.png) and both Flooded Cut images were inspected; the cut elders
stand on the existing submerged floor with their shoulders above the brine. The
[creature project](../../creatures/hes_gloamer_codex/README.md) contains playback and test evidence.
