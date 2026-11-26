#!/usr/bin/env bash
# A1's regression set at a Xeen merge point (devdocs/xeen/lanes/A1.md): the unit and runtime tests, MM6-MM9 start,
# map change, save, load and Town Portal, and the release scenarios, on the Xeen build tree. Two scenarios at a time.
#   tools/xeen/regressions.sh [game binary] [unit test binary]
# Prints one line per check and the failed ones' logs; exits non-zero when any fails. Logs stay in the folder printed
# at the end (a fresh temporary one).
set -uo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
game="${1:-$root/build-xeen/game/openyamm}"
tests="${2:-$root/build-xeen/tests/openyamm_unit_tests}"
runtime_tests="$(dirname "$tests")/openyamm_runtime_tests"
logs="$(mktemp -d "${TMPDIR:-/tmp}/xeen_regressions.XXXXXX")"
failed=0

scenarios=(
    tests/scenarios/worlds/mm7_roundtrip.yml
    tests/scenarios/worlds/mm8_roundtrip.yml
    tests/scenarios/worlds/mm9_roundtrip.yml
    tests/scenarios/mm9/mm9_no_teleport_maps.yml
    tests/scenarios/npcs/placed_npc_actor_outdoors.yml
    tests/scenarios/mm6/same_map_boat_closes_dialog.yml
    tests/scenarios/xeen/d4_same_map_ferry.yml
    tests/scenarios/xeen/d6_ambrose_flight.yml
    tests/scenarios/xeen/dd12_plate_after_load.yml
    devdocs/xeen/briefs/x2/L4/playtest_lake_dragons_leash.yml
    tests/scenarios/xeen/x2_fall_damage.yml
    tests/scenarios/xeen/dd17_belt_forward_held.yml
    tests/scenarios/equip_carried_item.yml
    tests/scenarios/mm7/hidden_monsters_not_killed.yml
    tests/scenarios/mm7/wine_cellar_vampire_leave.yml
    tests/scenarios/mm6/given_item_full_packs.yml
    tests/scenarios/xeen/given_item_held_kept.yml
    tests/scenarios/xeen/given_item_waiting_saved.yml
    tests/scenarios/mm7/magical_age_survives_rest.yml
    tests/scenarios/mm8/garrote_gorge_dragons_quest.yml
    tests/scenarios/xeen/loot_chest_closes.yml
    tests/scenarios/xeen/house_proprietor_once.yml
    tests/scenarios/xeen/shop_stock.yml
    tests/scenarios/xeen/key_npcs_unkillable.yml
    tests/scenarios/mm6/air_elemental_launch_height.yml
    tests/scenarios/xeen/x6_warzone_entrance.yml
    tests/scenarios/xeen/x6_cove_worms_pursue.yml
    tests/scenarios/xeen/d4_octopods_shore.yml
    tests/scenarios/xeen/p4_octopods_walks.yml
    tests/scenarios/xeen/dd15_lift_reload.yml
    tests/scenarios/xeen/fd04_rotating_door_reload.yml
)
while read -r line; do
    [ -n "$line" ] && scenarios+=("tests/scenarios/$line")
done < "$root/tests/scenarios/release/scenarios.txt"

if "$tests" > "$logs/unit_tests.log" 2>&1; then
    echo "PASS unit tests"
else
    echo "FAIL unit tests ($(grep -c 'TEST CASE:' "$logs/unit_tests.log") cases): $logs/unit_tests.log"
    grep -A3 'TEST CASE:' "$logs/unit_tests.log" | head -20
    failed=1
fi

# The world-facing runtime tests (the whole runtime suite crashes in "quick cast attacks instead ..." in build/ too).
if "$runtime_tests" --test-case='dimensional travel*,town portal*' > "$logs/runtime_tests.log" 2>&1; then
    echo "PASS runtime tests"
else
    echo "FAIL runtime tests: $logs/runtime_tests.log"
    grep -A3 'TEST CASE:' "$logs/runtime_tests.log" | head -20
    failed=1
fi

run_scenario()
{
    local scenario="$1"
    local name
    name="$(basename "$scenario" .yml)"
    mkdir -p "$logs/$name"
    if timeout 900 "$game" --user-data "$logs/$name" --headless-run-scenario "$root/$scenario" \
        --scenario-quiet --scenario-no-color > "$logs/$name.log" 2>&1; then
        echo "PASS $scenario"
    else
        echo "FAIL $scenario: $logs/$name.log"
        return 1
    fi
}

pids=()
for scenario in "${scenarios[@]}"; do
    run_scenario "$scenario" &
    pids+=($!)
    if [ "${#pids[@]}" -ge 2 ]; then
        wait "${pids[0]}" || failed=1
        pids=("${pids[@]:1}")
    fi
done
for pid in "${pids[@]}"; do
    wait "$pid" || failed=1
done

# Decision D-44: every world's model paths lie in engine/, the world or a declared dependency.
if python3 "$root/tools/xeen/model_dependencies.py" > "$logs/model_dependencies.log" 2>&1; then
    echo "PASS model dependencies"
else
    echo "FAIL model dependencies: $logs/model_dependencies.log"
    failed=1
fi

# The Xeen data gates (merge point 41): the quest audit, the key figures (unkillable, named, bodies) and every ranged
# model row's launch height against its drawn body.
# The fourth pin round's map gates (2026-11-26): rail ends held by something, no sky behind cut-out bars, basin-less
# fountains only in water, decorations not through walls, no monster penned behind openings its body cannot pass (D-185),
# the wild-land and rim rules of the outdoor maps (check_wild.py: rim.fin, kerbless hull tops under the land, D-192).
for gate in quests.py key_npcs.py check_actor_heights.py check_beam_ends.py "check_cutout_backing.py --all" \
    check_fountains.py "check_clipping.py --all" check_monster_fit.py "check_wild.py --check"; do
    script="${gate%% *}"
    # shellcheck disable=SC2086
    if python3 "$root/tools/xeen/$script" ${gate#"$script"} > "$logs/${script%.py}.log" 2>&1; then
        echo "PASS $gate"
    else
        echo "FAIL $gate: $logs/${script%.py}.log"
        failed=1
    fi
done

# Dungeon campfires (D-104, D-195): every open fire listed in common/campfires.py has its event in the L4 and in the
# installed map Lua, and no fire decoration is left unlisted.
if python3 "$root/level_generation/projects/xeen/common/campfires.py" --check > "$logs/campfires.log" 2>&1; then
    echo "PASS campfires.py --check"
else
    echo "FAIL campfires.py --check: $logs/campfires.log"
    failed=1
fi

echo "logs: $logs"
exit "$failed"
