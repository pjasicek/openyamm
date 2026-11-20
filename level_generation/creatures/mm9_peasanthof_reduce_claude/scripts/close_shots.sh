#!/bin/bash
# Close viewer shots installed vs reduced (half-orc women): arms, skirt front/back, Running skirt, feet, Talk arms, shoulders from
# behind, Hit, L hand outside, R hand outside, R hand front, hair/braids from behind above, chest/braids front.
# Usage: scripts/close_shots.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:front:skirt c2:Standing:0.5:rear:skirt c3:Running:0.2:quarter:skirt c4:Standing:0.5:quarter:feet c5:Talk:1.5:quarter:arms c6:Standing:0.5:rear:shoulders c7:Hit:0.6:quarter:body c8:Standing:0.5:front:body:0.85,1.10,0.45:0.50,1.00,0.18 c9:Standing:0.5:front:body:-0.82,1.08,0.60:-0.46,0.98,0.30 c10:Standing:0.5:front:body:-0.30,1.05,0.75:-0.46,0.98,0.30 c11:Standing:0.5:front:body:0.25,2.05,-0.55:0.0,1.65,-0.10 c12:Standing:0.5:front:body:0.0,1.55,0.75:0.0,1.45,0.15"
for m in ${1:-inst_a red_a inst_b red_b inst_c red_c}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_peasanthof_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
