#!/bin/bash
# Runs a command in one of two bake slots, waiting for a free one. A Cycles bake takes 16 threads, so two at once use the
# whole machine: usage: level_generation/projects/mm9r_common/bake_slot.sh python3 .../dungeon/lighting.py <project>
locks="$(dirname "$(readlink -f "$0")")/locks"
mkdir -p "$locks"
while true; do
    for slot in 0 1; do
        exec 9>"$locks/bake_$slot.lock"
        if flock -n 9; then
            "$@"
            exit $?
        fi
    done
    sleep 20
done
