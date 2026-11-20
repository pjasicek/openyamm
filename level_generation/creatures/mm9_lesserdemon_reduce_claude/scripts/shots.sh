#!/bin/bash
# Viewer shots for the reduction review, installed and reduced (one shot script at a time; from mm9_highwayman_reduce_claude):
# face sheet (front close-up, 3/4, true profile, low 3/4, party view; target fixed in Xhead at the snout/brow centre),
# body (front, 3/4, back in Standing; Walking and AttackMelee 3/4; Death 3/4) and close-ups (talons, horns from behind and
# above, mouth open in AttackRanged). Usage: scripts/shots.sh [models]  -> review/shots/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python; g=before/mm9_lesserdemon.glb
spec() { HEADUP=0,-0.09,0.14 $G -W ignore scripts/head_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
F=$(spec f Standing:0.5 "0,0.05,1:1.1" "0.75,0.1,0.75:1.1" "1,0.05,0:1.2" "0.7,-0.45,0.7:1.15" "0,0.42,1:3.6")
H=$(spec h Standing:0.5 "-0.6,0.5,-0.6:1.4" "0,1,0.15:1.3")
M=$(spec m AttackRanged:0.45 "0.35,0.05,1:1.2")
B="b0:Standing:0.5:front:body b1:Standing:0.5:quarter:body b2:Standing:0.5:rear:body b3:Walking:0.5:quarter:body b4:AttackMelee:0.3:quarter:body b5:Death:1.5:quarter:body c0:Standing:0.5:quarter:arms c1:AttackMelee:0.3:front:arms"
for m in ${1:-inst red}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_lesserdemon_reduce_claude/review/viewer/?model=$m" $P/review/shots/$m $F $H $M $B 2>&1 | tail -1
  cd $P
done
