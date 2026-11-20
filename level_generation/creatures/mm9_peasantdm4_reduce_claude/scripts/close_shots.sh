#!/bin/bash
# Close viewer shots installed vs reduced (PeasantDM4): arms, tunic skirt front/back, Running skirt, boots, Talk arms, shoulders
# from behind, Hit, L hand outside, R hand outside, R hand front, cap from behind above, beard from below 3/4, L sleeve and cuff.
# Usage: scripts/close_shots.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:front:skirt c2:Standing:0.5:rear:skirt c3:Running:0.2:quarter:skirt c4:Standing:0.5:quarter:feet c5:Talk:1.5:quarter:arms c6:Standing:0.5:rear:shoulders c7:Hit:0.6:quarter:body c8:Standing:0.5:front:body:0.62,0.55,0.30:0.32,0.47,0.05 c9:Standing:0.5:front:body:-0.66,0.55,0.30:-0.36,0.47,0.01 c10:Standing:0.5:front:body:-0.30,0.52,0.45:-0.36,0.47,0.01 c11:Standing:0.5:front:body:0.25,1.50,-0.45:0.0,1.15,-0.03 c12:Standing:0.5:front:body:0.22,0.82,0.42:0.0,0.93,0.08 c13:Standing:0.5:front:body:0.58,0.68,0.38:0.27,0.60,0.0"
for m in ${1:-inst_a red_a}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_peasantdm4_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
