#!/bin/bash
# Close viewer shots installed vs reduced (PeasantF6): arms, skirt front/back, Running skirt, feet, Talk arms, shoulders/veil from
# behind, Hit, L hand outside, R hand outside, R hand front, hood and veil from behind above.
# Usage: scripts/close_shots.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:front:skirt c2:Standing:0.5:rear:skirt c3:Running:0.2:quarter:skirt c4:Standing:0.5:quarter:feet c5:Talk:1.5:quarter:arms c6:Standing:0.5:rear:shoulders c7:Hit:0.6:quarter:body c8:Standing:0.5:front:body:0.72,0.92,0.22:0.29,0.83,-0.06 c9:Standing:0.5:front:body:-0.70,0.92,0.22:-0.27,0.83,-0.05 c10:Standing:0.5:front:body:-0.18,0.90,0.42:-0.27,0.83,-0.05 c11:Standing:0.5:front:body:0.25,1.85,-0.55:0.0,1.55,-0.05"
for m in ${1:-inst_a red_a inst_b red_b}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_peasantf6_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
