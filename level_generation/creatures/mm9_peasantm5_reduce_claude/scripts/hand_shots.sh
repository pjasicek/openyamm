#!/bin/bash
# Hand close-ups installed vs reduced (PeasantM1 Standing 0.5 hand joints: L 0.27,0.90,0.11; R -0.25,0.88,0.23; fingers ~8 cm lower)
# plus Talk/Conv1 hands. Usage: scripts/hand_shots.sh [models] -> review/shots_close/<model>/hN.png
cd "$(dirname "$0")/.."; P=$PWD
C="h0:Standing:0.5:front:body:0.68,0.91,0.37:0.27,0.84,0.11 h1:Standing:0.5:front:body:-0.65,0.91,0.53:-0.25,0.82,0.22 h2:Standing:0.5:front:body:-0.08,0.89,0.73:-0.25,0.82,0.22 h3:Standing:0.5:front:body:0.08,0.89,0.57:0.27,0.84,0.11"
for m in ${1:-inst_a red_a inst_b red_b}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm5_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
