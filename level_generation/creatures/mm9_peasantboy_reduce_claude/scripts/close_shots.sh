#!/bin/bash
# Hand shots c8-c10 aimed at the posed hands of Standing 0.5 s (+-0.26, 0.575, 0.05). Close viewer shots installed vs reduced (Peasant boy, from the Dwarf boy): arms, tunic hem front/back, Running hem, feet, Fidget arms (hands on the
# hips), shoulders from behind, AttackMelee, L hand outside, R hand outside, R hand front, hair from behind above.
# Usage: scripts/close_shots.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:front:skirt c2:Standing:0.5:rear:skirt c3:Running:0.2:quarter:skirt c4:Standing:0.5:quarter:feet c5:Fidget:1.5:quarter:arms c6:Standing:0.5:rear:shoulders c7:AttackMelee:0.6:quarter:body c8:Standing:0.5:front:body:0.62,0.62,0.25:0.265,0.576,0.04 c9:Standing:0.5:front:body:-0.62,0.6,0.3:-0.258,0.572,0.077 c10:Standing:0.5:front:body:-0.32,0.6,0.42:-0.258,0.572,0.077 c11:Standing:0.5:front:body:0.3,1.65,-0.7:0.0,1.22,-0.05"
for m in ${1:-inst_a red_a inst_b red_b inst_e red_e}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_peasantboy_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
