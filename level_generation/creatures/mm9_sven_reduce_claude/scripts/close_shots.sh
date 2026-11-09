#!/bin/bash
# Close viewer shots installed vs reduced (PeasantM1d copy of PeasantM2d's): arms, skirt front/back, Running skirt, feet, Talk arms, shoulders from
# behind, Hit, L hand outside, R hand outside, R hand front, hair from behind above, L bell cuff, chest trims and buckle.
# Usage: scripts/close_shots.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:front:skirt c2:Standing:0.5:rear:skirt c3:Running:0.2:quarter:skirt c4:Standing:0.5:quarter:feet c5:Talk:1.5:quarter:arms c6:Standing:0.5:rear:shoulders c7:Hit:0.6:quarter:body c11:Standing:0.5:front:body:0.25,1.95,-0.60:0.0,1.65,-0.05 c12:Standing:0.5:front:body:0.66,1.00,0.35:0.33,0.92,0.02 c13:Standing:0.5:front:body:0.0,1.14,0.55:0.0,1.06,0.12 c14:Standing:0.5:rear:body:0.0,1.12,-0.55:0.0,1.06,-0.12 c15:Standing:0.5:front:body:0.0,1.47,0.50:0.0,1.40,0.12 c16:Standing:0.5:front:body:0.34,1.68,0.04:0.09,1.62,-0.01 c17:Standing:0.5:front:body:-0.34,1.68,0.04:-0.09,1.62,-0.01 c18:Standing:0.5:front:body:-0.62,1.00,0.45:-0.30,0.90,0.12"
for m in ${1:-inst_a red_a inst_b red_b}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_sven_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
