#!/bin/bash
# Viewer shots for the reduction review, every tier, installed and reduced (one shot script at a time): face sheet (front close-up,
# 3/4, true profile, low 3/4, party view; framed on a point fixed in Bip01 Head, child scale) and body (front, 3/4, back in Standing;
# Walking and Talk 3/4; Death 3/4). Usage: scripts/shots.sh [models]  -> review/shots/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python; g=before/mm9_peasantgirl.glb
spec() { HEADBONE='Bip01 Head' HEADUP=${HEADUP:-0,0.0,0.09} $G -W ignore scripts/head_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
F=$(spec f Standing:0.5 "0,0.04,1:0.42" "0.75,0.06,0.75:0.44" "1,0.04,0:0.46" "0.7,-0.45,0.7:0.46" "0,0.5,1:1.6")
B="b0:Standing:0.5:front:body b1:Standing:0.5:quarter:body b2:Standing:0.5:rear:body b3:Walking:0.5:quarter:body b4:Talk:1.5:quarter:body b5:Death:1.2:quarter:body"
for m in ${1:-inst_g2 red_g2 inst_g3 red_g3 inst_g1e red_g1e}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_peasantgirl_reduce_claude/review/viewer/?model=$m" $P/review/shots/$m $F $B 2>&1 | tail -1
  cd $P
done
