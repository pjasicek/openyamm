#!/bin/bash
# Close viewer shots installed vs reduced (PeasantDM1; the Dwarf boy's close_shots.sh with DM1's coordinates: hands (Standing) as DM3, c18/c19 the forearm cuffs at x +-0.57 y 0.63, hair and beard 6-10 cm higher; c16/c17 fingertips): arms, hem front/back,
# Running hem, feet, Fidget arms, shoulders from behind, AttackMelee, L hand outside, R hand outside, R hand front, hair from
# behind above, hair from behind level, beard and collar from the side, Talk hands, Death body.
# Usage: scripts/close_shots_dm3.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:front:skirt c2:Standing:0.5:rear:skirt c3:Running:0.2:quarter:skirt c4:Standing:0.5:quarter:feet c5:Fidget:0.5:quarter:arms c6:Standing:0.5:rear:shoulders c7:AttackMelee:0.6:quarter:body c8:Standing:0.5:front:body:0.75,0.50,0.25:0.36,0.45,0.05 c9:Standing:0.5:front:body:-0.75,0.50,0.20:-0.37,0.44,0.0 c10:Standing:0.5:front:body:-0.40,0.50,0.45:-0.37,0.44,0.0 c11:Standing:0.5:front:body:0.25,1.45,-0.65:0.0,1.10,-0.05 c12:Standing:0.5:front:body:0.0,1.05,-0.62:0.0,1.05,-0.05 c13:Standing:0.5:front:body:0.45,0.98,0.40:0.0,0.95,0.06 c14:Talk:1.5:quarter:body c15:Death:1.6:quarter:body c16:Standing:0.5:front:body:0.50,0.62,0.28:0.36,0.40,0.05 c17:Standing:0.5:front:body:-0.32,0.36,0.36:-0.37,0.40,0.02 c18:Standing:0.5:front:body:0.95,0.72,0.30:0.56,0.63,0.03 c19:Standing:0.5:front:body:-0.95,0.72,0.25:-0.57,0.63,0.03"
for m in ${1:-inst_a red_a inst_b red_b}; do
  cd /home/pjasicek/github/OpenYAMM
  for i in 1 2 3; do
    timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
      "http://127.0.0.1:8912/level_generation/creatures/mm9_peasantdm1_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
    [ -f $P/review/shots_close/$m/c19.png ] && break
  done
  cd $P
done
