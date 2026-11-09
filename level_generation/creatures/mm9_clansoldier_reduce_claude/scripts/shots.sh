#!/bin/bash
# Clan Soldier: viewer shots for the reduction review, every tier, installed and reduced (one shot script at a time; after
# mm9_ebora_reduce_claude/scripts/shots.sh): face sheet (front close-up, 3/4, true profile, low 3/4, party view) and body
# (front, 3/4, back in Standing; Walking and AttackMelee 3/4). Usage: scripts/shots.sh [models]  -> review/shots/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python; g=before/mm9_clansoldier.glb
spec() { HEADUP=0,0.11,0.08 $G -W ignore scripts/head_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
F=$(spec f Standing:0.5 "0,0.08,1:0.55" "0.75,0.1,0.75:0.58" "1,0.08,0:0.6" "0.7,-0.45,0.7:0.6" "0,0.42,1:1.6")
B="b0:Standing:0.5:front:body b1:Standing:0.5:quarter:body b2:Standing:0.5:rear:body b3:Walking:0.5:quarter:body b4:AttackMelee:0.3:quarter:body"
for m in ${1:-a_before a_c70 b_before b_c70 c_before c_c70}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm9_clansoldier_reduce_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_clansoldier_reduce_claude/review/viewer/?model=clan_$m" $P/review/shots/$m $F $B 2>&1 | grep -v "^ *at " | tail -6
  cd $P
done
