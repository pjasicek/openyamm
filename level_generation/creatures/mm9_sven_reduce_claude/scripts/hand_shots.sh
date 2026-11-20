#!/bin/bash
# Hand close-ups installed vs reduced (PeasantM1 Standing 0.5 hand joints: L 0.27,0.90,0.11; R -0.25,0.88,0.23; fingers ~8 cm lower)
# plus Talk/Conv1 hands. Usage: scripts/hand_shots.sh [models] -> review/shots_close/<model>/hN.png
cd "$(dirname "$0")/.."; P=$PWD
C="h0:Standing:0.5:front:body:0.765,0.842,0.309:0.355,0.772,0.049 h1:Standing:0.5:front:body:-0.722,0.841,0.46:-0.322,0.751,0.15 h2:Standing:0.5:front:body:-0.152,0.821,0.66:-0.322,0.751,0.15 h3:Standing:0.5:front:body:0.165,0.822,0.509:0.355,0.772,0.049"
for m in ${1:-inst_a red_a inst_b red_b}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_sven_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
