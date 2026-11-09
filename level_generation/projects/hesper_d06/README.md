# D6 — Lattice Node West

Built and staged as map **9131**, `hes_d06.blv`, from D6 BUILD-READY and `plans_zone4.py` on 2026-10-23.
The [shared node module](../hesper_nodes_common/README.md) supplies the sixteen common sectors;
D6 adds the two pump sectors, two coolant-loop sectors and T2. Common construction was also exercised with
the D7 and D16 plans in Blender without exporting or changing those projects.

The compiled map has 21 playable sectors plus empty sector 0, 2,610 faces, 50 portal triangles, 15 movers,
37 actors (including eight initially hidden reinforcements and the Keeper), four chests, six loose items and
20 colony supply satchels. The plan contains 39 lights: 28 fixtures plus 11 explicit lights. All interaction faces bind,
all door ids match, and compilation reports no warnings. K9, K3 and the referenced K5/K1 surface masters resolve.

The quiet and loud paths, one-way west shortcut, timed arcs, four-vent sweep, eight alternating shield panels,
alarm waves, Keeper behaviour, heart shutdown, quest/experience reward, quiet-only vault, service door and
save/load restoration are implemented. The core's eight 850 × 64 × 1,024 panels are solid linear movers;
they alternate every three seconds and all sink when the boss dies. Couplings use D6's radius 800.

## Build, stage and test

From the repository root; `blender` must resolve to the actual executable. On this sandbox it is
`/snap/blender/current/blender` (the `/snap/bin/blender` launcher cannot run here).

```sh
mkdir -p output/hesper_stage/locks
(cd level_generation/projects/hesper_d06 && \
 SDL_AUDIODRIVER=dummy ALSOFT_DRIVERS=null XDG_CACHE_HOME=/tmp/d06-cache \
 flock -s ../../../output/hesper_stage/locks/stage.lock \
 /snap/blender/current/blender --background --factory-startup --python author_d06_blender.py)
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
 python3 level_generation/projects/hesper_d06/build_d06.py
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py
```

Reread shared stage inputs immediately before an additive edit and parse every edited YAML before staging.
The build writes `source/hes_d06.{blend,glb,geometry.yml,doors.yml,semantic.json}`, generated runtime files,
the boss/effect libraries and `d06_build.json`. Do not hand-edit generated runtime Lua.

```sh
(cd output/hesper_stage/scenario_run && \
 for scenario in d06_main_path d06_loud_path d06_hazards d06_pickups; do
   OPENYAMM_START_MINIMIZED=1 \
   flock -s ../locks/stage.lock flock -s ../locks/engine_build.lock \
     ../../../build/game/openyamm --world hesper --headless-run-scenario \
       "../../../level_generation/projects/hesper_d06/$scenario.yml" --scenario-no-color || exit 1
 done)
level_generation/projects/hesper_stage/rebuild_all.sh --scenarios-only
```

The shared rebuild registers D6 and its scenarios. Every game run must hold the engine lock shared;
engine builds use it exclusively. No engine build or outdoor lighting bake was needed for D6.

## Verification and review

All three faithful native scenarios pass:

- `d06_main_path.yml`: 86 steps; initial supply states, pylon, T1, physical route through pumps/loop/T2/T3,
  centre of the dais/ramp opening, live-core save/load, boss death/drops, quest bits, quiet vault and service
  tunnel, west shortcut, all panels down and dead-node save/load. Checks the current pending Crown exit.
- `d06_loud_path.yml`: 36 steps; rejected unskilled terminal, actual spare charge pickup plus two carried-charge
  fixtures, three consumed charges, alarm/wave delay, boss death, fused vault and persistent blown couplings.
- `d06_hazards.yml`: 31 steps; native walking across live/safe arcs and vents, core-entry trigger, panel clock
  and alternating door states. The damage traces show 60 Air and 55 Fire per character.

These are mechanics checks using high-level fixture parties, scripted boss damage and some disabled actor AI
on movement segments. They do not establish combat balance, fair targeting or visual quality of the boss phases.
The plan's minimum-ceiling and maximum-four-lights checks pass. New greybox model winding checks report zero
inverted closed parts; the design-data audit remains at zero findings.

The full `rebuild_all.sh` run built/staged every registered map and passed D6. It did **not** pass globally:
D11 `seedship_sabotage` failed its step-42 lift movement checkpoint; Undervault `bulkhead_open` expected to
remain in the Undervault after its bulkhead now travels to D15. D5's `relay_spire_climb` also failed under the
script's existing non-gating WIP classification. See `output/hesper_stage/logs/rebuild_d06_all.log` and the
individual scenario logs. These other maps were not patched by this build.

**Screenshot capture, `review/build01/sheet.jpg`, Wizard Eye and visual sign-off are explicitly deferred to the
integrator at the user's request.** Nine design shots are prepared in `review_tour_01.yml`. Capture minimized:

```sh
flock -s output/hesper_stage/locks/stage.lock \
 flock -s output/hesper_stage/locks/engine_build.lock \
 ./tools/run_game.sh --isolated d06 --world hesper --map hes_d06.blv \
   --assets "$PWD/output/hesper_stage/assets_editor_dev" \
   --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d06/review_tour_01.yml" --seconds 0
```

## State and integration contracts

| Map variables | Meaning |
|---|---|
| 1–3 | Couplings: 0 live, 1 shut, 2 blown |
| 4 / 5 | Pylon silenced / alarm raised |
| 6 / 7 | Boss dead / heart dead and reward granted |
| 8 / 9 / 10 | Arc clock / reinforcement clock / vent clock |
| 11 / 12 / 13 | Panel clock running / seconds / parity |
| 14 / 15 | First-entry text shown / west shortcut unlatched |

Timers 3–7 tick once per real second (30 game seconds). Completion sets QBit 100010, clears 100210 and grants
40,000 experience once per character. Door ids 1–6 and events follow the common module; D6 adds door 7/event 58
for T2, panel doors 8–15, vent events 100–103, Keeper death 151 and core-entry plates 152.

Arrivals are `blast_door` at (4800, 300, 0), heading 90°, and `service_tunnel` at (3424, 12200, -512), heading
270°. External exits read `hesper_out4/out4_build.json` arrivals `d6_door` and `d6_hatch`. That file is currently
absent: exit clicks explain that Crown integration is pending and leave the party in D6. The integrator must build
the Crown, rebuild D6, stage, and add both outdoor round trips; there are no invented destination coordinates.

## Stand-ins and outstanding decisions

- New flat-colour coil/on-off and dark-pylon GLBs live in `hesper_nodes_common/standins`. Existing colonial amber
  wall-light aliases supply the tunnel lamps. All use the plan's exact light radii/colours. No texture stand-in
  was needed. Geometry supplies the shelves, racks, pumps, chiller, terminals and heart.
- Two coolant valves and ten frost drifts are not placed: the document names them but supplies no position
  markers. Approval to use the machine anchors was requested and remains pending. Both low-poly frost sizes
  are prepared but unbound. The integrator should supply placements or approve the proposed anchors.
- Existing Trooper C bodies stand in for the Guards, Lancers and Nobles; Ward turrets for Sentinels; a native
  winged Demon C sprite for the Keeper. Its intended Noble body, halberd and coil harness remain art work.
  The Coil Spear/Regulator use existing native ground-item shapes; their Hesper icons and gameplay ids are staged.
- Existing shared roster tactics were preserved. Reconcile 10041's missing post tactic, 10057's current 60°/s
  traverse versus D6's 90°/s, and the Lancers' shared 1,536 leash versus the core adds' requested 800. The Keeper
  has its requested 1,200 leash and no Blink. Per-placement differences need an integrator decision.
- H3 has no staged native loot pool with its consumable/salvage chances. The three random lockers use native
  treasure level 6 and the design's average gold (12,000; T1 18,000). The quiet vault has exact items 11331/11215.
  The Keeper spawns 11422 and 11332; its exact 30,000 gold is credited once because `SummonItem` cannot supply a
  gold amount. Incidental floor gold was removed in the pickups pass below.
- Hacking checks the current character; the available event API does not charge the console action's recovery
  time. Existing charge, shield, impact and machine sounds stand in for the dedicated arc/hiss/hum cues.
- Consoles stop 64 below their ceilings instead of the impossible specified height 900. Ramp fixtures follow
  the actual slope. The plan emits 39 lights despite prose saying 38, and supplies no amber vault lamp; the build
  follows the plan. Some simple sectors are below 100 faces (the ramp has 18); all remain below 300.

The integrator should resolve the dressing, loot/action/tactics limitations and the plan/prose lamp discrepancy,
wire both Crown exits, and capture/review the tour before accepting the level's appearance.

## Pickups placement (2026-10-24)

20 colony satchels (2,610 faces; density capped at 20), no stat containers. Supplies are tucked around the
vestibule, Guard Hall, galleries, T1/T3 stores, service tunnel, pumps and coolant loop; the Core has none.

[`pickups.json`](pickups.json) records every position and event/cog id; the author exports them into the map.
The shared pickup mechanic supplies colours, opening, rewards and refill. All four batch-C maps are H3 and pass
`treasure = 6`: `evt.GetCurrentMapName()` currently returns the display name, while the shared automatic lookup
expects the filename. No shared mechanic or engine change is needed for this explicit setting.

The two incidental fixed floor-gold piles were removed under PICKUPS.md. The six themed cache items, chest contents and boss rewards remain.
No pickup models or textures needed stand-ins.

[`d06_pickups.yml`](d06_pickups.yml) tests actual clicks at the placed models and their resulting map variables. [`review_tour_pickups.yml`](review_tour_pickups.yml) supplies the storeroom and two supply views for the
integrator; captures remain with the integrator. `review/pickups/placement_checks.json` records floor support,
clear footprints and unchanged compiled geometry. Build and scenario logs are in
`output/hesper_stage/logs/pickups_batch_c_20261024/`.

Validation: the four builds and stage passed; all **17 batch-C scenarios** and the complete
`rebuild_all.sh --scenarios-only` sweep (**93/93**, exit 0) passed. Both decoration-id and actor-size audits
report zero mismatches across 22 maps; the design audit has zero findings. Final suite logs:
`output/hesper_stage/logs/scenarios_082633_7/`; summary: `pickups_batch_c_20261024/validation_summary.json`.

## Walkability (2026-10-24)

Built, staged and gated: zero audit findings, no exceptions. The shared node author supplies 16-unit dais
stairs with solid side parapets, chamfered vestibule/hall/terminals/core and hipped ceilings. The octagonal
core's north-west cut preserves its service door; the heart column meets the raised crown. D6 retains its
coolant loop, shield panels and down ramp. Eight actor positions clear stairs, pipes, arc posts, pump flanges
and the T2 console; all identities, order, events, doors, cogs, arrivals and pickup order are preserved.
The survey records 10/19 non-orthogonal rooms, 11/19 sloped ceilings; floor light samples reach at most three.

All five scenarios pass: seven pursuits in `d06_walkability.yml` (245 steps), main path, loud path, hazards and
pickups. `review/walkability/` contains the audit, survey, light and invariant checks; logs are in
`output/hesper_stage/logs/walkability_batch_d/`. `review_tour_walkability.yml` is ready for the integrator's
capture; screenshots are unavailable in this sandbox. No new art or stand-ins were introduced.

Final batch-D sweep: `rebuild_all.sh --scenarios-only` **108/108 PASS, exit 0**. Decoration and actor-size
mismatches: zero. All five batch maps' staged walkability audits are zero and all five are gated.
Logs: `output/hesper_stage/logs/scenarios_174417_3622123/`; batch summary:
`output/hesper_stage/logs/walkability_batch_d/validation_summary.json`.
