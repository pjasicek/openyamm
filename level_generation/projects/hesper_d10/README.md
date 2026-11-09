# D10 Colony Archive — hes_d10.blv

Map **9105**, world **hesper**, from
[`D10_COLONY_ARCHIVE.md`](../../../design/kreegan_world/zone1/dungeons/D10_COLONY_ARCHIVE.md), the zone-1 `d10`
plan and P4's item placement/readable handoff. Built with `hesper_stage/blv_kit.py` and `blv_build.py`.
Everything installs into `output/hesper_stage`; this project never writes `assets_dev`.

## Walkability and room shapes — 2026-10-24

Desktop review follow-up (2026-10-24, item 5): the Gallery Ramp doorway now has one portal into each
Atrium half, with its continuous reveal split between those sectors and no central jamb. Both doorway halves
are connected from the original lower-bend pose.
The map was restaged under the exclusive lock; its audit and all map scenarios pass. Tour poses are unchanged.
Evidence: `review/walkability/desktop_fix/`; logs: `output/hesper_stage/logs/walkability_review_c_20261024/`.
Native recapture is blocked by this sandbox’s “SDL_Init failed: No available video device”; desktop visual
confirmation remains with the integrator. The full shared sweep below predates this focused follow-up.

The Reading Rooms have 128-unit corner chamfers. The Gallery Ramp retains its 512-unit drop and 512-wide floor,
with paired 45-degree bends moving its middle 128 east; both doorway positions stay unchanged. Its ceiling
follows the slope, with no floor underneath. Its hanging light bar is raised 128, from 164 to 292 above the
ramp, leaving clearance for the melee pursuers. The chamfered Dome Atrium remains the signature hall.
The native survey counts 7/12 non-orthogonal room parts, 91% axis-aligned wall area and four sloped ceilings
(before: 3/12, 93%, four). The author checks controls, fixtures and pickups against their room footprints.

The middle Reading Reaver (actor 1) moves from (3300, 1200, 180) to (3500, 1200, 180), clear of the suspended
light crossbar. All eleven actors retain their order, IDs and groups. The 22 pickups, three ground items
(Charter, Repeater and shelf gold), three doors, three chests, events/cogs and arrivals are unchanged.
There are 1,328 native faces and twelve occupied sectors, at most 284 non-portal faces per sector.

The local and staged walkability audits have zero live findings. Nine furniture exceptions are documented in
`hesper_stage/walkability_allow.yml`: four reading desks, four glass well caps and the relic/gold shelf.
`d10_walkability.yml` checks a tall ground melee monster at the cleared Reading position and pursuers on the
gallery in both directions. `review_tour_walkability.yml` covers those spots and the reshaped rooms for the
integrator's capture. Evidence is in `review/walkability/`. No new stand-ins or shared kit changes.
All four shared-stage scenarios pass: main route 112, hacking/hazard 70, pickups 17 and walkability 44 steps.
D10 is in the shared walkability gate and scenario queue; staged payloads match the runtime byte for byte.
These counts supersede the historical geometry records below.

Final shared regression: `rebuild_all.sh --scenarios-only` passes **103/103** (exit 0). Actor-size and
decoration-ID audits have zero mismatches; the design audit has zero findings. Logs:
`output/hesper_stage/logs/scenarios_141329_8/`; batch summary:
`output/hesper_stage/logs/walkability_batch_c_20261024/validation_summary.json`.

## Build and stage

Run from the repository root. The author imports the plan without running its document-generation main.

```sh
flock -s output/hesper_stage/locks/stage.lock blender --background --factory-startup \
  --python level_generation/projects/hesper_d10/author_d10_blender.py
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
  python3 level_generation/projects/hesper_d10/build_d10.py
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py
```

On this sandbox the snap launcher fails, and Blender's audio shutdown can hang after a successful save. The verified
local invocation is `/snap/blender/current/blender --background --factory-startup --python <author path>`.
The author flushes output and exits immediately after a successful export. Check the author log for a traceback
and require the compiler's successful output. The thumbnail-cache write warning is unrelated to the saved map.
No engine build is required.

## Built content

Seven rooms, twelve occupied sectors plus empty sector 0, eleven actors, three rising doors, three loot containers,
45 decorations and seventeen lights (the thirteen plan lights plus four small shard-socket lights). The plan's
ceiling/stacking/light checks pass; the native compiler reports zero warnings. The dome and Memory Wells are
chamfered round rooms; the gallery has a continuous slope down 512 units. Adjoining walls are inset 32 each to give
64-unit openings with floor, soffit and jambs.

The four plaques give wells **2, 4, 1, 3**. A wrong choice resets the sequence and deals Air 2D8. Partial progress and
the solved state survive reload; lit wells show their founder reliefs. Success opens door 3 and enables the Hall's
gold light. The archivist supplies key 11487 once; it opens door 2 without being consumed. Master Hacking opens the
same door and makes Sentinel group 4 friendly until reload. The shorted shelf deals Air 3D8 within 300 and recharges
in ten one-second ticks.

The Charter **11372** is a real pickup on the Reading Rooms' lectern at **(3900, 1500, 115)**, with P4's full readable
text and approved slate icon. A thin physical tray supports it. The Repeater **11420** and **20,000 gold** lie on the
Armoury shelf at **(3120, -3000, -400)** and **(3300, -3000, -400)**. There is no event-18 chest. Casket 2 contains
11481, 11332 and three 11331; event 19 completes S3 (100103, clearing 100223). The record sets 100050 and autonote
10030; puzzle success sets autonote 10031. Incidental floor gold was removed in the pickups pass below.

Ground items and actors use the compiler's GLB room order, checked against the exported GLB. Merely using the
semantic room insertion order gives incorrect sectors; assigning pickups to empty sector 0 makes them unpickable.

## Starport Reach integration

The incoming arrival is `source/hes_d10.semantic.json` → `arrivals.dome_stair`: **(1200, 2150, 0), 270°**.
Starport Reach event **13** currently displays its sealed-door placeholder. The integrator should gate its
`dungeon_entry('hesper_d10', 'hes_d10.blv', 'dome_stair', ...)` call on **100022**, retain the sealed hint before it,
and light the outdoor sockets from **100018–100021**. This builder did not edit or rebuild `hesper_out1`.

D10's return reads out1's exported `archive_dome` event-13 face in its source geometry/scene manifests. It steps
500 units south of that face, yielding **(-8640, 18747, 1152), 270°** in the current build. No outdoor coordinate is
hardcoded in the build script. Please publish a named `archive_arrival` in `out1_build.json` when wiring the entry;
D10 can then use that named record. The outgoing transition is tested; the round trip waits for the entrance hook.

## Scenarios and review

```sh
cd output/hesper_stage/scenario_run
OPENYAMM_START_MINIMIZED=1 flock -s ../locks/stage.lock flock -s ../locks/engine_build.lock \
  ../../../build/game/openyamm --world hesper --headless-run-scenario \
  ../../../level_generation/projects/hesper_d10/d10_main_path.yml --scenario-no-color
OPENYAMM_START_MINIMIZED=1 flock -s ../locks/stage.lock flock -s ../locks/engine_build.lock \
  ../../../build/game/openyamm --world hesper --headless-run-scenario \
  ../../../level_generation/projects/hesper_d10/d10_hacking_and_hazard.yml --scenario-no-color
```

`d10_main_path.yml` exercises actual controls and pickups, plaque/relay interactions, both lockers, wrong and correct
well sequences, partial/solved save-load, the key route, casket/record flags, the ramp and three passage walks, and
the exit to Starport Reach. `d10_hacking_and_hazard.yml` checks rejection without the key/skill, Master Hacking,
Sentinel hostility reset, safe brine, the shelf's damage and recharge. Combat clearing is explicit test setup.
Both are registered in `hesper_stage/rebuild_all.sh`.

**Validation status (2026-10-23):** both D10 scenarios pass (112 and 70 steps). Static checks confirm empty sector 0,
288 maximum faces per occupied sector, at most three overlapping floor lights including the four sockets, eleven
actors, three containers and five ground items. The design audit reports zero findings. Logs are in `validation/`.
The pre-existing `assets_dev` status paths are unchanged from the start of this task.

The registered scenario queue was checked against the existing stage without rebuilding other maps: **32/35 pass**
including both D10 scenarios. `validation/regressions/results.txt` records the other 33 runs. D11
`seedship_sabotage` fails step 81 (24.801 units from its expected stop, tolerance 16); Undervault `bulkhead_open`
fails step 5 because the newly built D15 transition replaces its old stay-in-Undervault expectation; D5's
`relay_spire_climb` remains the queue's declared WIP failure (step 45). These other projects were left unchanged.

The user explicitly assigned capture to the integrator: **`review/build01/sheet.jpg` was skipped**. The prepared tour
includes the dome, plaques/Charter, Stacks, ramp, dormant/lit wells, Armoury and Hall. From the repository root:

```sh
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
  ./tools/run_game.sh --isolated hesper_d10_review --world hesper --map hes_d10.blv \
  --assets "$PWD/output/hesper_stage/assets_editor_dev" \
  --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d10/review_tour_01.yml" --seconds 0
```

The launcher starts minimized. Native visual review, daylight/texture assessment and the contact sheet remain for
the integrator. The full shared rebuild script also rebuilds out1; it is left to the integrator under the user's
out1 ownership restriction.

## Stand-ins, adjustments and outstanding integration

- All specified surface textures and decoration models exist; no decoration or texture substitutions were needed.
  Ground models use native aliases: Charter `scroll2`, Repeater `raygun2`, Armoury Key `7item361`, shard `gem7`,
  Core `gem5`, Engrams `shard`. Their approved Hesper icons are staged where available. Heavy Sentinels retain the
  shared Ward Turret body pending their own art.
- The compiler has no indoor water flag. `hawater` is a safe flat floor, without physical wading or water reflection.
- No sector-ambient event API exists. The Hall retains ambient 28; its gold light switches on. The requested
  ambient 28→16 change needs integrator/engine support.
- The console marker (2300, -3100) is inside the locked Armoury. Its control face is fitted on the outer wall at
  x=2068, y=-3100, so the alternative Hacking route is accessible.
- The Charter position was unspecified; its lectern placement is recorded above for review. Shelves stop short of the plan's archivist and locker locations.
- The two H3 lockers use the existing native T6 stand-in (9,000 gold each) until Hesper's H3 pool is integrated.
- Drones use the native roaming/combat AI. Exact room-bounded patrols need per-actor movement constraints; this build
  does not add an AI implementation or change the shared drone rows. The Repeater's draft Chain2/special shield
  properties likewise await engine integration; its item row, base Energy Guns statistics and placement are present.
- The staged facility music is available. Dedicated water/crystal ambience, well chimes, static crack and projected
  volumetric daylight shafts remain presentation work; the wells have native light/texture/portrait state changes.

Questions for the integrator: accept the accessible console face and unspecified loot placements; publish the out1
return key and wire event 13; schedule the patrol, shallow-water, ambient, audio and relic-effect follow-ups.

## Pickups placement (2026-10-24)

12 stim canisters and ten colony satchels (1,210 faces). Six canisters form the Guard Armoury supply store
(events 700–705); three stand at each end of the Reading Rooms (706–708 west, 709–711 east). The built Archive has
no medical bay, so the existing Armoury is the matching storeroom. Satchels sit at the edges of the Atrium,
Reading Rooms, Stacks, Wells, Armoury and Hall, clear of doors and the existing scenario routes.

[`pickups.json`](pickups.json) records every position and event/cog id; the author exports them into the map.
The shared pickup mechanic supplies colours, opening, rewards and refill. All four batch-C maps are H3 and pass
`treasure = 6`: `evt.GetCurrentMapName()` currently returns the display name, while the shared automatic lookup
expects the filename. No shared mechanic or engine change is needed for this explicit setting.

The two incidental fixed floor-gold piles were removed under PICKUPS.md. The Charter, Repeater and authored
20,000-gold shelf reward remain; there are now three ground items.
No pickup models or textures needed stand-ins.

[`d10_pickups.yml`](d10_pickups.yml) tests actual clicks at the placed models and their resulting map variables. [`review_tour_pickups.yml`](review_tour_pickups.yml) supplies the storeroom and two supply views for the
integrator; captures remain with the integrator. `review/pickups/placement_checks.json` records floor support,
clear footprints and unchanged compiled geometry. Build and scenario logs are in
`output/hesper_stage/logs/pickups_batch_c_20261024/`.

Validation: the four builds and stage passed; all **17 batch-C scenarios** and the complete
`rebuild_all.sh --scenarios-only` sweep (**93/93**, exit 0) passed. Both decoration-id and actor-size audits
report zero mismatches across 22 maps; the design audit has zero findings. Final suite logs:
`output/hesper_stage/logs/scenarios_082633_7/`; summary: `pickups_batch_c_20261024/validation_summary.json`.

## R5 Gloamers — 2026-10-26

Added two four-member Gloamer packs (10321): southern Flooded Stacks B at z=0 and the vault hall A at z=-512.
They occupy broad floor clear of the stairs. Earlier actors 0–10 retain their records; the new actors are 11–18.
The build appends local semantic packs, leaving the design source unchanged.

`d10_gloamers.yml` advances one minute from the distant atrium: every resident keeps full HP and the eight
Gloamers remain near their packs without targets. Static walkability has zero findings; standard scenarios pass.
`d10_walkability.yml` clears residents before each isolated pursuit and uses spawned index 19 (formerly 11).
The direct minimized NVIDIA OpenGL tour succeeds; [native vault pack](review/gloamers/02-vault_den.png).
Both final images were inspected. Model playback and all results are in the
[creature project](../../creatures/hes_gloamer_codex/README.md).
