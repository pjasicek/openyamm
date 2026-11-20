#!/bin/bash
# Close viewer shots installed vs reduced (PeasantDM2): arms, tunic hem front/back, Running hem, feet, Fidget arms (hands on the
# hips), shoulders from behind, AttackMelee, L hand outside, R hand outside, R hand front, hair from behind above.
# Usage: scripts/close_shots.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:front:skirt c2:Standing:0.5:rear:skirt c3:Running:0.2:quarter:skirt c4:Standing:0.5:quarter:feet c5:Fidget:1.5:quarter:arms c6:Standing:0.5:rear:shoulders c7:AttackMelee:0.6:quarter:body c8:Standing:0.5:front:body:0.55,0.46,0.22:0.24,0.40,0.07 c9:Standing:0.5:front:body:-0.55,0.46,0.18:-0.24,0.41,0.03 c10:Standing:0.5:front:body:-0.30,0.45,0.40:-0.24,0.41,0.03 c11:Standing:0.5:front:body:0.25,1.20,-0.60:0.0,0.88,-0.08"
for m in ${1:-inst_a red_a inst_b red_b}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_peasantdm2_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
