#!/bin/bash
# Viewer shots installed vs lined (three.js viewer on this project's review/viewer/, served by the repository HTTP server on
# PORT, default 8947): close-ups of every lined opening from outside (cuffs, collar/lapels, armpit, boot tops and cuffs, hem,
# buckle, hair) and the see-through gate's worst views per zone. Usage: scripts/shots.sh <set: close|worst|body> [models]
cd "$(dirname "$0")/.."; P=$PWD; G="../claude_shared/gltf_venv/bin/python -W ignore"; PORT=${PORT:-8947}
spec() { $G scripts/shot_specs.py before/mm9_bjarni.glb "$@" 2>/dev/null | grep -v Unexpected; }
case $1 in
close) S=$(spec \
  yoke_front:Standing:15:0:10:0.55:@0,1.40,0.12 yoke_side:Standing:15:270:5:0.6:@-0.18,1.40,0.05 yoke_back:Standing:15:180:10:0.6:@0,1.38,-0.12 \
  yoke_low_back:Standing:15:200:-35:0.6:@0,1.33,-0.12 yoke_low_front:Standing:15:20:-35:0.6:@0,1.36,0.12 \
  beads:Standing:15:15:5:0.35:@0,1.44,0.11 nape:Standing:15:180:-10:0.4:@0,1.52,-0.11 nape_low:Standing:15:160:-35:0.4:@0,1.52,-0.11 \
  hem_front:Standing:15:0:0:0.8:@0,0.85,0.08 hem_back:Standing:15:180:0:0.8:@0,0.85,-0.08 hem_low:Standing:15:30:-30:0.8:@0,0.85,0.08 \
  bootL_front:Standing:15:20:5:0.5:@0.15,0.38,-0.03 bootL_back:Standing:15:160:5:0.5:@0.15,0.38,-0.08 \
  bootR_front:Standing:15:340:5:0.5:@-0.15,0.38,-0.03 bootR_back:Standing:15:200:5:0.5:@-0.15,0.38,-0.08 \
  run_knees:Running:28:315:10:1.1:@0,0.42,0 run_knees2:Running:24:225:0:1.1:@0,0.42,0 \
  soles_s16:ArgumentSpeak16:0:0:20:1.0:@0,0.10,0 shot1a_yoke:ArgumentShot1A:240:45:10:0.9:@0,1.40,0 \
  fidget_yoke:Fidget:24:315:0:0.9:@0,1.40,0 applause_yoke:Applause:8:90:0:0.9:@0,1.40,0) ;;
worst) S=$(spec \
  torso_Death28:Death:28:315:0:2.6 collar_Death16:Death:16:315:0:2.6 sleeveL_Run0:Running:0:135:0:2.4 sleeveR_Run16:Running:16:225:0:2.4 \
  bootL_Run28:Running:28:315:0:2.4 bootR_S16:ArgumentSpeak16:4:0:20:2.4 trousersL_Run24:Running:24:225:0:2.4 head_Death12:Death:12:315:0:2.6 \
  torso_Dead0:Dead:0:45:0:2.6 torso_Cower:Cower:20:315:0:2.4) ;;
poke) S=$(spec \
  pk_applause8:Applause:8:90:0:0.6:@0.15,1.37,0.13 pk_shot1a32:ArgumentShot1A:32:90:0:0.6:@0.15,1.37,0.13 \
  pk_speak2_148:ArgumentSpeak2:148:90:0:0.6:@0.15,1.37,0.13 pk_shake48:ArgumentShake:48:0:20:0.6:@0,1.38,0.13 \
  pk_attack16:AttackMelee:16:0:20:0.6:@0,1.38,0.13 pk_cower0:Cower:0:0:20:0.6:@0,1.38,0.13 \
  pk_speak9_36:ArgumentSpeak9:36:90:0:0.6:@0.15,1.37,0.13 pk_fidget32:Fidget:32:315:20:0.6:@-0.15,1.37,0.13 \
  pk_talk36:Talk:36:135:0:0.6:@0.15,1.40,0.05 pk_speak16_92:ArgumentSpeak16:92:315:0:0.6:@-0.15,1.37,0.13) ;;
arms) S=$(spec \
  ar_applause60:Applause:60:330:10:0.6:@0.017,1.075,0.161 ar_applause60b:Applause:60:30:30:0.6:@0.017,1.075,0.161 \
  ar_applause72:Applause:72:330:10:0.6:@0.017,1.075,0.161 ar_fidget32:Fidget:32:330:0:0.6:@0,1.44,0.11 \
  ar_fidget32b:Fidget:32:30:10:0.6:@0,1.44,0.11) ;;
body) S=$(spec b_front:Standing:15:0:5:3.2 b_quarter:Standing:15:45:5:3.2 b_back:Standing:15:180:5:3.2 b_walk:Walking:12:45:5:3.2 \
  b_talk:Talk:45:45:5:3.2 b_death:Death:44:45:15:3.2 b_party:Standing:15:20:20:3.6 b_sit:Sit:20:30:10:3.2) ;;
esac
for m in ${@:2}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 900 node level_generation/creatures/mm9_bjarni_lining_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:$PORT/level_generation/creatures/mm9_bjarni_lining_claude/review/viewer/?model=$m" $P/review/shots/$1/$m $S 2>&1 | tail -1
  cd $P
done
