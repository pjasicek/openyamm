#!/bin/bash
# Close viewer shots of the goose headdress (fix pass, chart guard): goose head and eye from both sides, the scales below the
# beak from the front, 3/4 above, the band from the side, the back. Usage: scripts/hat_shots.sh [models] -> review/shots_hat/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python
C=$($G -W ignore scripts/close_specs.py before/mm9_honkf.glb \
  "h0:Standing:0.5:Bip01 Head:1,0.1,0.25:0.24:0,0.35,0.03" "h1:Standing:0.5:Bip01 Head:-1,0.1,0.25:0.24:0,0.35,0.03" \
  "h2:Standing:0.5:Bip01 Head:0,0.25,1:0.32:0,0.27,0.02" "h3:Standing:0.5:Bip01 Head:0.6,0.7,0.6:0.36:0,0.25,0" \
  "h4:Standing:0.5:Bip01 Head:1,0.05,0.3:0.3:0,0.18,0" "h5:Standing:0.5:Bip01 Head:0.2,0.4,-1:0.36:0,0.24,0" 2>/dev/null | grep -v Unexpected | tr '\n' ' ')
for m in ${1:-inst_a red_a inst_b red_b}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 900 node level_generation/creatures/mm9_honkf_reduce_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_honkf_reduce_claude/review/viewer/?model=$m" $P/review/shots_hat/$m $C 2>&1 | tail -1
  cd $P
done
