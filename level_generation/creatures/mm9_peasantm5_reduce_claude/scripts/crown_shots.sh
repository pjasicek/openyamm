#!/bin/bash
# Crown-streak fix (2026-11-05): crown from behind above (c11), shoulders and hair from behind (c6), every model given; each model is
# loaded twice (the first load times out while other jobs run). Usage: scripts/crown_shots.sh [models] -> review/shots_crown/<model>/
cd "$(dirname "$0")/.."; P=$PWD
C="c11:Standing:0.5:front:body:0.25,1.95,-0.60:0.0,1.65,-0.05 c6:Standing:0.5:rear:shoulders c14:Standing:0.5:front:body:-0.25,1.95,-0.60:0.0,1.65,-0.05"
for m in ${1:-inst_a red_a inst_b red_b}; do
  cd /home/pjasicek/github/OpenYAMM
  for i in 1 2; do
    timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
      "http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm5_reduce_claude/review/viewer/?model=$m" $P/review/shots_crown/$m $C 2>&1 | grep SHOTS && break
  done
  cd $P
done
