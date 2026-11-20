#!/bin/bash
# Run a command (usually `codex exec ...`) in one of sixteen shared Codex slots, so parallel creature agents together
# never run more than sixteen Codex sessions (the user raised the cap from four on 2026-10-30). Waits until a slot is free.
#
#     level_generation/creatures/claude_shared/codex_slot.sh codex exec ...
set -u
SLOTS_DIR="$(cd "$(dirname "$0")" && pwd)/locks/codex_slots"
mkdir -p "$SLOTS_DIR"
while true; do
    for slot in 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
        exec {fd}>"$SLOTS_DIR/slot$slot.lock"
        if flock -n "$fd"; then
            "$@"
            status=$?
            flock -u "$fd"
            exec {fd}>&-
            exit $status
        fi
        exec {fd}>&-
    done
    sleep 5
done
