#!/bin/bash
# Viewer shots for the reduction review, every tier, installed and reduced (one shot script at a time; PeasantF8's shots.sh):
# face sheet (front close-up, 3/4, true profile, low 3/4, party view) and body (front, 3/4, back in Standing; Walking and Talk
# 3/4; Death 3/4). Usage: scripts/shots.sh [models]  -> review/shots/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python
spec() { HEADBONE="Bip01 Head" HEADUP=${HEADUP:-0,0.08,0.10} $G -W ignore scripts/head_specs.py $1 "${@:2}" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
B="b0:Standing:0.5:front:body b1:Standing:0.5:quarter:body b2:Standing:0.5:rear:body b3:Walking:0.5:quarter:body b4:Talk:1.5:quarter:body b5:Death:1.2:quarter:body"
for m in ${1:-inst_a red_a inst_b red_b inst_c red_c}; do
  g=before/mm9_peasanthof1.glb; [[ $m == *_c ]] && g=before/mm9_peasanthof2.glb
  F=$(spec $g f Standing:0.5 "0,0.08,1:0.62" "0.75,0.1,0.75:0.64" "1,0.08,0:0.66" "0.7,-0.45,0.7:0.66" "0,0.42,1:1.6")
  cd /home/pjasicek/github/OpenYAMM
  timeout 900 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_peasanthof_reduce_claude/review/viewer/?model=$m" $P/review/shots/$m $F $B 2>&1 | tail -1
  cd $P
done
