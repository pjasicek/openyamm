#!/bin/bash
# Close viewer shots installed vs reduced (Krohn, Standing 0.5 unless named): R fist + glaive outside / front, L hand outside /
# front, chest (shoulder medallion, baldric, mail, tabard trim), ram buckle and belt, back (cape, hair, sword), knees + greaves,
# L bracer, crown from above, Running and Hit 3/4, back of the legs (socks, boot bands), R bracer, ankle bands front/back, glaive head, shaft collars.
# Usage: scripts/close_shots.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:front:body:-1.10,1.40,0.30:-0.42,1.33,0.08 c1:Standing:0.5:front:body:-0.42,1.38,0.80:-0.42,1.33,0.08 c2:Standing:0.5:front:body:1.20,1.35,0.20:0.55,1.30,-0.02 c3:Standing:0.5:front:body:0.55,1.35,0.70:0.55,1.30,-0.02 c4:Standing:0.5:front:body:0.0,2.05,1.25:0.0,2.05,0.20 c5:Standing:0.5:front:body:0.10,1.60,1.30:0.0,1.60,0.25 c6:Standing:0.5:front:body:0.0,2.10,-1.60:0.0,2.00,-0.30 c7:Standing:0.5:front:body:0.60,0.65,1.30:0.0,0.60,0.10 c8:Standing:0.5:front:body:1.20,1.60,0.60:0.50,1.55,0.00 c9:Standing:0.5:front:body:0.40,3.30,0.80:0.0,2.65,0.0 c10:Running:0.2:quarter:body c11:Hit:0.6:quarter:body c12:Standing:0.5:front:body:0.30,0.70,-1.40:0.0,0.70,-0.10 c13:Standing:0.5:front:body:-1.20,1.60,0.60:-0.45,1.55,0.05 c14:Standing:0.5:front:body:0.75,0.50,1.10:0.20,0.30,0.05 c15:Standing:0.5:front:body:0.55,0.50,-1.20:0.20,0.30,-0.10 c16:Standing:0.5:front:body:0.90,1.75,1.40:0.10,1.55,0.70 c17:Standing:0.5:front:body:-0.30,1.30,1.10:-0.40,1.15,0.10"
for m in ${1:-inst_a red_a}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm9_krohn_reduce_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_krohn_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
