#!/bin/bash
# Forad extra close viewer shots: necklace front, R and L hand fingers close (side, f1/f2; front, f8/f9), ponytail and ties from behind, Applause (hands
# meet), Sit, ArgumentSpeak6 (hand on the body), Bow. Usage: scripts/close_shots_forad.sh [models] -> review/shots_close/<model>/f0..f7
cd "$(dirname "$0")/.."; P=$PWD
C="f0:Standing:0.5:front:body:0.0,1.45,0.42:0.0,1.43,0.08 f1:Standing:0.5:front:body:-0.52,0.84,0.40:-0.26,0.82,0.26 f2:Standing:0.5:front:body:0.52,0.84,0.24:0.25,0.82,0.10 f3:Standing:0.5:front:body:0.18,1.55,-0.50:0.0,1.50,-0.15 f4:Applause:1.5:front:body:0.4,1.3,1.0:0.0,1.1,0.1 f5:Sit:1.0:quarter:body f6:ArgumentSpeak6:2.0:quarter:arms f7:Bow:1.5:quarter:body f8:Standing:0.5:front:body:-0.30,0.84,0.62:-0.26,0.82,0.26 f9:Standing:0.5:front:body:0.32,0.84,0.48:0.25,0.82,0.10"
for m in ${1:-inst_a red_a}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:${VPORT:-8912}/level_generation/creatures/mm9_forad_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
