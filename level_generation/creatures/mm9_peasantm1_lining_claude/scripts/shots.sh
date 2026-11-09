#!/bin/bash
# Viewer shots installed vs lined (three.js viewer on this project's review/viewer/, served by the repository HTTP server on
# PORT, default 8957): close-ups of every lined opening from outside (cuffs, collar/lapels, armpit, boot tops and cuffs, hem,
# buckle, hair) and the see-through gate's worst views per zone. Usage: scripts/shots.sh <set: close|worst|body> [models]
cd "$(dirname "$0")/.."; P=$PWD; G="../claude_shared/gltf_venv/bin/python -W ignore"; PORT=${PORT:-8957}
spec() { $G scripts/shot_specs.py before/mm9_peasantm1.glb "$@" 2>/dev/null | grep -v Unexpected; }
case $1 in
close) S=$(spec \
  cuffL_out:Standing:15:60:10:0.45:@0.61,1.058,0.093 cuffL_low:Standing:15:90:-35:0.45:@0.61,1.058,0.093 \
  cuffR_out:Standing:15:300:10:0.45:@-0.607,1.047,0.099 cuffR_low:Standing:15:270:-35:0.45:@-0.607,1.047,0.099 \
  collar_front:Standing:15:0:15:0.55:@0,1.45,0.09 collar_side:Standing:15:300:10:0.55:@0,1.45,0.09 collar_top:Standing:15:20:50:0.6:@0,1.47,0.0 \
  collar_back:Standing:15:180:15:0.55:@0,1.47,-0.12 \
  hipL:Standing:15:110:0:0.5:@0.18,0.982,-0.025 shirt_front:Standing:15:0:0:0.6:@0.006,1.211,0.113 shirt_side:Standing:15:330:0:0.6:@0.006,1.211,0.113 \
  hem_front:Standing:15:0:0:0.9:@0,0.95,0.12 hem_back:Standing:15:180:0:0.9:@0,0.95,-0.1 hem_low:Standing:15:30:-30:0.9:@0,0.95,0.12 \
  edge_quarter:Standing:15:45:0:0.8:@0.1,1.2,0.15 edge_quarterR:Standing:15:315:0:0.8:@-0.1,1.2,0.15 \
  hair_front:Standing:15:0:0:0.5:@0,1.68,0.05 hair_back:Standing:15:180:10:0.5:@0,1.68,-0.05 hair_low:Standing:15:45:-25:0.5:@0,1.66,0.03 \
  hair_party:Standing:15:20:20:0.9:@0,1.6,0.05) ;;
worst) S=$(spec \
  torso_Death28:Death:28:315:0:2.6 torso_Talk28:Talk:28:315:0:2.6 sleeveR_Death28:Death:28:0:20:2.6 collar_Death24:Death:24:0:0:2.6 \
  sleeveL_Bow48:Bow:48:90:0:2.4 head_Death24:Death:24:0:0:1.2:0,0.3,0 bootL_Bow40:Bow:40:0:0:2.4 sleeveL_AM8:AttackMelee:8:270:0:2.4 \
  torso_Dead0:Dead:0:45:20:2.6) ;;
body) S=$(spec b_front:Standing:15:0:5:3.2 b_quarter:Standing:15:45:5:3.2 b_back:Standing:15:180:5:3.2 b_walk:Walking:12:45:5:3.2 \
  b_talk:Talk:45:45:5:3.2 b_death:Death:44:45:15:3.2 b_party:Standing:15:20:20:3.6) ;;
esac
for m in ${@:2}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 900 node level_generation/creatures/mm9_peasantm1_lining_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:$PORT/level_generation/creatures/mm9_peasantm1_lining_claude/review/viewer/?model=$m" $P/review/shots/$1/$m $S 2>&1 | tail -1
  cd $P
done
