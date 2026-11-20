#!/bin/bash
# PeasantHOM1 cameras (2026-11-05): c8-c10 hands, c11 hair from behind above, c12 L cuff, c13 chest toggle, c14 boots, c15 L fingers.
# Close viewer shots installed vs reduced (PeasantM7d, after PeasantM2d's close_shots.sh): arms, tunic front/back, Running,
# feet/boot cuffs, Talk arms, shoulders from behind, Hit, L hand outside, R hand outside, R hand front, hair from behind above,
# L cuff, chest lacing and belt buckle, boot cuffs front.
# Usage: scripts/close_shots.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:front:skirt c2:Standing:0.5:rear:skirt c3:Running:0.2:quarter:skirt c4:Standing:0.5:quarter:feet c5:Talk:1.5:quarter:arms c6:Standing:0.5:rear:shoulders c7:Hit:0.6:quarter:body c8:Standing:0.5:front:body:1.00,1.00,0.55:0.55,0.98,0.33 c9:Standing:0.5:front:body:-1.00,1.00,0.75:-0.54,0.96,0.45 c10:Standing:0.5:front:body:-0.35,1.00,1.00:-0.54,0.96,0.45 c11:Standing:0.5:front:body:0.30,2.45,-0.55:0.04,2.00,0.15 c12:Standing:0.5:front:body:0.85,1.25,0.55:0.50,1.20,0.14 c13:Standing:0.5:front:body:0.00,1.25,0.85:0.08,1.17,0.27 c14:Standing:0.5:front:body:0.15,0.45,1.00:0.00,0.30,0.05 c15:Standing:0.5:front:body:0.75,1.30,0.75:0.55,0.95,0.33"
for m in ${1:-inst_a red_a inst_b red_b inst_c red_c}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm9_peasanthom_reduce_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_peasanthom_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
