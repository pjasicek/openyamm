#!/bin/bash
# Close viewer shots installed vs reduced (one shot script at a time): arms, skirt front/back, Running skirt, feet, AttackMelee arms
# (hand on the belly), shoulders from behind, CowerLoop, both hands outside + R hand front, hair from behind and in profile.
# Usage: scripts/close_shots.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:front:skirt c2:Standing:0.5:rear:skirt c3:Running:0.2:quarter:skirt c4:Standing:0.5:quarter:feet c5:AttackMelee:2.5:quarter:arms c6:Standing:0.5:rear:shoulders c7:CowerLoop:1.0:quarter:body c8:Standing:0.5:front:body:0.70,1.00,0.30:0.29,0.93,0.01 c9:Standing:0.5:front:body:-0.68,1.00,0.42:-0.29,0.91,0.12 c10:Standing:0.5:front:body:-0.20,0.97,0.52:-0.29,0.91,0.12 c11:Standing:0.5:front:body:0.25,1.90,-0.60:-0.01,1.68,-0.05 c12:Standing:0.5:front:body:0.62,1.70,0.02:-0.01,1.67,-0.02"
for m in ${1:-inst_nj red_nj}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_njam_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
