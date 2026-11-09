#!/bin/bash
# Poll until succeeded or failed, then download. Usage: scripts/meshy_wait.sh <job>  (repo root)
P=level_generation/creatures/mm9_peasantboy_claude; T=$(cat $P/LEASE_TOKEN.txt); J=$1
for i in $(seq 1 60); do
  o=$(python3 tools/creature_meshy.py --project $P --state creature_3d_progress.json --token $T poll --job $J --wait-seconds 40 2>&1 | tail -1)
  case "$o" in *SUCCEEDED*|*succeeded*) python3 tools/creature_meshy.py --project $P --state creature_3d_progress.json --token $T download --job $J 2>&1 | tail -1 | cut -c1-200; echo DONE $J; exit 0;; *FAILED*|*failed*|*CANCELED*|*Traceback*) echo FAIL $J "$o" | cut -c1-300; exit 1;; esac
done
echo TIMEOUT $J
