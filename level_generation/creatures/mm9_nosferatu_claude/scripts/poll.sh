#!/bin/bash
# scripts/poll.sh <job>: poll a Meshy job to the end and download it (repo root)
P=level_generation/creatures/mm9_nosferatu_claude; TOKEN=1c0e5e1540b7420dac9502a19ef8ac67
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do r=$(python3 tools/creature_meshy.py --project $P --token $TOKEN poll --job $1 --wait-seconds 45 2>&1 | cut -c1-120 | tail -1); echo "$r" | grep -q -E "SUCCEEDED|FAILED|EXPIRED|CANCELED" && break; done; echo "$r"
python3 tools/creature_meshy.py --project $P --token $TOKEN download --job $1 2>&1 | cut -c1-200 | tail -1
