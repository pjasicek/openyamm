#!/bin/bash
# Close viewer shots placed by coordinates for the 1 m Dwarf boy, scaled x 1.35 for the 1.37 m Peasant boy (the viewer's skirt/shoulder presets frame adult heights):
# tunic hem front and back, left sleeve outside, Running 3/4, Talk, AttackMelee upper body, hair from above, Hit.
# Usage: scripts/close_shots2.sh [models] -> review/shots_close/<model>/c12..c17
cd "$(dirname "$0")/.."; P=$PWD
C="c12:Standing:0.5:front:body:0.0,0.61,1.01:0.0,0.54,0.03 c13:Standing:0.5:front:body:0.14,0.61,-1.01:0.0,0.54,-0.07 c14:Standing:0.5:front:body:0.95,0.88,0.3:0.22,0.85,0.0 c15:Running:0.2:front:body:0.81,0.74,1.01:0.0,0.61,0.0 c16:Talk:1.0:front:body:0.68,1.01,0.94:0.0,0.88,0.0 c17:AttackMelee:0.6:front:body:0.81,0.94,1.08:0.0,0.81,0.0 c18:Standing:0.5:front:body:0.2,1.96,0.41:0.0,1.28,-0.03 c19:Hit:0.6:front:body:0.81,0.94,1.08:0.0,0.74,0.0"
for m in ${1:-inst_a red_a inst_b red_b inst_e red_e}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_peasantboy_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
