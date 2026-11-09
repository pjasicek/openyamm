#!/bin/bash
# Hand close-ups installed vs reduced (Markel Standing 0.5 hand joints: L 0.335,0.878,0.111; R -0.305,0.849,0.222; fingers ~8 cm lower)
# plus Talk/Conv1 hands. Usage: scripts/hand_shots.sh [models] -> review/shots_close/<model>/hN.png
cd "$(dirname "$0")/.."; P=$PWD
C="h0:Standing:0.5:front:body:0.75,0.89,0.39:0.34,0.82,0.13 h1:Standing:0.5:front:body:-0.71,0.88,0.55:-0.31,0.79,0.24 h2:Standing:0.5:front:body:-0.14,0.86,0.75:-0.31,0.79,0.24 h3:Standing:0.5:front:body:0.15,0.87,0.59:0.34,0.82,0.13"
for m in ${1:-inst_a red_a}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:${PORT:-8912}/level_generation/creatures/mm9_bjarni_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
