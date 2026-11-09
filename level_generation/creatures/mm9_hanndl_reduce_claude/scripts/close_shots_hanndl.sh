#!/bin/bash
# Close viewer shots installed vs reduced (Hanndl, 1.78 m; PeasantDM2's close_shots_dm2.sh): arms, tunic hem front/back,
# Running hem, feet, Fidget arms, shoulders from behind, AttackMelee, L hand outside, R hand outside, R hand front, hair from
# behind above, Death lying, Talk arms, belt front, boots front, collar/necklace front.
# Usage: scripts/close_shots_dm2.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:front:skirt c2:Standing:0.5:rear:skirt c3:Running:0.2:quarter:skirt c4:Standing:0.5:quarter:feet c5:Fidget:1.5:quarter:arms c6:Standing:0.5:rear:shoulders c7:AttackMelee:0.6:quarter:body c8:Standing:0.5:front:body:0.66,1.02,0.48:0.31,0.92,0.22 c9:Standing:0.5:front:body:-0.70,1.02,0.36:-0.32,0.94,0.13 c10:Standing:0.5:front:body:-0.28,0.98,0.56:-0.32,0.94,0.13 c11:Standing:0.5:front:body:0.30,1.98,-0.62:0.0,1.62,-0.05 c12:Death:1.9:quarter:body c13:Talk:1.3:quarter:arms c14:Standing:0.5:front:body:0.12,1.02,0.75:0.0,0.97,0.10 c15:Standing:0.5:front:body:0.20,0.36,0.85:0.0,0.25,0.05 c16:Standing:0.5:front:body:0.10,1.47,0.62:0.0,1.42,0.10"
for m in ${1:-inst_a red_a}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_hanndl_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
