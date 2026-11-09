#!/bin/bash
# Close viewer shots installed vs reduced (peasant girls, child scale): c0 arms 3/4, c1 skirt front, c2 skirt back, c3 Running skirt,
# c4 feet, c5 Talk arms, c6 shoulders from behind, c7 Hit, c8 L hand outside, c9 R hand outside, c10 R hand front, c11 vest front,
# c12 vest 3/4, c13 bodice back, c14 hem front, c15 L cuff, c16 hair from behind, c17 hair from above 3/4.
# Usage: scripts/close_shots.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:front:skirt c2:Standing:0.5:rear:skirt c3:Running:0.2:quarter:skirt c4:Standing:0.5:quarter:feet c5:Talk:1.5:quarter:arms c6:Standing:0.5:rear:shoulders c7:Hit:0.6:quarter:body"
C="$C c8:Standing:0.5:front:body:0.55,0.62,0.15:0.24,0.55,0.03 c9:Standing:0.5:front:body:-0.55,0.62,0.15:-0.24,0.55,0.04 c10:Standing:0.5:front:body:-0.12,0.62,0.38:-0.24,0.55,0.04"
C="$C c11:Standing:0.5:front:body:0.0,0.86,0.48:0.0,0.84,0.1 c12:Standing:0.5:front:body:0.32,0.88,0.36:0.0,0.84,0.08 c13:Standing:0.5:front:body:0.0,0.86,-0.48:0.0,0.84,-0.05"
C="$C c14:Standing:0.5:front:body:0.0,0.25,0.6:0.0,0.18,0.1 c15:Standing:0.5:front:body:0.5,0.8,0.3:0.2,0.7,0.03 c16:Standing:0.5:front:body:0.0,1.15,-0.6:0.0,1.0,-0.1 c17:Standing:0.5:front:body:0.35,1.6,0.35:0.0,1.2,0.0"
for m in ${1:-inst_g2 red_g2 inst_g3 red_g3 inst_g1e red_g1e}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 900 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_peasantgirl_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
