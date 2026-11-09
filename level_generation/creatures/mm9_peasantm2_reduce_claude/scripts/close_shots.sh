#!/bin/bash
# Close viewer shots installed vs reduced (PeasantM2): arms, skirt front/back, Running skirt, feet, Talk arms, shoulders from
# behind, Hit, L hand outside, R hand outside, R hand front, hair from behind above, L bell cuff, chest trims and buckle.
# Usage: scripts/close_shots.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:front:skirt c2:Standing:0.5:rear:skirt c3:Running:0.2:quarter:skirt c4:Standing:0.5:quarter:feet c5:Talk:1.5:quarter:arms c6:Standing:0.5:rear:shoulders c7:Hit:0.6:quarter:body c8:Standing:0.5:front:body:0.75,0.95,0.15:0.34,0.92,-0.02 c9:Standing:0.5:front:body:-0.75,0.95,0.30:-0.34,0.90,0.10 c10:Standing:0.5:front:body:-0.22,0.92,0.52:-0.33,0.90,0.10 c11:Standing:0.5:front:body:0.25,1.95,-0.60:0.0,1.65,-0.05 c12:Standing:0.5:front:body:0.62,1.15,0.32:0.31,1.05,-0.05 c13:Standing:0.5:front:body:0.0,1.22,0.55:0.0,1.12,0.10"
for m in ${1:-inst_a red_a inst_b red_b}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm2_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
