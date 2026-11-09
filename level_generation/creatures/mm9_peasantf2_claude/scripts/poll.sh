#!/bin/bash
# scripts/poll.sh <job>: poll a Meshy job to the end and download it (repo root)
P=level_generation/creatures/mm9_peasantf2_claude; TOKEN=$(awk '{print $2}' $P/LEASE_TOKEN.txt)
for i in $(seq 1 40); do r=$(python3 tools/creature_meshy.py --project $P --token $TOKEN poll --job $1 --wait-seconds 45 2>&1 | cut -c1-160 | tail -1); echo "$r" | grep -q -E "SUCCEEDED|FAILED|EXPIRED|CANCELED" && break; done; echo "$r"
python3 tools/creature_meshy.py --project $P --token $TOKEN download --job $1 2>&1 | cut -c1-300 | tail -2
