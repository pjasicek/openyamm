#!/bin/sh
# Polls and downloads Meshy jobs until all named jobs are done. Usage: scripts/poll_jobs.sh <token> <job>...
cd "$(dirname "$0")/../../../../.." || exit 1
P=level_generation/props/items_claude/view_model_weapons_20261114
T=$1; shift
for job in "$@"; do
  until [ -f "$P/meshy/$job/texture_urls_0_base_color.png" ]; do
    out=$(./tools/run_creature_meshy.sh --project $P --token $T poll --job "$job" --wait-seconds 30 2>&1 | tail -1)
    echo "$job $out" | cut -c1-200
    case "$out" in
      *SUCCEEDED*) ./tools/run_creature_meshy.sh --project $P --token $T download --job "$job" 2>&1 | tail -1 ;;
      *FAILED*|*CANCELED*|*EXPIRED*) echo "$job failed"; break ;;
    esac
  done
done
