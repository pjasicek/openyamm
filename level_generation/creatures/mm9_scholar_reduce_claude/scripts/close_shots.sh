#!/bin/bash
# Close viewer shots installed vs reduced (Scholar copy of the Wyrde's): arms, robe front/back, Running robe, feet, Fidget arms,
# shoulders/hair from behind, Hit, +x hand outside, -x hand front, stole + medallion front, stole + chain 3/4, cap from behind above, cuff
# and hem from below.
# Usage: scripts/close_shots.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:front:skirt c2:Standing:0.5:rear:skirt c3:Running:0.2:quarter:skirt c4:Standing:0.5:quarter:feet c5:Fidget:1.5:quarter:arms c6:Standing:0.5:rear:shoulders c7:Hit:0.6:quarter:body c8:Standing:0.5:front:body:0.62,0.95,0.30:0.29,0.82,0.04 c9:Standing:0.5:front:body:-0.20,1.05,0.45:-0.22,0.96,0.08 c10:Standing:0.5:front:body:0.0,1.35,0.55:0.0,1.33,0.05 c11:Standing:0.5:front:body:0.45,1.45,0.40:0.08,1.35,0.0 c12:Standing:0.5:front:body:0.25,2.25,-0.55:0.0,1.75,-0.05 c13:Standing:0.5:front:body:0.35,0.35,0.55:0.0,0.25,0.0"
for m in ${1:-inst_a red_a inst_b red_b}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_scholar_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -2
  cd $P
done
