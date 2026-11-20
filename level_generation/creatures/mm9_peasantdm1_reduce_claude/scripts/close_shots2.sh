#!/bin/bash
# Close viewer shots placed by coordinates for the 1 m figure (the viewer's skirt/shoulder presets frame adult heights):
# tunic hem front and back, left sleeve outside, Running 3/4, Fidget2 (hand at the face), AttackMelee upper body, hair from above, Hit.
# Usage: scripts/close_shots2.sh [models] -> review/shots_close/<model>/c12..c17
cd "$(dirname "$0")/.."; P=$PWD
C="c12:Standing:0.5:front:body:0.0,0.45,0.75:0.0,0.40,0.02 c13:Standing:0.5:front:body:0.1,0.45,-0.75:0.0,0.40,-0.05 c14:Standing:0.5:front:body:0.75,0.62,0.25:0.2,0.60,-0.02 c15:Running:0.2:front:body:0.6,0.55,0.75:0.0,0.45,0.0 c16:Fidget2:1.0:front:body:0.5,0.75,0.7:0.0,0.65,0.0 c17:AttackMelee:0.6:front:body:0.6,0.70,0.8:0.0,0.60,0.0 c18:Standing:0.5:front:body:0.15,1.45,0.30:0.0,0.95,-0.02 c19:Hit:0.6:front:body:0.6,0.70,0.8:0.0,0.55,0.0"
for m in ${1:-inst_a red_a inst_b red_b}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_peasantdm1_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
