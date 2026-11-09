# Hesper D13: Deepwell

Map **9135**, `hes_d13.blv`, built from the complete [build document](../../../design/kreegan_world/zone4/dungeons/D13_DEEPWELL.md)
and `plans_zone4.py`'s `d13` plan. Shared author/compiler: `hesper_stage/blv_kit.py` and `blv_build.py`, following D12,
D1 and D2. Native BLV geometry uses the kit's tiled textures and explicit sector membership, rather than model LODs.

## Build and stage

From the repository root:

```sh
(cd level_generation/projects/hesper_d13 && flock -s ../../../output/hesper_stage/locks/stage.lock blender --background --factory-startup --python author_d13_blender.py -- --through tap)
# First-level compile and plan checks are recorded under review/.
(cd level_generation/projects/hesper_d13 && flock -s ../../../output/hesper_stage/locks/stage.lock blender --background --factory-startup --python author_d13_blender.py -- --through escape)
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock python3 level_generation/projects/hesper_d13/build_d13.py
flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_d13/make_scenarios.py
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock python3 level_generation/projects/hesper_d12/build_d12.py
flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_d12/make_scenarios.py
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py
level_generation/projects/hesper_stage/rebuild_all.sh --scenarios-only
```

The integrator rebuilds `hesper_out4`. Do not run the full shared rebuild while builders work. Any compiler/engine
rebuild takes `engine_build.lock` exclusively; every game run takes it shared. No engine rebuild was needed here.

## Built

Eight rooms on two levels, 14 occupied sectors plus empty sector 0, 1,462 faces, 926 vertices, six movers, 28 actors,
25 decorations, 20 planned lights (three explicit and 17 fixtures), no chests, and a reachable ground Breach Charge.
The final busiest sector has 284 faces including its portals. Nine simple sectors have 38–86 faces, below the
guide's nominal 100-face lower target. Both level checks and the final check report no ceiling or stacking problems;
maximum light overlap is two.

The three locks support Hacking Expert or the 120-second two-wave manual override, consumption of item 11304, and
Aster's codes. The overload seals door 3, opens door 4, changes the exchanger/core/alarm textures, pulses the red
beacons and counts down in status text without pausing play. The two pressure plates queue their rubble movers,
show the Pyre Hounds/Harrowers and keep the northern loop passable. The vent preserves locks 1–2, resets lock 3 and
both collapse plates, raises the blocks, hides groups 7–8 without reviving their dead members, returns to `tap_ring`
and offers another overload on the next one-second timer tick. Same-map travel closes dialogs, so the question
must follow the teleport rather than be issued in its frame. Countdown restoration is tested across saving/loading;
override progress is stored in map variables. Tear it out selects
the Pilot/safety-vent text. Only the Service Lift sets 100607; its travel confirmation can be canceled and retried.

Published arrivals:

| Key | Position | Facing |
|---|---|---|
| `shaft_bottom` | `[400,1000,0]` | east, 0° |
| `tap_ring` | `[5228,1000,0]` | east, 0° |

Exit 50 reads D12's `shaft_head`; exit 51 reads the Crown's `pad_lift`. D12 was rebuilt to read this project's
`shaft_bottom` for exit 53. Its previously reported gate interception does not recur: after opening door 1,
a current-view click at D12's `spire_gate` arrival `[0,400,0]` triggers exit 50 and reaches the Crown. That exact
pose and event assertion are now retained in D12's round-trip scenario. Deepwell's escape is intentionally one-way;
the shaft round trip is tested before the overload.

## Checks

Run one scenario from the stage working directory, minimized and under both shared locks:

```sh
(cd output/hesper_stage/scenario_run && OPENYAMM_START_MINIMIZED=1 \
 flock -s ../locks/stage.lock flock -s ../locks/engine_build.lock \
 ../../../build/game/openyamm --world hesper --headless-run-scenario \
 ../../../level_generation/projects/hesper_d13/d13_main_path.yml --scenario-no-color)
```

- `d13_main_path.yml`: actual ground pickup and console clicks, seals, both floor plates and rubble drops, the
  16-step stair, both loop openings, Service Lift confirmation cancellation/retry and 100607/Crown arrival.
- `d13_override.yml`: both defence waves and the full 120-second release without Hacking.
- `d13_vent.yml`: native clock reaches one second; save/load retains it; actual vent teleport, locks, doors and retry question.
- `d13_collapse_reset.yml`: vent after both cave-ins, with living and dead members of the collapse groups.
- `d13_charge.yml`: native Crown Harrower charge hits; the party can still click lock 1 from its resulting pose,
  with no teleport/reset between the hit and click. The pit has a continuous 128-high blocking railing.
- `d13_round_trips.yml`: shaft lift to D12 and actual exit 53/Yes back to Deepwell.
- `d13_smoke.yml`: cold start, dormant wave, initial doors.

These seven checks are registered in the scenarios-only regression. Final results are in `review/verification.json`.
The latest complete regression (`output/hesper_stage/logs/scenarios_154442_3/`) ended **68 PASS / 3 FAIL**, exit 1.
D8's main path and D15's side paths passed unchanged locked retries. Crown's entrance scenario still uses the
old D12 doorway pose at y=-3292; its current build record publishes y=-4817. D12's own scenario was regenerated
from that record and all four D12 scenarios pass. The complete shared run remains failed; Crown's builder owns
its scenario update. The subsequent lift cancellation/retry fix passes the updated D13 main path and both clock
rehearsals.
After `d13_override` and `d13_collapse_reset`, run `python3 level_generation/projects/hesper_d13/check_scenario_saves.py`:
it checks the saved actors' actual visibility flags before/after the waves and vent, and the party's native
movement state at `tap_ring`. The vent scenarios use neutral movement frames because `advance_runtime` does not
process timer-issued map moves; no engine changes were made.
`d13_timing_bare.yml` and `d13_timing_fighting.yml` are separate clock rehearsals: 18.441 and 73.259 scripted
seconds from the escape door to the lift; the native countdown has 99 and 45 seconds left respectively at the
exit click. The fighting fixture is five level-135 Knights, Energy Guns 20 Master, Ion Carbines, with 50 seconds of
native firing/recovery across the escape packs. It engages the packs and then leaves; it does not require every
enemy to die. Geometry collision remains active; actor-body collision is disabled for repeatable movement.
The 120-second clock is retained. These controlled rehearsals do not establish human difficulty balance.

## Integrator review and stand-ins

`review_tour_01.yml` is ready with the six requested shots; `tap_overload` restores the hot state through console
commands. Positions are party feet; the engine adds eye height. **No screenshots or `review/build01/sheet.jpg` were
captured**, as explicitly requested for this sandbox. The integrator captures the sheet and reviews appearance,
Wizard Eye/automap readability, and the playing/fighting run.

```sh
flock -s output/hesper_stage/locks/engine_build.lock flock -s output/hesper_stage/locks/stage.lock \
 ./tools/run_game.sh --isolated d13 \
 --world hesper --map hes_d13.blv --assets "$PWD/output/hesper_stage/assets_editor_dev" \
 --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d13/review_tour_01.yml" --seconds 0
```

| Art / behavior | Staged representation |
|---|---|
| Crown Harrower 10242 | Existing Trooper C body/attachments/clips. Its designed native charge modifier is installed from the design data. Its frenzy remains pending engine support, as the design specifies. These actors are mobile, so the shared row's post leash (which only applies to immobile placements) does not restrict their chase. |
| Crown Sentinel | Existing Ward Turret body. The Pyre Hound and Reaver Drone use their dedicated models. |
| Tunnel lamps / rotating red beacons | Existing amber wall-light and dark wall-light bodies; the exact planned amber/red radii and colours, and beacon pulses, are applied. No rotating dome model yet. |
| New machine/alarm/crash audio and spoken countdown | Existing staged charge/hover/EMP sounds and P4's text; dedicated audio/voices remain art work. |
| Steam / falling dust | Project effect definitions using the existing smoke sprite, with upward steam and downward dust. |
| Breach Charge | Existing staged item's ground-art stand-in on a reachable 64-high supply shelf. |

All K3 deep masters and K1 trim/console/door textures exist and are used. The dead technician, shelf rack and rubble
use their existing decoration models. Machines, the column, railing, consoles and debris blocks are map geometry.
Three geometric collars shape the tap column; the tiled `htcore` master carries its smaller stacked rings, keeping
the busiest sector within the face budget. The plan leaves 464 units between the exchangers and control: one
continuous reveal bridges that marked link. No design positions were moved. The plate follows the plan's y=3150
(690 into the hall), rather than the stale “500” wording in the events table.

## Brightness B — 2026-10-23

Main rooms now use ambient 14; corridors, stairs and the lift use 15. D13-only tunnel lamps have radius 864 and
alarm beacons 704; the exchanger heat and hot-core radii are 1056 and 1200. Three always-on amber fixtures cover
Control, the Collapse Stair and the Exchanger Loop, so every room has a lit fixture of radius at least 640 even
between alarm pulses. The existing red alarm groups/pulse and magma glow remain. All 23 lights together peak at
four overlaps, including a 32-unit check of actual stair heights across both levels. Ceiling/stacking checks pass.

The Debris Hall's machinery spine now has one fitted gauge row at z=96–224, centered at the party's 160-unit eye
height, with plain `hcpanel` above and below. The compiled gauge UVs span exactly one texture height; the block's
bounds and both aisles are unchanged. No new texture/model stand-ins were needed.

The complete map was re-authored and built under the shared stage lock: 1,486 faces, 938 vertices, 15 sectors,
six movers, three explicit lights, 28 decorations and zero compiler warnings. YAML checks and exclusive staging
pass. All scenarios pass: main **89/89**, override **54/54**, vent **66/66**, charge **28/28**, round trips **15/15**,
collapse reset **88/88**, smoke **6/6**, bare clock **90/90**, fighting clock **92/92**. Native saved wave flags,
collapse visibility and vent arrival also pass. The save checker now explicitly accepts version 101 after checking
its actor/movement prefixes against the serializer (the new version adds MAW class state elsewhere).

Evidence is in `review/brightness_b/`, including the shared regression log and native gauge/fixture checks.
The design audit has zero findings; its report was written there without rewriting the design's audit report.
The original six-shot sheet is preserved (mean 62.5, darkest 42.6); the tour now targets `review/build02/`.
No new capture was attempted. The integrator captures and re-measures; final regression results are in P3.


## Pickup placement — 2026-10-24

10 stim canisters: 5 in the sealed shaft stores, 3 by the exchanger crews’ lockers and 2 at the debris hall’s
side. 12 colony satchels. All positions are authored in `author_d13_blender.py` and exported under `pickups`
in the semantic record. Stat containers occupy wall-side storage groups; satchels avoid boss rooms and central
routes.

The authored handlers call `HesperPickups.setup` with explicit treasure level **6 (H3)**. The shared automatic
map-name lookup failed at the first satchel click; the documented treasure override gives the correct dungeon
loot level. Stage installation supplies `hes_d13_pickups.lua` with every colour/empty model. No new art or
stand-ins were needed.

`d13_pickups.yml` clicks every placed pickup; all stat containers reach the empty state and survive save/load.
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

### Pyre Hound placement (2026-10-26)

R5-1 replaces the eight Drudge Hulk records with Pyre Hounds (10302), retaining actor
indices and trigger groups. Five patrol the Heat Exchangers' central aisle. The hidden
group 7 pack of three moves from Debris Hall to the western Exchanger Loop, near
(4900,7250,512), alongside the countdown Harrowers. The existing visibility triggers
remain authoritative. No own event or scenario source names the replaced monster id.
The Reaver Drone records and other groups are preserved for their separate R5-3 change.

Native R5 review spreads the five exchanger hounds across two rows (x=2800–3600, y=1000/1350) and the three countdown hounds over x=4500/4900/5300, clear of the Harrowers.

R5 native-save verification rechecked the actor/movement prefixes against the serializer and explicitly
accepts the current executable's version 133, alongside 106. Later formats still require a fresh check.

The scenario runner now removes its temporary saves. For this native-save check, run `d13_override` with
`OPENYAMM_SCENARIO_SAVE_DIR=/tmp/openyamm_scenario_saves/hesper_d13_d13_override`, and
`d13_collapse_reset` with `OPENYAMM_SCENARIO_SAVE_DIR=/tmp/openyamm_scenario_saves/hesper_d13_d13_collapse_reset`.
Set that environment variable on the headless command shown above; it retains fresh saves for the checker.

## R5 Gloam Elders — 2026-10-26

Replaced only the six Reaver Drones (10052, actor indices 5–7 and 25–27) with Gloam Elders (10322), in two packs
of three. Slot 3 is `hes_gloamer`, difficulty 4, count [0,0]: placed actors only. All Kreegans and the eight
Pyre Hounds from R5-1 retain their records.

The upper pack occupies the Collapse Route (z=512). The lower pack occupies a dark basalt Deep Vein side cavern
beyond the debris room (x=8192..10792, y=2900..4400, z=0), connected by a 512-wide opening. This realizes the
specified vein below the tap and separates the wild elders from the Kreegans' 2560-unit acquisition range.
There are now 16 occupied sectors, 17 apertures/34 directed portals and the same six doors. Geometry remains
local to this project; no design generator or other creature project was edited.

Removed the two stale drone-hover calls from collapse handling; the existing timed EMP cue remains. Generated
scenario fixtures now kill unshielded elders/hounds once, preserving two-hit shield removal on Kreegans.
`d13_gloamers.yml` uses a distant invisible observer and advances one minute: all 28 actors retain full HP, all
six elders stay by their dens with no target. Standard scenarios pass. Static walkability has no actor findings;
its one remaining finding is the existing 64-unit charge shelf at (5304,1896,64), unrelated to these packs.

Both additional timing scenarios pass. The direct minimized NVIDIA OpenGL tour succeeds; all three final images
were inspected, including the [elder's front and sac](review/gloamers/03-elder_front.png). Final clip renders,
playback and headless results are in the [creature project](../../creatures/hes_gloamer_codex/README.md).
