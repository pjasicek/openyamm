#!/usr/bin/env bash
# Job lanes for parallel agents (several sessions converting MM9 maps at once):
#   lane.sh build                      cmake --build build --target openyamm -j25, one build at a time
#   lane.sh map <stem> <command...>    a heavy job for one map (a conversion, a scratch build): never the same map twice
#                                      at once, and at most SLOTS heavy jobs together (memory)
#   lane.sh job <command...>           a heavy job for no map (a game run, a scenario), in the same slots
# Locks live in level_generation/projects/mm9r_common/locks/ (lane_map_<stem>.lock, lane_slot_<n>.lock).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../../.." && pwd)"
locks="$here/locks"
SLOTS=${LANE_SLOTS:-6}

with_slot() {
    while true; do
        for ((n = 0; n < SLOTS; n++)); do
            exec {fd}>"$locks/lane_slot_$n.lock"
            if flock -n "$fd"; then
                set +e
                "$@"
                status=$?
                set -e
                flock -u "$fd"
                exec {fd}>&-
                return $status
            fi
            exec {fd}>&-
        done
        sleep 2
    done
}

case "${1:-}" in
    build)
        cd "$repo"
        flock -x "$locks/cmake_build.lock" cmake --build build --target openyamm -j25
        ;;
    map)
        stem="$2"
        shift 2
        cd "$repo"
        exec {mapfd}>"$locks/lane_map_$stem.lock"
        flock -x "$mapfd"
        with_slot "$@"
        ;;
    job)
        shift
        cd "$repo"
        with_slot "$@"
        ;;
    *)
        sed -n '2,8p' "$0"
        exit 2
        ;;
esac
