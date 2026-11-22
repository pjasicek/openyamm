#!/bin/bash
# A lane's two game slots: runs "$@" while holding one of two lock files, waiting until a slot is free. Called
# through a lane's output/studio_cal/<lane>/locks/game_slot.sh link, the lane's locks there are used; called here,
# output/xeen_locks/game_slots/. Each game goes through tools/heavy.sh 6.
# Usage: game_slot.sh <command> [args...]   (the command's exit status is returned)
dir=$(dirname "$0")
root="$(cd "$(dirname "$(readlink -f "$0")")/../../../../.." && pwd)"
case "$(cd "$dir" && pwd -P)" in */level_generation/*) dir=$root/output/xeen_locks/game_slots; mkdir -p "$dir";; esac
while true; do
    for slot in 1 2; do
        exec {fd}>"$dir/game$slot.lock"
        if flock -n "$fd"; then
            "$root/tools/heavy.sh" 6 "$@"
            status=$?
            flock -u "$fd"
            exit $status
        fi
        exec {fd}>&-
    done
    sleep 5
done
