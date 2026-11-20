#!/bin/bash
# Finger close-ups installed vs reduced (Hanndl): R and L hands from outside, front and behind in Standing 0.5, fingers
# framed on the hand-and-fingertip centre (posed). Usage: scripts/finger_shots.sh [models] -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="h0:Standing:0.5:front:body:0.62,0.90,0.50:0.30,0.82,0.30 h1:Standing:0.5:front:body:0.32,0.86,0.72:0.30,0.82,0.30 h2:Standing:0.5:front:body:0.40,0.88,-0.05:0.30,0.82,0.30 h3:Standing:0.5:front:body:-0.66,0.92,0.42:-0.32,0.85,0.19 h4:Standing:0.5:front:body:-0.30,0.88,0.62:-0.32,0.85,0.19 h5:Standing:0.5:front:body:-0.42,0.90,-0.15:-0.32,0.85,0.19"
for m in ${1:-inst_a red_a}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_hanndl_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
