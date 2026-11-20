#!/bin/bash
# Close viewer shots installed vs reduced (Lich King): arms, coat front/back, Running coat, boots, AttackRanged arms, shoulders from
# behind, Hit, R hand on the staff (outside, below), L hand outside, chest medallions and buckle, knee medals and tabard, back
# medallions, L bracer, boots front. Usage: scripts/close_shots.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:front:skirt c2:Standing:0.5:rear:skirt c3:Running:0.2:quarter:skirt c4:Standing:0.5:quarter:feet c5:AttackRanged:0.47:quarter:arms c6:Standing:0.5:rear:shoulders c7:Hit:0.6:quarter:body"
C="$C c8:Standing:0.5:front:body:-0.62,0.88,0.38:-0.238,0.80,0.06 c9:Standing:0.5:front:body:0.60,0.82,0.45:0.219,0.77,0.17"
C="$C c10:Standing:0.5:front:body:0.0,1.12,0.80:0.0,1.08,0.15 c11:Standing:0.5:front:body:0.18,0.48,0.90:0.0,0.45,0.2"
C="$C c12:Standing:0.5:front:body:0.12,1.22,-0.75:0.0,1.18,-0.05 c13:Standing:0.5:front:body:0.72,0.95,0.12:0.24,0.9,0.05"
C="$C c14:Standing:0.5:front:body:0.0,0.28,0.78:0.0,0.10,0.15 c15:Standing:0.5:front:body:-0.40,0.45,0.40:-0.238,0.80,0.05"
for m in ${1:-inst_a red_a}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_lichking_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
