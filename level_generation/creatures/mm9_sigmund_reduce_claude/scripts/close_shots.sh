#!/bin/bash
# Close viewer shots installed vs reduced (Sigmund, Standing 0.5 unless named): hands outside (c0, c1) and front (c2, c3), gold collar
# front / back (c4, c5), belt + buckle (c6), bracers (c7, c8), boot lacing front / back (c9, c10), hair from behind above (c11),
# hauberk hem (c12), Running (c13), Applause hands (c14).
# Usage: scripts/close_shots.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:front:body:0.62,0.95,0.45:0.22,0.84,0.09 c1:Standing:0.5:front:body:-0.62,0.95,0.60:-0.22,0.83,0.18 c2:Standing:0.5:front:body:0.22,0.86,0.75:0.22,0.84,0.09 c3:Standing:0.5:front:body:-0.22,0.86,0.85:-0.22,0.83,0.18 c4:Standing:0.5:front:body:0.0,1.42,0.75:0.0,1.38,0.05 c5:Standing:0.5:front:body:0.0,1.45,-0.75:0.0,1.40,-0.05 c6:Standing:0.5:front:body:0.10,1.08,0.80:0.0,1.06,0.05 c7:Standing:0.5:front:body:0.75,1.05,0.35:0.25,1.0,0.05 c8:Standing:0.5:front:body:-0.75,1.05,0.45:-0.25,1.0,0.10 c9:Standing:0.5:front:body:0.25,0.35,0.95:0.0,0.30,0.0 c10:Standing:0.5:front:body:0.20,0.40,-0.95:0.0,0.35,-0.05 c11:Standing:0.5:front:body:0.30,1.75,-0.75:0.0,1.50,-0.10 c12:Standing:0.5:front:body:0.35,0.90,0.95:0.0,0.88,0.0 c13:Running:0.2:quarter:body c14:Applause:1.5:front:body:0.30,1.10,0.80:0.0,0.95,0.15"
for m in ${1:-inst red}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_sigmund_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
