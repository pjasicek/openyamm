#!/bin/bash
# scripts/poll.sh <job>: wait for a Meshy job, download it
source /home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_lizardorc_claude/scripts/env.sh; cd $REPO
for i in $(seq 1 30); do r=$(python3 tools/creature_meshy.py --project $P --token $TOKEN poll --job $1 --wait-seconds 45 2>&1 | cut -c1-120 | tail -1); echo "$r" | grep -q -E "SUCCEEDED|FAILED|EXPIRED|CANCELED" && break; done; echo "$r"
python3 tools/creature_meshy.py --project $P --token $TOKEN download --job $1 2>&1 | cut -c1-200 | tail -1
