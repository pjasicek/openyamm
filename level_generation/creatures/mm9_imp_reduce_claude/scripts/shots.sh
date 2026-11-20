#!/bin/bash
# Viewer shots for the reduction review, every tier, installed and reduced (one shot script at a time; after the Highwayman's
# shots.sh): face sheet f0-f4 (front close-up, 3/4, true profile, low 3/4, party view; framed on a point fixed in the head
# bone at the mouth's centre), body b0-b5 (Standing front/3-4/back, Walking 3/4, AttackMelee 3/4, Death 3/4) and close shots
# c0-c6 (arms and hands, back/shoulders, feet, AttackMelee2 arms, Hit chest, Dead, Running feet).
# Usage: scripts/shots.sh [models]  -> review/shots/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python; g=before/mm9_imp.glb
spec() { HEADUP=0.0,0.09,0.20 $G -W ignore scripts/head_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
F=$(spec f Standing:0.5 "0,0.08,1:0.8" "0.75,0.1,0.75:0.8" "1,0.08,0:0.85" "0.7,-0.45,0.7:0.8" "0,0.42,1:2.6")
B="b0:Standing:0.5:front:body b1:Standing:0.5:quarter:body b2:Standing:0.5:rear:body b3:Walking:0.5:quarter:body b4:AttackMelee:0.3:quarter:body b5:Death:1.2:quarter:body"
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:rear:shoulders c2:Standing:0.5:quarter:feet c3:AttackRanged:0.45:quarter:arms c4:Hit:0.9:quarter:shoulders c5:Dead:0.5:quarter:body c6:Running:0.2:quarter:feet"
for m in ${1:-inst_a red_a inst_b red_b inst_c red_c}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 900 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_imp_reduce_claude/review/viewer/?model=$m" $P/review/shots/$m $F $B $C 2>&1 | tail -1
  cd $P
done
