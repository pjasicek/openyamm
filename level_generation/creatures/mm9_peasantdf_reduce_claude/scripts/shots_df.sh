#!/bin/bash
# Viewer shots for the reduction review (one shot script at a time; after ../mm9_peasantf3_reduce_claude/scripts/shots.sh):
# face sheet (front close-up, 3/4, true profile, low 3/4, party view; framed on the face by head_specs.py, head bone
# Bip01 Head, the viewer's head focus misframes this rig) and body (Standing front/3-4/back, Walking 3/4, Talk 3/4, Death 3/4),
# then close-ups: arms/sleeves, skirt front/back, Running skirt, feet, Talk arms, shoulders from behind, Hit, L hand outside,
# R hand outside, R hand front, hem from below.
# Usage: scripts/shots_df.sh [models] -> review/shots/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python
spec() { HEADBONE="Bip01 Head" HEADUP=0,0.07,0.09 $G -W ignore scripts/head_specs.py before/mm9_peasantdf1.glb "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
F=$(spec f Standing:0.5 "0,0.08,1:0.47" "0.75,0.1,0.75:0.48" "1,0.08,0:0.48" "0.7,-0.6,0.7:0.48" "0,0.42,1:1.05")
B="b0:Standing:0.5:front:body b1:Standing:0.5:quarter:body b2:Standing:0.5:rear:body b3:Walking:0.5:quarter:body b4:Talk:1.5:quarter:body b5:Death:1.2:quarter:body"
C="c0:Standing:0.5:quarter:arms c1:Standing:0.5:front:skirt c2:Standing:0.5:rear:skirt c3:Running:0.2:quarter:skirt c4:Standing:0.5:quarter:feet c5:Talk:1.5:quarter:arms c6:Standing:0.5:rear:shoulders c7:Hit:0.6:quarter:body c8:Standing:0.5:front:body:0.56,0.52,0.20:0.29,0.47,0.04 c9:Standing:0.5:front:body:-0.56,0.52,0.20:-0.28,0.47,0.04 c10:Standing:0.5:front:body:-0.14,0.50,0.33:-0.28,0.47,0.04 c11:Standing:0.5:front:body:0.30,0.08,0.55:0.0,0.30,0.0"
for m in ${@:-inst_d1a red_d1a}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 900 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_peasantdf_reduce_claude/review/viewer/?model=$m" $P/review/shots/$m $F $B $C 2>&1 | tail -1
  cd $P
done
