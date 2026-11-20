#!/bin/bash
# Viewer shots installed vs lined (three.js viewer on this project's review/viewer/, served by the repository HTTP server on
# PORT, default 8941): close-ups of every lined opening from outside (cuffs, collar/lapels, armpit, boot tops and cuffs, hem,
# buckle, hair) and the see-through gate's worst views per zone. Usage: scripts/shots.sh <set: close|worst|body> [models]
cd "$(dirname "$0")/.."; P=$PWD; G="../claude_shared/gltf_venv/bin/python -W ignore"; PORT=${PORT:-8941}
spec() { $G scripts/shot_specs.py before/mm9_pm1d.glb "$@" 2>/dev/null | grep -v Unexpected; }
case $1 in
close) S=$(spec \
  cuffL_out:Standing:15:60:10:0.45:@0.682,1.091,0.088 cuffL_low:Standing:15:90:-35:0.45:@0.682,1.091,0.088 \
  cuffR_out:Standing:15:300:10:0.45:@-0.679,1.092,0.084 cuffR_low:Standing:15:270:-35:0.45:@-0.679,1.092,0.084 \
  collar_front:Standing:15:0:15:0.55:@0,1.36,0.11 collar_side:Standing:15:300:10:0.55:@0,1.36,0.11 \
  armpitR:Standing:15:270:0:0.5:@-0.155,1.261,0.008 armpitR_back:Standing:15:225:0:0.5:@-0.155,1.261,0.008 \
  hem_front:Standing:15:0:0:0.9:@0,0.9,0.05 hem_back:Standing:15:180:0:0.9:@0,0.9,-0.05 hem_low:Standing:15:30:-30:0.9:@0,0.9,0.05 \
  buckle:Standing:15:20:5:0.45:@0.015,1.07,0.137 \
  bootL_front:Standing:15:20:5:0.6:@0.17,0.38,-0.02 bootL_back:Standing:15:160:5:0.6:@0.17,0.38,-0.02 \
  bootR_front:Standing:15:340:5:0.6:@-0.16,0.38,-0.02 bootR_back:Standing:15:200:5:0.6:@-0.16,0.38,-0.02 \
  run_knees:Running:12:150:0:1.2:@0,0.45,0 run_knees2:Running:24:210:0:1.2:@0,0.45,0 \
  hair_front:Standing:15:0:0:0.5:@0,1.68,0.05 hair_side:Standing:15:90:0:0.5:@0,1.68,0 hair_back:Standing:15:180:10:0.5:@0,1.68,-0.05 \
  hair_low:Standing:15:45:-25:0.5:@0,1.66,0.03 hair_party:Standing:15:20:20:0.9:@0,1.6,0.05) ;;
worst) S=$(spec \
  torso_Death28:Death:28:0:0:2.6 torso_Dead0:Dead:0:45:0:2.6 bootL_Run24:Running:24:225:0:2.4 bootR_Run12:Running:12:135:0:2.4 \
  trousersL_Run0:Running:0:0:0:2.4 trousersR_AM24:AttackMelee:24:315:0:2.4 head_Hit4:Hit:4:45:0:2.4 \
  sleeveL_Death24:Death:24:315:0:2.6 sleeveR_Death20:Death:20:0:0:2.6 bootR_Cower4:Cower:4:90:0:2.4 torso_Death28_low:Death:28:0:20:2.6) ;;
body) S=$(spec b_front:Standing:15:0:5:3.2 b_quarter:Standing:15:45:5:3.2 b_back:Standing:15:180:5:3.2 b_walk:Walking:12:45:5:3.2 \
  b_talk:Talk:45:45:5:3.2 b_death:Death:44:45:15:3.2 b_party:Standing:15:20:20:3.6) ;;
esac
for m in ${@:2}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 900 node level_generation/creatures/mm9_pm1d_lining_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:$PORT/level_generation/creatures/mm9_pm1d_lining_claude/review/viewer/?model=$m" $P/review/shots/$1/$m $S 2>&1 | tail -1
  cd $P
done
