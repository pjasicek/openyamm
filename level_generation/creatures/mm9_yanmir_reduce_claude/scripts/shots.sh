#!/bin/bash
# Viewer shots for the reduction review, every tier, installed and reduced (one shot script at a time; after
# mm9_lizardorc_reduce_claude/scripts/shots.sh): face sheet (front close-up, 3/4, true profile, low 3/4, party view) and body
# (front, 3/4, back in Standing; Walking and AttackRanged 3/4; Death 3/4); Yanmir: one tier (a). Usage: scripts/shots.sh [models]  -> review/shots/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python; g=before/mm9_yanmir.glb
spec() { HEADBONE="Bip01 Head" HEADUP=${HEADUP:-0,0.15,0.27} $G -W ignore scripts/head_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
F=$(spec f Standing:0.5 "0,0.08,1:0.95" "0.75,0.1,0.75:0.98" "1,0.08,0:1.0" "0.7,-0.45,0.7:1.0" "0,0.42,1:2.6")
B="b0:Standing:0.5:front:body:0,1.40,5.6:0,1.30,0 b1:Standing:0.5:front:body:3.9,1.60,3.9:0,1.30,0 b2:Standing:0.5:front:body:0,1.50,-5.6:0,1.30,0 b3:Walking:0.5:front:body:3.9,1.60,3.9:0,1.30,0 b4:AttackRanged:0.4:front:body:3.9,1.60,3.9:0,1.30,0 b5:Death:1.2:front:body:3.6,1.9,3.6:0,0.8,0"
for m in ${1:-inst_a red_a}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_yanmir_reduce_claude/review/viewer/?model=$m" $P/review/shots/$m $F $B 2>&1 | tail -1
  cd $P
done
