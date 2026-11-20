#!/bin/bash
# scripts/poll_nh.sh <job>: pass 7, poll a Meshy job to the end and download it (repo root; lease token work/nh/lease_token.txt)
P=level_generation/creatures/mm9_fre_claude; TOKEN=$(cat $P/work/nh/lease_token.txt)
for i in $(seq 1 60); do r=$(python3 tools/creature_meshy.py --project $P --state creature_3d_progress.json --token $TOKEN poll --job $1 --wait-seconds 45 2>&1 | cut -c1-160 | tail -1); echo "$r" | grep -q -E "SUCCEEDED|FAILED|EXPIRED|CANCELED" && break; done; echo "$r"
python3 tools/creature_meshy.py --project $P --state creature_3d_progress.json --token $TOKEN download --job $1 2>&1 | cut -c1-300 | tail -2
