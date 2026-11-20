#!/bin/bash
# Close viewer shots installed vs reduced (Green Man, Standing 0.5 unless named): R hand on the staff outside (c0) / front (c2),
# L hand outside (c1) / front (c3), chest and mantle leaves (c4), leaf hood from behind (c5), leaf kilt front (c6) / back (c7),
# crown branches (c8), feet (c9), staff top (c10) and lower staff (c11), shoulder leaves (c12), Running (c13), Fidget2 beard stroke (c14).
# Usage: scripts/close_shots.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:front:body:-1.10,1.60,0.60:-0.47,1.52,0.25 c1:Standing:0.5:front:body:1.10,1.55,0.50:0.47,1.47,0.14 c2:Standing:0.5:front:body:-0.40,1.55,1.00:-0.47,1.52,0.25 c3:Standing:0.5:front:body:0.45,1.50,0.90:0.47,1.47,0.14 c4:Standing:0.5:front:body:0.0,1.95,1.00:0.0,1.90,0.15 c5:Standing:0.5:front:body:0.0,2.40,-0.90:0.0,2.30,0.0 c6:Standing:0.5:front:body:0.10,1.25,1.00:0.0,1.20,0.10 c7:Standing:0.5:front:body:0.0,1.30,-1.00:0.0,1.25,-0.10 c8:Standing:0.5:front:body:0.60,2.75,0.80:0.0,2.45,0.05 c9:Standing:0.5:front:body:0.20,0.35,1.00:0.0,0.15,0.0 c10:Standing:0.5:front:body:-0.90,2.30,1.20:-0.42,2.20,0.45 c11:Standing:0.5:front:body:-0.90,0.75,1.10:-0.40,0.70,0.40 c12:Standing:0.5:front:body:0.90,2.15,0.60:0.30,2.05,0.0 c13:Running:0.2:quarter:body c14:Fidget2:2.0:front:body:0.20,2.25,1.00:0.0,2.10,0.20"
for m in ${1:-inst red}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_greenman_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
