# Hesper: D1 Starport Terminal (`hes_d01.blv`)

The first real dungeon and quest M2 (Dead Terminal), built to its
[build document](../../../design/kreegan_world/zone1/dungeons/D1_STARPORT_TERMINAL.md). Rooms, links, markers and
lights are the `d1` plan of `design/kreegan_world/zone1/dungeons/make_dungeon_plans.py`. The geometry comes from the
shared Hesper indoor kit (`../hesper_stage/blv_kit.py`, the Blender side) and `../hesper_stage/blv_build.py` (the
compile, scene and Lua side), which D2 uses too.

## Build

```sh
(cd level_generation/projects/hesper_d01 && flock -s ../../../output/hesper_stage/locks/stage.lock \
 timeout 1800 blender --background --factory-startup --python author_d01_blender.py)
flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_d01/build_d01.py              # compile, scene, Lua -> runtime/worlds/hesper
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py                # install into the shared Hesper stage (id 9103)
flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_out1/build_out1.py            # only when the arrival moved: event 11 reads it
```

- `author_d01_blender.py` writes `source/`: the ground floor (vestibule, Concourse in three sectors, Customs,
  Security, the Baggage Claim and its two carousels, the Belt Tunnel, Lost Luggage behind its secret panel, the
  Sorting Floor and its conveyor pits,
  Maintenance, the Tower Stair Hall), the octagonal Control Tower at 768, and the basement at −768 (the service
  corridor, the Freight Lift shaft, the Power Plant's catwalks over its pit at −1 280, Drone Control). Every room has
  64-thick walls and reveals: the indoor renderer draws both sides of a face, so rooms never share a wall plane.
- `semantic.json` carries what the build needs and what later passes need: the arrivals, the door ids, the chest
  events and the monster pack anchors; the build expands these into placed actors.
- `build_d01.py` compiles the BLV, checks every face event is bound and the door ids match, and writes the scene and
  Lua (handlers in `source/hes_d01.handlers.lua`; the exit is Starport Reach's `terminal_arrival` from
  `out1_build.json`).
- Textures: the D0 Colonial set (design/kreegan_world/art/textures_d0/blv) and the Terminal set
  (design/kreegan_world/art/textures_interiors/masters, `hc*`).

## Look and test

```sh
flock -s output/hesper_stage/locks/stage.lock \
 flock -s output/hesper_stage/locks/engine_build.lock ./tools/run_game.sh --isolated d1 --world hesper --map hes_d01.blv \
    --assets "$PWD/output/hesper_stage/assets_editor_dev" \
    --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d01/review_tour_01.yml" --seconds 0
```

`review/build01/sheet.jpg` is the first tour. `power_and_exit.yml` (run from `output/hesper_stage/scenario_run`) plays
M2 through: the emergency lift ride, the breakers 2, 3, 1, the Drone Control seal, the console's QBit 100002 (M2 done;
it clears 100202, M2 given), Aster's relay post (event 3: her first words, P4's `relay_d01` since 2026-10-23, M3 given
100203 unless M3 is done), the glass doors out to Starport Reach and the Lift Head down to the Undervault. It passes.
Event 23's text reads "the drones that patrol Landfall's walls" (D1's Texts, 2026-10-23). After Tear it out (100034)
the relay post is dead again (follow-up 35). `chests_and_cache.yml` (2026-10-23, follow-ups 28 and 44): chest A holds
the Drone Control Duty Log (11373, a readable: its text in `hesper_stage/items.yml`), an Engram and two Shield Cells
(the Militia Warrant waits for its staging), and the new cache on the Power Plant's north catwalk before Drone Control
(event 15, chest 6) two Shield Cells and a Stim. It passes. `blv_build.build` takes fixed chest contents.

## Status (2026-10-23)

Built: the whole plan, seven doors, the breaker puzzle (map variables 1–3, light group 1, cog 110 on the departure
board, cogs 101–103 on the breaker cabinets), the arcing plate, seven chests (chest A and the cache fixed, the rest random H1). Not yet: chest B's fixed items, the Hacking terminals (their handlers remain placeholders),
sounds.

## Monsters (2026-10-23)

The build places **42 actors** from the twelve plan marks: 25 Seeker Drones (including the nest of six and the
power gang's three), eight Acid Crawlers, four Starport Turrets, four Drudges and the Custodian. All are level
60–90. Encounter slots 1/2 identify Drones/Crawlers; their counts are zero because the plan's explicit packs supply
the population. `d01_build.json` records every native actor, group, position and sector. Geometry and arrivals
were preserved; this pass did not rebuild another map.

Groups follow the pack order, 1–12. Group 11 starts hidden and appears when the third correct breaker restores
power, once per map lifetime. The two vent packs (groups 5/9) appear within 600 of their plan marks. Group 12 is
the Custodian, posted with the staged 1,000-unit leash and 2,500-point Light shield. His death sets map variable 4
and drops Aster Shard 1 (11478) plus an Engram Core (11332) once. Drone Control refuses completion until he dies;
the existing M2/M3 and Lift Head progression remains intact. Map variables 5/6 retain the vent wakes.

The four turrets guard immediately: D1 describes guards in Customs and the Power Plant, with no switch wake;
the shutter wake belongs to D0. This ambiguity in the fix prompt was raised during the build. Their staged
stationary/TrueAim/NeverStaggers and traverse tactics are preserved. The gang appears at its plan anchor facing
east; its subsequent movement uses native AI, which has no scripted eastward march command.

`d01_main_path.yml` checks the occupied route, gang state, shield breaking without body damage, the console's
live-boss refusal, real boss death, drops, persistence and the exits. `power_and_exit.yml` now kills the boss before
using the console. The existing chest test remains. After D1/D2's scenarios, run
`python3 level_generation/projects/hesper_d01/check_monsters.py`: it checks both maps' native floor/ceiling clearance,
pack counts, staged boss rules and actual saved visibility bits (the scenario's `actor_visible` cannot assert those).
The save check deliberately requires version 103; update it if the actor save prefix changes.

Existing approved models cover every monster; no new creature stand-ins were introduced. Shard/Core ground art
uses the stage's existing gem shapes. The Custodian's two-second sweep remains the explicitly unbound engine-queue
item in P1's creature acceptance and `design/kreegan_world/ENGINE.md`; the normal attack has its existing half-second
glow. Four-second shield-break stagger is also pending engine support. No engine code or creature bindings changed.

All focused scenarios and saved-state checks pass. The required desktop smoke was attempted minimized under both
shared locks but stopped before loading the map: `SDL_Init failed: No available video device` in
`/tmp/openyamm-desktop-d01_monsters_smoke-sqkk_4v0/game.log`. Thus model loading and visual/combat acceptance remain
unverified in this sandbox. The integrator captures `review_tour_monsters.yml`; use the main-path scenario's
**pre-boss powered save** to include the gang:

```sh
flock -s output/hesper_stage/locks/stage.lock flock -s output/hesper_stage/locks/engine_build.lock \
 ./tools/run_game.sh --isolated d01_monsters --world hesper \
 --save /tmp/openyamm_scenario_saves/hesper_d01_main_path/d01_after_power.oysav \
 --assets "$PWD/output/hesper_stage/assets_editor_dev" \
 --set debug.screenshot_tour_path="$PWD/level_generation/projects/hesper_d01/review_tour_monsters.yml" --seconds 0
```

Run headless checks minimized with shared stage and engine locks from `output/hesper_stage/scenario_run`, as in the
builder guide. Regression command: `level_generation/projects/hesper_stage/rebuild_all.sh --scenarios-only`.

The completed shared regression passed **76/76 scenarios**, exit 0, with no WIP failures. Summary: `output/hesper_stage/logs/d01d02_monsters_regression.log`. The final extended front-door round trips also pass in the focused logs (`monsters_hesper_d01_d01_main_path.log` and `monsters_hesper_d02_d02_main_path.log`). Design audit: zero findings; `assets_dev` status unchanged. Fixtures and scripted damage verify mechanics, not combat balance.

## Pickups placement (2026-10-24)

10 stim canisters; **15 colony satchels**, from 1,826 built faces (8 per 1,000, rounded and clamped to 6–20). Five canisters in Customs' northeast bonded supply corner, three at the west Concourse kiosk and two at the east kiosk. Satchels occupy side rooms and perimeter supply corners; none in Drone Control.

The author keeps the placements as `(room, event, x, y, z, facing)` rows and exports them in `semantic.json`
under `pickups`. Events equal cogs: containers 701–710, satchels/bundles 751–765. The stage installs the map's
`_pickups.lua` sprite overlay automatically. All models and full/empty variants already exist; no stand-ins.

The map passes `treasure = 3` to the shared helper (H1). Its default lookup expects a filename,
but `GetCurrentMapName()` returns the display title; the explicit tier avoids that failed lookup without engine changes.

[`pickups.yml`](pickups.yml) checks native clicks, each stat supply group where present, two separated satchel
spots, save/reload and a repeat click. Item-roll state is covered headlessly; delivery to the hand remains the
shared mechanic's desktop check. [`review_tour_pickups.yml`](review_tour_pickups.yml) has the supply store and two
satchel views, writing to `review/pickups/`. This sandbox cannot capture; the integrator runs the tour.

All four batch-A authors flush outputs and use `os._exit(0)` after export; run them under `timeout 1800` and the
shared stage lock. On this sandbox use `/snap/blender/current/blender` in place of the Snap `blender` launcher.

Focused checks passed: `pickups.yml` (28 steps), native event/cog/model bindings and floor placement;
geometry, actors, chests, doors and arrivals preserved. Logs: `output/hesper_stage/logs/pickups_batch_a/`.

Shared sweep: **92/93 pass**; only the other batch's `hesper_d04/d04_key_path` fails at step 12, also on
focused retry. All Batch A scenarios and both audits pass (zero decoration-id or actor-size mismatches).
Integrator handoff: `design/kreegan_world/WORK_PACKAGES/requests/P4.md`, pickups placement, batch A.

## Walkability (2026-10-24)

**Built, staged and gated:** the final staged audit reports zero findings with three furniture exceptions.
All five scenarios pass: `d01_walkability` (seven pursuits), `d01_main_path`, `power_and_exit`,
`chests_and_cache` and `pickups`. D1 and its new fight scenario are included in `rebuild_all.sh`.

The freight platform now fills its shaft and meets both landings flush over a 768-unit travel. The belt lip is
32 high. Both sorting pits have 16-unit stairs with parapets above the surrounding floor; the Plant pit has a
26.6-degree railed ramp with its underlying floor cut away. Tower flights use 16-unit risers under a sloped ceiling.
The vestibule, Customs, Security, Claim, Sorting, Maintenance and outer Concourse bays have chamfered corners;
hipped ceilings articulate the Concourse bays, vestibule, Customs, Claim and octagonal tower. The service corridor
keeps its endpoints and gains a 45-degree dogleg. Its wall lamps follow the new wall, and the upper stair lamps
now stand above the actual treads. All event/door/cog IDs, pickup order, arrivals and actor records are preserved.

The shape survey records 10/20 non-orthogonal rooms and 8/20 sloped ceilings. The deliberate furniture exceptions
are the two claim carousels and the tower console. `d01_walkability.yml` has seven isolated pursuits: the belt,
both sorting pits, the Plant ramp, Tower flights and both freight landings. Each requires the actor to cross the
repaired floor before getting within 400 units of the party. The existing route, chest and pickup scenarios remain
in the focused suite. Evidence is in `review/walkability/` and `output/hesper_stage/logs/walkability_batch_d/`.

`review_tour_walkability.yml` covers the fixed floors and reshaped rooms. This sandbox cannot capture screenshots;
the integrator runs the tour (the lower freight landing requires the lift down). No new art or stand-ins.

Final batch-D sweep: `rebuild_all.sh --scenarios-only` **108/108 PASS, exit 0**. Decoration and actor-size
mismatches: zero. All five batch maps' staged walkability audits are zero and all five are gated.
Logs: `output/hesper_stage/logs/scenarios_174417_3622123/`; batch summary:
`output/hesper_stage/logs/walkability_batch_d/validation_summary.json`.
