#!/bin/bash
# Close-up viewer shots (installed and reduced, both tiers) of the reduced parts: hands, robe front/back/side, sleeves,
# boots, shoulders. Usage: scripts/close_shots.sh [models] -> review/close/<model>/c*.png
cd "$(dirname "$0")/.."; P=$PWD
S="c0:Standing:0.5:front:body:0,1.0,1.1:0,0.95,0.15 c1:Standing:0.5:front:body:-0.75,1.05,0.75:-0.22,0.95,0.15
c2:Walking:0.3:front:body:0,0.75,-1.6:0,0.6,-0.1 c3:Standing:0.5:front:body:0.45,0.6,1.4:0,0.5,0.1
c4:Fidget2:0.8:front:body:1.3,1.45,1.3:0,1.2,0 c5:Standing:0.5:front:body:0.5,0.4,1.0:0,0.25,0.1
c6:AttackRanged:0.6:front:body:0.6,1.6,-1.5:0,1.3,0 c7:Running:0.3:front:body:1.5,0.5,0.3:0,0.6,0"
for m in ${1:-inst_a red_a inst_b red_b}; do
  for k in 1 2 3; do
    cd /home/pjasicek/github/OpenYAMM
    timeout 900 node level_generation/creatures/mm9_lich_reduce_claude/scripts/viewer_shots.mjs \
      "http://127.0.0.1:8912/level_generation/creatures/mm9_lich_reduce_claude/review/viewer/?model=$m" $P/review/close/$m $S 2>&1 | tail -1
    cd $P; [ -f review/close/$m/c7.png ] && break
  done
done
