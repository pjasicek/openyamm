#!/bin/bash
# poll + download. Usage (repo root): scripts/meshy_wait.sh <job>
P=level_generation/creatures/mm9_colloidalwarrior_claude; T=$(cat $P/work/token); J=$1
for i in $(seq 1 40); do r=$(python3 tools/creature_meshy.py --project $P --token $T poll --job $J --wait-seconds 45 2>&1 | tail -1); s=$(echo "$r" | grep -o '"status": *"[A-Z_]*"' | head -1); echo "$s"; case "$s" in *SUCCEEDED*) break;; *FAILED*|*CANCELED*) echo "$r"|cut -c1-300; exit 1;; esac; done
python3 tools/creature_meshy.py --project $P --token $T download --job $J 2>&1 | tail -1 | cut -c1-200
