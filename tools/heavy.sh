#!/usr/bin/env bash
# Runs one heavy job (a build, a lighting bake, a map build, a game run or playthrough) so that it cannot take the
# machine down: it waits until enough memory is free, then runs the job in its own cgroup scope with a hard memory
# cap and no swap, so a runaway job is killed alone instead of filling RAM and swap (the 2026-11-22 10:19 lock-up:
# 120 GB and swap full, a power cycle).
#
#   tools/heavy.sh <cap GB> <command...>
#   tools/heavy.sh 24 cmake --build build-xeen --target openyamm -j16
#   tools/heavy.sh 12 flock output/xeen_locks/bake.lock <bake command>
#   tools/heavy.sh 6 python3 tests/playthrough/xeen/run.py 59
#
# It starts the job only while MemAvailable >= cap + RESERVE_GB (default 24) and swap is less than half used,
# checking every 20 s. Caps by kind (AGENTS.md "Heavy jobs and memory"): C++ build 24 (-j16), Blender bake 16,
# oymap map build 8, one game run or playthrough 6, a Python tool 4.
set -euo pipefail
if [[ $# -lt 2 || ! "$1" =~ ^[0-9]+$ ]]; then
    echo "usage: tools/heavy.sh <cap GB> <command...>" >&2
    exit 2
fi
cap_gb=$1
shift
reserve_gb=${RESERVE_GB:-24}

mem_kb() { awk -v key="$1" '$1 == key":" {print $2}' /proc/meminfo; }

while true; do
    available_gb=$(( $(mem_kb MemAvailable) / 1048576 ))
    swap_total=$(mem_kb SwapTotal)
    swap_free=$(mem_kb SwapFree)
    if (( available_gb >= cap_gb + reserve_gb )) && (( swap_total == 0 || swap_free * 2 >= swap_total )); then
        break
    fi
    echo "heavy.sh: waiting for memory (${available_gb} GB available, need $((cap_gb + reserve_gb)))" >&2
    sleep 20
done

exec systemd-run --user --scope --quiet --collect -p MemoryMax="${cap_gb}G" -p MemorySwapMax=0 -- "$@"
