#!/bin/bash
# Close viewer shots of the reduced regions, installed vs reduced: hands (Standing, Conv3), crown 3/4 above, hair from behind,
# dress back, chest/apron front, left sleeve and bracelet from below, hem and feet in Walking, Death, braids, Fidget hair. Usage: scripts/close_shots.sh [models]
# -> review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python
C=$($G -W ignore scripts/close_specs.py before/mm9_peasantf7.glb \
  "c0:Standing:0.5:FHP L Hand:1,0.2,0.6:0.4" "c1:Standing:0.5:FHP R Hand:-1,0.2,0.6:0.4" \
  "c2:Conv3:2.0:FHP R Hand:-0.4,0.3,1:0.45" "c3:Standing:0.5:FHP Head:0.6,0.5,0.6:0.6:0,0.1,0" \
  "c4:Standing:0.5:FHP Head:0.25,0.2,-1:0.75:0,-0.12,0" "c5:Standing:0.5:FHP Spine2:0.2,0.15,-1:0.9" \
  "c6:Standing:0.5:FHP Spine2:0.3,0.1,1:0.6" "c7:Standing:0.5:FHP L Forearm:0.4,-1,0.6:0.45" \
  "c8:Walking:0.4:FHP L Foot:0.6,0.3,1:0.8:0,0.25,0" "c9:Death:1.0:FHP Spine2:0.5,1,0.5:1.1" \
  "c10:Standing:0.5:FHP Spine3:-0.5,0.1,1:0.5" "c11:Fidget:1.2:FHP Head:-0.7,0.3,-0.7:0.8:0,-0.1,0" 2>/dev/null | grep -v Unexpected | tr '\n' ' ')
for m in ${1:-inst_a red_a inst_b red_b}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 900 node level_generation/creatures/mm9_peasantf7_reduce_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_peasantf7_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -1
  cd $P
done
