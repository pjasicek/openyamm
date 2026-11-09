# D7 — Lattice Node East

Map **9132**, `hes_d07.blv`, built from D7 BUILD-READY and `plans_zone4.py`. The sixteen shared sectors come from
[`hesper_nodes_common`](../hesper_nodes_common/README.md); D7 adds the assembly hall (two), capacitor gallery and T2.
The map has 20 playable sectors plus empty sector 0, 2,500 faces, 48 portal triangles, eight doors, 41 actor records
(40 design actors, with two mutually exclusive Bulwark forms), four chests, six loose items and 20 colony satchels.
The plan supplies 36 lights: 29 fixtures and seven explicit lights. Compilation has zero warnings.

The assembly beds, ten cradles/shells, six fabricator arms, line-stop, fourteen mine plates, common terminals,
heart and couplings are built. Timers release the line's two flights at 20/40 seconds unless stopped, and deploy
one core mine every six seconds during the coupled phase. Grandmaster Hacking at a collar precedes consuming a
charge. Cutting all three feeds swaps the immune coupled Bulwark for its free form, hides its cables and disarms
its mines. The free form has the twelve-second sweep and overheat behaviour. Heart shutdown grants 40,000 XP,
sets 100009, clears 100209, opens the service door and opens the vault only if no coupling was blown.

## Commands

From the repository root. Background Blender uses no display; game runs stay minimized and take shared locks.
On this sandbox the actual Blender executable is `/snap/blender/current/blender`.

```sh
(cd level_generation/projects/hesper_d07 && \
 SDL_AUDIODRIVER=dummy ALSOFT_DRIVERS=null XDG_CACHE_HOME=/tmp/d07-cache \
 flock -s ../../../output/hesper_stage/locks/stage.lock \
 /snap/blender/current/blender --background --factory-startup --python author_d07_blender.py)
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
 python3 level_generation/projects/hesper_d07/build_d07.py
python3 level_generation/projects/hesper_d07/make_scenarios.py
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py
(cd output/hesper_stage/scenario_run && \
 for scenario in d07_main_path d07_loud_path d07_factory_and_mines d07_arcs d07_front_and_charge d07_pickups; do
   OPENYAMM_START_MINIMIZED=1 \
   flock -s ../locks/stage.lock flock -s ../locks/engine_build.lock \
     ../../../build/game/openyamm --world hesper --headless-run-scenario \
       "../../../level_generation/projects/hesper_d07/$scenario.yml" --scenario-no-color \
       > "../logs/$scenario.log" 2>&1 || exit 1
 done)
python3 level_generation/projects/hesper_d07/check_scenario_saves.py
level_generation/projects/hesper_stage/rebuild_all.sh --scenarios-only
```

The supplemental checker reads the scenario saves' native actor visibility bits and compares the mine-health
traces at `output/hesper_stage/logs/d07_factory_and_mines.log`. Redirect the focused run there, as in this build,
when rerunning that check. It deliberately requires save version 100 and validates the actor-record prefixes;
update it with the save codec if that format changes. The standard scenario runner cannot assert visibility bits.

Authoring regenerates D7's greybox models. For a fresh stage, run `author_standins_blender.py` directly and stage
its decoration registrations before the map's first export. Reread shared inputs before additive edits, parse edited
YAML before staging, and never run the full rebuild during parallel builds. D7 does not build the Crown.

## Verification

All five final staged scenarios pass (97, 46, 43, 10 and 12 steps), as do the native-save checks.
The design audit reports zero findings; the `assets_dev` status matches the pre-build snapshot.

The shared `rebuild_all.sh --scenarios-only` run finished **62 PASS / 1 FAIL / 1 WIP-FAIL**, exit 1.
D8's main path could not load its map at step 1; an unchanged, locked retry passed all 98 steps. D5's relay climb
remains its existing non-gating WIP failure. The complete run did not pass, although every gating scenario now
has a passing result. Logs: `output/hesper_stage/logs/scenarios_151228_61/`, `d07_regression.log` and
`d07_d08_main_path_recheck.log`. No other map was rebuilt or patched.

The five native scenarios cover:

- `d07_main_path`: the inner door/pylon, west door refusing from T1, assembly aisle and stopped factory,
  marked minefield route, T2–T3, quiet boss swap, save/load, boss reward, vault contents and service-hatch round trip.
- `d07_loud_path`: real cache charge plus two carried charges, armed core mine, three charge consumptions,
  boss swap, two alarm waves, persistent fused vault and completion.
- `d07_factory_and_mines`: Grandmaster collars preserve the carried charge and stay quiet; both factory flights
  appear on schedule; a mine does exactly 75 damage per character once, including after save/load.
- `d07_arcs`: live and safe crossings using native walking.
- `d07_front_and_charge`: a native Harrower charge and the front-door Crown round trip.

The supplemental save checks verify the actual group 8/9 visibility swap, groups 12/13 remaining hidden after
line-stop, their 20/40-second release, and both alarm waves. Tests use high-level fixture parties, scripted boss
damage and disabled actor AI on movement segments: they verify mechanics, not combat balance or art quality.

D7's only shared-module extension is optional `wall_roles`, used for its east-wall T2 accent. D6's pre/post
construction data compares identical (`d07_common_unchanged.log`), and all three of its scenarios pass in the
shared regression. Every new greybox model passes winding checks with zero inverted closed parts. All plan
ceilings/light-overlap checks and interaction/door checks pass. Some inherited simple sectors are below the
100-face target; D7's busiest sector stays below 300 by using four-sided fabricator posts.

## Arrivals and runtime state

`blast_door`: (4800, 300, 0), 90°; `service_tunnel`: (3424, 12200, -512), 270°.
Both exits read `d7_door`/`d7_hatch` from `hesper_out4/out4_build.json`; the return checks read its `door_poses`.
The integrator independently updated the Crown during this build. D7 does not substitute guessed outdoor
coordinates, edit the Crown output or rebuild the Crown. Both complete round trips pass against that stage;
the service return retains the completed node state.

Map variables 1–9 follow NODE_SKELETON; 10 is the free-form flag, 11 first visit, 12 west shortcut unlatched,
13 line state, 14 line seconds, 20–27 gallery mine states, 30–35 core mine states, 36 core entered. Mines use
0 empty, 1 armed, 2 spent. Door ids 1–6 follow the skeleton; 7 is assembly-to-gallery (event 58), 8 gallery-to-T2
(event 59). Bulwark free/coupled actor indices are emitted in the semantic record rather than assumed by tests.

## Stand-ins and remaining decisions

- The Harrowers use Trooper A/B/C bodies. Their design `charge` modifiers are staged and a native charge passes;
  Frenzy is still pending engine support. The Bulwark forms currently use the shared Ward turret model as a
  temporary machine body; final walking legs, sockets, mine racks and sweep animation are missing. Existing
  Trooper/Ward bodies also supply the shared Nobles and Sentinels.
- Own low-poly greyboxes supply mines/spent scorches, drone shells, the wreck and three removable cables.
  Existing D4 lever aliases supply the line-stop; the common module supplies its coil/dark-pylon stand-ins.
  The mines have steady emissive eyes rather than final blinking art. No surface texture stand-ins were needed.
- **Capacitor wall banks are pending placement approval.** The document gives 500-unit spacing but no origins;
  applying it along the two long walls intersects marked mines, doors and the safe path. The prescribed 640 height
  also exceeds the 512 ceiling. No mine or route marker was moved to accommodate them. Supply a bank layout and
  fitting height. Approval to derive placements from the named walls was requested during the build.
- The line console retains its 400 × 300 footprint but extends west from its near-wall anchor and is 576 high;
  shared consoles retain D6's 64-unit headroom correction. The three cables derive endpoints from the boss/coupling
  marks and vary in length to reach them; the north span exceeds the document's generic 1,600-unit cable length.
- Shared roster tactics remain authoritative: 10041 lacks its post tactic; 10052/10042 retain shared 1,536 leashes,
  and 10241's shared guard leash is 1,536 rather than the line guard's requested 1,200. Per-placement leash differences
  need an integrator decision. The currently staged Sentinels have the requested 90°/s traverse.
- H3 lockers retain D6's native treasure-level-6 stand-in and average 12,000 gold (T1 18,000) until the Hesper
  loot pool is available. The vault has exact items 11331/11004. The boss spawns 11332 and credits 30,000 gold once
  because `SummonItem` cannot supply a gold payload. Incidental floor gold was removed in the pickups pass below.
  Native ground-item shapes stand in for Hesper loot models. Console/lever action recovery has no event API.
- Existing machine/combat sounds stand in for the dedicated factory/mine/cable sounds. The new steam effect uses
  the existing smoke sprite. The plan emits 36 lights although the prose says 35; the build follows the plan.

Screenshots, Wizard Eye review and `review/build01/sheet.jpg` are explicitly deferred to the integrator.
`review_tour_01.yml` contains the shared views plus assembly, capacitor gallery and Bulwark shots. Capture minimized:

```sh
flock -s output/hesper_stage/locks/stage.lock \
 flock -s output/hesper_stage/locks/engine_build.lock \
 ./tools/run_game.sh --isolated d07 --world hesper --map hes_d07.blv \
   --assets "$PWD/output/hesper_stage/assets_editor_dev" \
   --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d07/review_tour_01.yml" --seconds 0
```

## Pickups placement (2026-10-24)

20 colony satchels (2,500 faces; density capped at 20), no stat containers. Supplies are tucked around the
vestibule, Guard Hall, galleries, T1/T3 stores, service tunnel and assembly hall; the Core has none.

[`pickups.json`](pickups.json) records every position and event/cog id; the author exports them into the map.
The shared pickup mechanic supplies colours, opening, rewards and refill. All four batch-C maps are H3 and pass
`treasure = 6`: `evt.GetCurrentMapName()` currently returns the display name, while the shared automatic lookup
expects the filename. No shared mechanic or engine change is needed for this explicit setting.

The two incidental fixed floor-gold piles were removed under PICKUPS.md. The six themed cache items, chest contents and boss rewards remain.
No pickup models or textures needed stand-ins.

[`d07_pickups.yml`](d07_pickups.yml) tests actual clicks at the placed models and their resulting map variables. [`review_tour_pickups.yml`](review_tour_pickups.yml) supplies the storeroom and two supply views for the
integrator; captures remain with the integrator. `review/pickups/placement_checks.json` records floor support,
clear footprints and unchanged compiled geometry. Build and scenario logs are in
`output/hesper_stage/logs/pickups_batch_c_20261024/`.

Validation: the four builds and stage passed; all **17 batch-C scenarios** and the complete
`rebuild_all.sh --scenarios-only` sweep (**93/93**, exit 0) passed. Both decoration-id and actor-size audits
report zero mismatches across 22 maps; the design audit has zero findings. Final suite logs:
`output/hesper_stage/logs/scenarios_082633_7/`; summary: `pickups_batch_c_20261024/validation_summary.json`.

## Walkability (2026-10-24)

Built and staged; zero audit findings with two assembly beds allowlisted as furniture. D7 is audit-gated.
Shared node geometry gives 16-unit dais stairs with side parapets, chamfered vestibule/hall/terminals/core,
and hipped ceilings. The octagonal core's north-west cut preserves the service door. Seven actor positions
clear stairs, pipes, arc posts and the T2 console; identities/order, events, doors, cogs, pickups and arrivals
are unchanged. Survey: 10/18 non-orthogonal rooms, 11/18 sloped ceilings. Floor light overlap is at most three.

All seven scenarios passed on a private copy of the assets with the new D7 runtime: six pursuits in
`d07_walkability.yml` (192 steps), main/loud paths, factory/mines, arcs, front/charge and pickups.
All seven also pass on the shared stage in the final 108/108 regression sweep (exit 0).
The temporary engine SIGFPE was resolved by the 17:44 rebuild; no engine changes were made here.
Evidence: `review/walkability/`; logs: `output/hesper_stage/logs/walkability_batch_d/`.
`review_tour_walkability.yml` covers the repaired floors, rooms and assembly aisle. Screenshots await the
integrator's desktop capture. No new art or stand-ins.

Final batch-D sweep: `rebuild_all.sh --scenarios-only` **108/108 PASS, exit 0**. Decoration and actor-size
mismatches: zero. All five batch maps' staged walkability audits are zero and all five are gated.
Logs: `output/hesper_stage/logs/scenarios_174417_3622123/`; batch summary:
`output/hesper_stage/logs/walkability_batch_d/validation_summary.json`.
