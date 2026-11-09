#!/usr/bin/env bash
# Rebuild every Hesper map (plans, Blender sources, compile and Lua; then Starport Reach), install the stage, run
# the Hesper scenarios.
# Usage: level_generation/projects/hesper_stage/rebuild_all.sh [--no-scenarios | --scenarios-only]
# --scenarios-only runs every scenario against the current stage without rebuilding any map (logs in a run folder of
# its own): the regression check for builders while other maps are being built. Only the integrator runs the full
# rebuild while several builders work, since it re-authors every map in place.
# A scenario listed in WIP_SCENARIOS (a map still being built) still runs, but its failure is reported as WIP-FAIL
# and does not fail the run; the map's builder removes it from the list once it passes. Keep the list short.
set -euo pipefail
export OPENYAMM_START_MINIMIZED=1
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
LOGS="$ROOT/output/hesper_stage/logs"
[[ "${1-}" == "--scenarios-only" ]] && LOGS="$LOGS/scenarios_$(date +%H%M%S)_$$"
mkdir -p "$LOGS"
if [[ "${1-}" != "--scenarios-only" ]]; then
python3 design/kreegan_world/zone1/dungeons/make_dungeon_plans.py > /dev/null
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py > /dev/null      # decoration ids for new models
MAPS="d13 d12 d15 d09 d00 d01 d02 undervault d04 d05 d03 d08 d10 d11 d06 d07 d16 pickups_test walk_test"
# Author every map first: the builds read each other's arrivals (D2 and the Undervault their Water Works doors).
for name in $MAPS; do
    (cd "level_generation/projects/hesper_$name" && flock -s "$ROOT/output/hesper_stage/locks/stage.lock" blender --background --factory-startup \
        --python "author_${name}_blender.py" > "$LOGS/author_$name.log" 2>&1) \
        || { tail -20 "$LOGS/author_$name.log"; exit 1; }
    grep -q Traceback "$LOGS/author_$name.log" && { grep -A20 Traceback "$LOGS/author_$name.log"; exit 1; }
done
for name in $MAPS; do
    flock -s output/hesper_stage/locks/stage.lock python3 "level_generation/projects/hesper_$name/build_$name.py" | tail -1 | cut -c1-110
done
# Starport Reach last: its entrances and the Lift Head lead to the dungeons' arrivals.
flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_out1/build_out1.py > "$LOGS/build_out1.log" 2>&1 \
    || { tail -20 "$LOGS/build_out1.log"; exit 1; }
tail -1 "$LOGS/build_out1.log" | cut -c1-110
# The Scour: its doors read D3's, D4's and D8's arrivals and the Undervault's Water Works; theirs read out2_build.json.
flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_out2/build_out2.py > "$LOGS/build_out2.log" 2>&1 \
    || { tail -20 "$LOGS/build_out2.log"; exit 1; }
head -1 "$LOGS/build_out2.log" | cut -c1-110
python3 level_generation/projects/hesper_out2/make_scenarios.py > /dev/null   # poses and actor indices
# The Brood Spires: its doors read D5's, D9's and D11's arrivals; theirs read out3_build.json.
flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_out3/build_out3.py > "$LOGS/build_out3.log" 2>&1 \
    || { tail -20 "$LOGS/build_out3.log"; exit 1; }
head -1 "$LOGS/build_out3.log" | cut -c1-110
python3 level_generation/projects/hesper_out3/make_scenarios.py > /dev/null   # the scenarios' actor indices
# The Crown: its doors read D6's and D12's arrivals; theirs read out4_build.json.
flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_out4/build_out4.py > "$LOGS/build_out4.log" 2>&1 \
    || { tail -20 "$LOGS/build_out4.log"; exit 1; }
tail -1 "$LOGS/build_out4.log" | cut -c1-110
python3 level_generation/projects/hesper_out4/make_scenarios.py > /dev/null   # poses and actor indices
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py > /dev/null
fi
[[ "${1-}" == "--no-scenarios" ]] && exit 0
WIP_SCENARIOS=""
status=0
# Let queued restages finish, then hold one shared scope for the audits and the entire scenario suite.
while grep ":$(stat -c %i output/hesper_stage/locks/stage.lock) " /proc/locks | grep -q -- '->.*WRITE'; do
    sleep 1
done
exec 9<output/hesper_stage/locks/stage.lock
flock -s 9
exec 8<output/hesper_stage/locks/engine_build.lock
flock -s 8
# Every built map's decorations against decoration_ids.yml (a map built before an id changed draws wrong models).
if ! python3 level_generation/projects/hesper_stage/check_decoration_ids.py > "$LOGS/decoration_ids.log" 2>&1; then
    echo "FAIL decoration ids ($LOGS/decoration_ids.log)"; status=1
fi
# Every built map's placed actors against their monster rows (a map built before a row's height or radius changed
# draws and collides its actors at the old size).
if ! python3 level_generation/projects/hesper_stage/check_actor_sizes.py > "$LOGS/actor_sizes.log" 2>&1; then
    echo "FAIL actor sizes ($LOGS/actor_sizes.log)"; status=1
fi
# Where monsters walk (steps, flights, unreachable regions, pits, movers, actor spots): a report for every map; a
# failure fails the run for the maps already fixed (WALKABILITY_GATED, comma-separated). Add a map once its findings
# are fixed or allowlisted in walkability_allow.yml; gate them all when the 16 dungeons are done.
WALKABILITY_GATED="hes_d16,hes_d07,hes_d06,hes_d04,hes_d01,hes_d03,hes_d08,hes_d12,hes_d11,hes_d00,hes_d05,hes_d15,hes_d10"
if ! python3 level_generation/projects/hesper_stage/check_walkability.py --gate "$WALKABILITY_GATED" > "$LOGS/walkability.log" 2>&1; then
    echo "FAIL walkability ($LOGS/walkability.log)"; status=1
fi
tail -1 "$LOGS/walkability.log"
cd output/hesper_stage/scenario_run
# Every actor binding of worlds/hesper/models/actors.yml through the game's own model loader and binding rules
# (headless scenarios load no models, so a GLB the desktop refuses would pass them).
if ! timeout 300 ../../../build/game/openyamm --world hesper --headless-validate-actor-models \
        > "$LOGS/actor_models.log" 2>&1; then
    echo "FAIL actor models ($LOGS/actor_models.log)"; status=1
fi
grep "^Actor models" "$LOGS/actor_models.log"
for scenario in hesper_d01/d01_main_path hesper_d01/d01_walkability hesper_d02/d02_main_path hesper_d02/d02_drain_crawlers \
                hesper_d07/d07_main_path hesper_d07/d07_loud_path hesper_d07/d07_factory_and_mines \
                hesper_d07/d07_arcs hesper_d07/d07_front_and_charge hesper_d07/d07_walkability \
                hesper_out4/crown_entrances hesper_out4/crown_market hesper_out4/crown_edges hesper_out4/crown_ring hesper_out4/crown_cannon \
                hesper_out3/brood_round_trips hesper_out3/brood_acid_rain hesper_out3/brood_nest \
                hesper_out3/brood_turrets hesper_out3/brood_tablets hesper_out3/brood_collision \
                hesper_d13/d13_main_path hesper_d13/d13_override hesper_d13/d13_vent \
                hesper_d13/d13_charge hesper_d13/d13_round_trips hesper_d13/d13_collapse_reset hesper_d13/d13_smoke \
                hesper_d12/d12_smoke hesper_d12/d12_walkability hesper_d12/d12_main_path hesper_d12/d12_backdoor hesper_d12/d12_round_trips \
                hesper_d06/d06_main_path hesper_d06/d06_loud_path hesper_d06/d06_hazards hesper_d06/d06_walkability \
                hesper_d16/d16_main_path hesper_d16/d16_columns hesper_d16/d16_hazards hesper_d16/d16_walkability \
                hesper_d11/seedship_sabotage hesper_d11/d11_walkability hesper_d10/d10_main_path hesper_d10/d10_hacking_and_hazard hesper_d10/d10_walkability \
                hesper_d15/d15_main_path hesper_d15/d15_side_paths hesper_d15/d15_walkability \
                hesper_d08/d08_main_path hesper_d08/d08_hazards hesper_d08/d08_walkability \
                hesper_d09/brood_pits_descent hesper_d00/d00_mechanisms hesper_d00/d00_walkability hesper_d01/power_and_exit hesper_d01/chests_and_cache \
                hesper_d02/drain_and_water_works hesper_d02/chests_and_cache hesper_d03/d03_main_path hesper_d03/d03_walkability \
                hesper_d05/relay_spire_climb hesper_d05/d05_walkability \
                hesper_d04/d04_main_path hesper_d04/d04_key_path hesper_d04/d04_walkability \
                hesper_undervault/lift_round_trip hesper_undervault/bulkhead_and_tunnel hesper_undervault/bulkhead_open \
                hesper_undervault/houses_and_people hesper_out1/camp_and_homes hesper_out1/landfall_keepers hesper_out1/true_aim \
                hesper_out1/charge hesper_out1/frenzy \
                hesper_out1/arrival hesper_out1/crew_ramp_round_trip hesper_out1/landfall_defenders \
                hesper_out1/hostile_spawns hesper_out1/shields_relations hesper_out1/shield_followups \
                hesper_out1/building_collision hesper_out2/scour_edges hesper_out2/scour_exits \
                hesper_out2/scour_camps hesper_out2/scour_depot hesper_out2/scour_depot_hacked \
                hesper_out2/scour_harvester hesper_out2/scour_tablets hesper_out2/scour_collision \
                hesper_stage/tech_skills_landfall hesper_stage/talk_topics hesper_stage/cybernetics_teachers \
                hesper_d04/d04_pickups hesper_d05/d05_pickups hesper_d08/d08_pickups hesper_d09/d09_pickups \
                hesper_d06/d06_pickups hesper_d07/d07_pickups hesper_d16/d16_pickups hesper_d10/d10_pickups \
                hesper_d00/pickups hesper_d01/pickups hesper_d02/pickups hesper_d03/pickups \
                hesper_d11/d11_pickups hesper_d12/d12_pickups hesper_d13/d13_pickups hesper_d15/d15_pickups \
                hesper_stage/item_expansion hesper_stage/vreth_relic_pair hesper_pickups_test/pickups \
                hesper_walk_test/walk_test hesper_walk_test/engine_calls; do
    if timeout 300 ../../../build/game/openyamm --world hesper --headless-run-scenario \
        "../../../level_generation/projects/$scenario.yml" --scenario-no-color > "$LOGS/$(basename $scenario).log" 2>&1
    then
        echo "PASS $scenario"
        if [[ " $WIP_SCENARIOS " == *" $scenario "* ]]; then echo "     (passes: remove it from WIP_SCENARIOS)"; fi
    elif [[ " $WIP_SCENARIOS " == *" $scenario "* ]]; then
        echo "WIP-FAIL $scenario ($LOGS/$(basename $scenario).log; known failing, not gating)"
    else
        echo "FAIL $scenario ($LOGS/$(basename $scenario).log)"; status=1
    fi
done
exit $status
