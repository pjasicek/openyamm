#!/bin/bash
# Close viewer shots installed vs reduced (Yanmir, Standing 0.5 unless named): R fist outside / front, L hand outside / front,
# chest + mantle + necklace disks, belt and loincloth, back (mantle, hair), greaves and boots, staff head, crown from above,
# Running and Hit 3/4, back of the legs, left shoulder + bracer. Usage: scripts/close_shots.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c0:Standing:0.5:front:body:-1.25,1.40,0.25:-0.58,1.38,0.05 c1:Standing:0.5:front:body:-0.55,1.40,0.75:-0.56,1.38,0.05 c2:Standing:0.5:front:body:1.25,1.35,0.25:0.58,1.33,0.07 c3:Standing:0.5:front:body:0.60,1.35,0.80:0.58,1.33,0.07 c4:Standing:0.5:front:body:0.0,2.05,1.10:0.0,2.05,0.05 c5:Standing:0.5:front:body:0.10,1.35,1.20:0.0,1.35,0.05 c6:Standing:0.5:front:body:0.0,2.20,-1.30:0.0,2.20,-0.15 c7:Standing:0.5:front:body:0.70,0.55,1.10:0.0,0.50,0.0 c8:Standing:0.5:front:body:-0.60,2.25,1.10:-0.44,2.15,0.33 c9:Standing:0.5:front:body:0.40,3.30,0.80:0.0,2.70,0.0 c10:Running:0.2:quarter:body c11:Hit:0.6:quarter:body c12:Standing:0.5:front:body:0.30,0.90,-1.40:0.0,0.90,-0.10 c13:Standing:0.5:front:body:1.40,1.90,0.20:0.45,1.85,-0.05"
for m in ${1:-inst_a red_a}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_yanmir_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
