#!/usr/bin/env bash
# Polls and downloads the five head retextures one after another (run from the repository root).
P=level_generation/creatures/mm6_hyd_texpass_claude
T=$(python3 -c "import json;print(json.load(open('$P/work/LEASE.txt'))['token'])")
for k in 1 2 3 4 5; do
  bash $P/scripts/tp_meshy_wait.sh $P $T head${k}_retexture_v1 | tail -3
done
echo WAIT_DONE
