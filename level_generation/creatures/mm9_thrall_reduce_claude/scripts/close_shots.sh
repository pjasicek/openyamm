#!/bin/bash
# Close viewer shots (arms/fists, skirt, feet, shoulders, R/L hand outside, R hand front, hair from behind) installed vs reduced. Usage: scripts/close_shots.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:front:skirt c2:Standing:0.5:rear:skirt c3:Running:0.2:quarter:skirt c4:Standing:0.5:quarter:feet c5:AttackMelee2:0.4:quarter:arms c6:Standing:0.5:rear:shoulders c7:Hit2:0.6:quarter:body c8:Standing:0.5:front:body:-0.92,0.95,0.58:-0.50,0.87,0.23 c9:Standing:0.5:front:body:0.94,0.97,0.68:0.50,0.89,0.31 c10:Standing:0.5:front:body:-0.40,0.92,0.78:-0.50,0.87,0.23 c11:Standing:0.5:front:body:0.25,1.85,-0.45:0.01,1.62,0.20"
for m in ${1:-inst_a red_a inst_c red_c}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_thrall_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
