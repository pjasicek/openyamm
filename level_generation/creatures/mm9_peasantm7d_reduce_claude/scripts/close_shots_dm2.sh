#!/bin/bash
# Close viewer shots installed vs reduced (PeasantDM2, 1.22 m; after the Dwarf boy's close_shots.sh): arms, tunic hem front/back,
# Running hem, feet, Fidget arms, shoulders from behind, AttackMelee, L hand outside, R hand outside, R hand front, hair from
# behind above, Death lying, RubBeard hand on the beard, belt front, boots front.
# Usage: scripts/close_shots_dm2.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:front:skirt c2:Standing:0.5:rear:skirt c3:Running:0.2:quarter:skirt c4:Standing:0.5:quarter:feet c5:Fidget:1.5:quarter:arms c6:Standing:0.5:rear:shoulders c7:AttackMelee:0.6:quarter:body c8:Standing:0.5:front:body:0.72,0.48,0.30:0.37,0.43,0.07 c9:Standing:0.5:front:body:-0.72,0.46,0.25:-0.39,0.41,0.00 c10:Standing:0.5:front:body:-0.33,0.45,0.42:-0.39,0.41,0.00 c11:Standing:0.5:front:body:0.25,1.45,-0.65:0.0,1.08,-0.08 c12:Death:1.9:quarter:body c13:RubBeard:1.2:front:body:0.12,1.00,0.62:0.0,0.95,0.10 c14:Standing:0.5:front:body:0.10,0.66,0.62:0.0,0.60,0.08 c15:Standing:0.5:front:body:0.18,0.24,0.70:0.0,0.15,0.05"
for m in ${1:-inst_a red_a inst_b red_b}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm7d_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
