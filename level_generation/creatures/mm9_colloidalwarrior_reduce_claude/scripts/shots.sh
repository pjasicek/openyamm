#!/bin/bash
# Viewer shots for the reduction review, every tier, installed and reduced (one shot script at a time):
# face sheet (front close-up, 3/4, true profile, low 3/4, party view from 22 deg), body (front, 3/4, back in Standing;
# Walking and AttackMelee 3/4, AttackRanged front). Usage: scripts/shots.sh [models...]  -> review/shots/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python; g=export/mm9_colloidalwarrior.glb
spec() { HEADUP=0.12,0.10,0.25 $G -W ignore ../mm9_ebora_claude/scripts/head_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
F=$(spec f Standing:0.5 "0,0.05,1:1.0" "0.75,0.1,0.75:1.05" "1,0.05,0:1.05" "0.7,-0.45,0.7:1.1" "0,0.42,1:3.2")
B="b0:Standing:0.5:front:body b1:Standing:0.5:quarter:body b2:Standing:0.5:rear:body b3:Walking:0.5:quarter:body b4:AttackMelee:0.4:quarter:body b5:AttackRanged:0.6:front:body"
for m in ${@:-a_inst a_red b_inst b_red c_inst c_red}; do
  for try in 1 2 3; do   # the viewer load times out now and then while other jobs load the machine: retry
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_colloidalwarrior_reduce_claude/review/viewer/?model=$m" $P/review/shots/$m $F $B 2>&1 | tail -1
  cd $P; [ "$(ls review/shots/$m 2>/dev/null | wc -l)" -ge 11 ] && break
  done
done
