# The walkability test room (hes_walk_test.blv)

A one-room test map for the engine's monster movement: a 3 072 × 2 048 hall with a raised platform along its north wall
(96 above the floor, from y 1 300; a sheer edge no walker climbs) and a ramp up to it at the east end
(x 2 560-3 072, y 500-1 300). The floor is cut under the ramp and the platform. Map id 9108 (zone 1 reserve) in
`hesper_stage/maps.yml`; it has no entrance, only its scenario loads it.

## Build

```sh
cd level_generation/projects/hesper_walk_test
flock -s ../../../output/hesper_stage/locks/stage.lock blender --background --factory-startup --python author_walk_test_blender.py
cd ../../..
flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_walk_test/build_walk_test.py
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py
```

`rebuild_all.sh` builds it (`MAPS`: `walk_test`) and runs its scenario.

## Scenario

```sh
cd output/hesper_stage/scenario_run
flock -s ../locks/engine_build.lock flock -s ../locks/stage.lock ../../../build/game/openyamm --world hesper \
    --headless-run-scenario ../../../level_generation/projects/hesper_walk_test/walk_test.yml --scenario-no-color
```

[`walk_test.yml`](walk_test.yml), with the party on the platform:
- **The detour:** a Drudge 700 south of it on the floor plans a route, takes the ramp and reaches melee on the
  platform (feet at 96).
- **Out of reach below the edge:** a Drudge just below the edge, within the flat melee distance, does not strike up
  96 (Hesper's `world.yml` `actorCombat.meleeVerticalReach: 0.5`: half its height of 179 is less), so the party stays
  unhurt, and it goes round by the ramp.

Engine changes it covers (2026-10-26, design/kreegan_world/ENGINE.md): headless runs plan monster routes on the
calling thread (`OPENYAMM_SYNCHRONOUS_PATH_PLANS`, set by `main.cpp` for every headless command: before, a plan on a
worker landed only after the run had simulated many seconds, so headless pursuits never detoured), and the world's
melee vertical reach.
