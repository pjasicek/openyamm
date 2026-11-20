#!/bin/bash
# Close viewer shots installed vs reduced (PeasantDM1; the Dwarf boy's close_shots.sh with DM3's coordinates): arms, hem front/back,
# Running hem, feet, Fidget arms, shoulders from behind, AttackMelee, L hand outside, R hand outside, R hand front, hair from
# behind above, hair from behind level, beard and collar from the side, Talk hands, Death body.
# Usage: scripts/close_shots_dm3.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:front:skirt c2:Standing:0.5:rear:skirt c3:Running:0.2:quarter:skirt c4:Standing:0.5:quarter:feet c5:Fidget:0.5:quarter:arms c6:Standing:0.5:rear:shoulders c7:AttackMelee:0.6:quarter:body c8:Standing:0.5:front:body:0.75,0.50,0.25:0.36,0.45,0.05 c9:Standing:0.5:front:body:-0.75,0.50,0.20:-0.37,0.44,0.0 c10:Standing:0.5:front:body:-0.40,0.50,0.45:-0.37,0.44,0.0 c11:Standing:0.5:front:body:0.25,1.35,-0.65:0.0,0.98,-0.08 c12:Standing:0.5:front:body:0.0,0.95,-0.62:0.0,0.95,-0.08 c13:Standing:0.5:front:body:0.45,0.92,0.40:0.0,0.88,0.06 c14:Talk:1.5:quarter:body c15:Death:1.6:quarter:body"
for m in ${1:-inst_a red_a inst_b red_b}; do
  cd /home/pjasicek/github/OpenYAMM
  for i in 1 2 3; do
    timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
      "http://127.0.0.1:8912/level_generation/creatures/mm9_peasantdm1_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
    [ -f $P/review/shots_close/$m/c15.png ] && break
  done
  cd $P
done
