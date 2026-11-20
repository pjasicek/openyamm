#!/bin/bash
# Hand close-ups installed vs reduced (Tryggva Standing 0.5 hand joints: L 0.30,0.91,0.14; R -0.28,0.88,0.25; fingers ~8 cm lower)
# plus Talk/Conv1 hands. Usage: scripts/hand_shots.sh [models] -> review/shots_close/<model>/hN.png
cd "$(dirname "$0")/.."; P=$PWD
C="h0:Standing:0.5:front:body:0.71,0.92,0.40:0.30,0.85,0.14 h1:Standing:0.5:front:body:-0.68,0.92,0.56:-0.28,0.82,0.25 h2:Standing:0.5:front:body:-0.11,0.90,0.76:-0.28,0.82,0.25 h3:Standing:0.5:front:body:0.11,0.90,0.60:0.30,0.85,0.14"
for m in ${1:-inst_a red_a inst_b red_b}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_tryggva_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
