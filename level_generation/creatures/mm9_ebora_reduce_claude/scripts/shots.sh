#!/bin/bash
# Viewer shots for the reduction review, every tier, installed and reduced (one shot script at a time):
# face sheet (front close-up, 3/4, true profile, low 3/4, party view from 22 deg), body (front, 3/4, back in Standing;
# Walking and AttackMelee 3/4). Usage: scripts/shots.sh  -> review/shots/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python; g=work/candidate_mp_i57.glb
spec() { $G -W ignore ../mm9_ebora_claude/scripts/head_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
F=$(spec f Standing:0.5 "0,0.08,1:0.30" "0.75,0.1,0.75:0.32" "1,0.08,0:0.32" "0.7,-0.45,0.7:0.34" "0,0.42,1:1.1")
B="b0:Standing:0.5:front:body b1:Standing:0.5:quarter:body b2:Standing:0.5:rear:body b3:Walking:0.5:quarter:body b4:AttackMelee:0.4:quarter:body"
for m in eb_inst eb_red s1_inst s1_red s2_inst s2_red s3_inst s3_red s4_inst s4_red; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_ebora_reduce_claude/review/viewer/?model=$m" $P/review/shots/$m $F $B 2>&1 | tail -1
  cd $P
done
