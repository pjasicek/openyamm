#!/bin/bash
# Viewer shots for the reduction review, installed and reduced (one shot script at a time; after
# mm9_lizardorc_reduce_claude/scripts/shots.sh): face sheet (front close-up, 3/4, true profile, low 3/4, party view), body
# (front, 3/4, back in Standing; Walking, Fidget, Death 3/4) and close-ups (review_specs.py close).
# Usage: scripts/shots.sh [models]  -> review/shots/<model>/, review/shots_close/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python; g=before/mm9_skraelos.glb
F=$($G -W ignore scripts/review_specs.py $g face 2>/dev/null | grep -v Unexpected)
C=$($G -W ignore scripts/review_specs.py $g close 2>/dev/null | grep -v Unexpected)
B="b0:Standing:0.5:front:body b1:Standing:0.5:quarter:body b2:Standing:0.5:rear:body b3:Walking:0.5:quarter:body b4:Fidget:1.5:quarter:body b5:Death:1.2:quarter:body b6:ResurrectSpell:2.5:quarter:body b7:Running:0.3:quarter:body"
for m in ${1:-inst_a red_a}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_skraelos_reduce_claude/review/viewer/?model=$m" $P/review/shots/$m $F $B 2>&1 | tail -3
  timeout 600 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_skraelos_reduce_claude/review/viewer/?model=$m" $P/review/shots_close/$m $C 2>&1 | tail -2
  cd $P
done
