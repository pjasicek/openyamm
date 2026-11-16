#!/usr/bin/env bash
# Scene and cinematics overlays (devdocs/map_studio/S6_PLAN.md G1, G2, G5) on shipped maps, from the test mount in
# this folder (mount/worlds/<world>/maps/<stem>_scenetest.*), never from assets_dev. Usage, from anywhere:
#   tests/scenarios/scene_overlays/run.sh [path to openyamm]   (default build/game/openyamm)
# Each scenario runs headless with its own user-data folder under output/scene_overlays/run/ (logs beside them); the
# three save scenarios share one (saves), where they keep their saves (the game works in its user-data folder, so a
# scenario's relative save path is inside it). Exit code 1 when any scenario fails.
set -uo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
here="$root/tests/scenarios/scene_overlays"
game="${1:-$root/build/game/openyamm}"
mount="$here/mount"
work="$root/output/scene_overlays/run"
failed=0
cd "$root" || exit 1
mkdir -p "$work"

# run <scenario> <mount|plain> <user-data folder name> [a line the log must hold]
run()
{
    local name="$1" withMount="$2" userData="$work/$3" expectLine="${4:-}"
    local args=(--user-data "$userData" --headless-run-scenario "$here/$name.yml")
    [ "$withMount" = mount ] && args=(--extra-mount "$mount" "${args[@]}")
    mkdir -p "$userData"
    SDL_AUDIODRIVER=dummy "$game" "${args[@]}" > "$work/$name.log" 2>&1
    local status=$?

    if [ $status -eq 0 ] && { [ -z "$expectLine" ] || grep -qF "$expectLine" "$work/$name.log"; }; then
        echo "PASS $name"
    else
        echo "FAIL $name (exit $status; log $work/$name.log)"
        failed=1
    fi
}

run overlay_actor_item mount overlay_actor_item
run overlay_ladder mount overlay_ladder
run overlay_cinematics_new mount overlay_cinematics_new "6d02_scenetest.cinematics.yml"
run overlay_cinematics_replace mount overlay_cinematics_replace "isleofashes_scenetest.cinematics.yml"
# A save made without the overlay, loaded with it, saved again and loaded without it: the map starts afresh both times.
run save_before_overlay plain saves
run load_with_overlay mount saves "map 6d02.blv changed since the save; its state was reset"
run load_without_overlay plain saves "map 6d02.blv changed since the save; its state was reset"
exit $failed
