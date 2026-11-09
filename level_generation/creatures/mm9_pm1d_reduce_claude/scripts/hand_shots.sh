#!/bin/bash
# Hand close-ups installed vs reduced (PeasantM1d Standing 0.5 hand joints: L 0.34,0.91,0.13; R -0.32,0.88,0.23; fingers ~8 cm lower)
# plus Talk/Conv1 hands. Usage: scripts/hand_shots.sh [models] -> review/shots_close/<model>/hN.png
cd "$(dirname "$0")/.."; P=$PWD
C="h0:Standing:0.5:front:body:0.75,0.92,0.40:0.34,0.85,0.14 h1:Standing:0.5:front:body:-0.72,0.92,0.55:-0.32,0.83,0.24 h2:Standing:0.5:front:body:-0.15,0.90,0.75:-0.32,0.83,0.24 h3:Standing:0.5:front:body:0.15,0.90,0.60:0.34,0.85,0.14"
for m in ${1:-inst_d red_d inst_c red_c}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_pm1d_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
