#!/bin/bash
# Viewer shots for the fish reduction review, installed and reduced (goose copy; one shot script at a time). Every camera is
# framed on a point fixed in a bone (the clips carry the +0.41 m swimmer lift): face sheet f0-f4 (front close-up, 3/4, true
# profile, low 3/4, party; a point 7.5 cm in front of XCENTER = the head), body b0-b5 (Standing front/3-4/back, Walking 3/4,
# Running side, Death end 3/4) and close shots of the cut regions: c0/c1 flank left/right, c2 back and dorsal root from above,
# c3 belly and pelvic/anal roots from below, c4 tail stalk in Fidget, c5 nape and gill edge from above-front.
# Usage: scripts/shots.sh [models]  -> review/shots/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python; g=before/mm9_fish.glb
sp() { $G -W ignore scripts/bone_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
F=$(BONE=XCENTER HEADUP=0,0,0.075 sp f Standing:0.5 "0,0.1,1:0.17" "0.75,0.1,0.75:0.17" "1,0.05,0:0.17" "0.7,-0.45,0.7:0.16" "0,0.42,1:0.9")
B="$(BONE=XCENTER HEADUP=0,0,-0.01 sp b Standing:0.5 "0,0.1,1:0.6" "-0.7,0.25,1:0.6" "0,0.1,-1:0.6") $(BONE=XCENTER HEADUP=0,0,-0.01 sp b3x Walking:0.25 "-0.7,0.25,1:0.6") $(BONE=XCENTER HEADUP=0,0,-0.01 sp b4x Running:0.15 "1,0.1,0:0.6") $(BONE=XCENTER HEADUP=0,0,-0.01 sp b5x Death:2.3 "-0.7,0.6,1:0.6")"
C="$(BONE=XCENTER HEADUP=0,0,-0.02 sp c Standing:0.5 "1,0.1,-0.2:0.25" "-1,0.1,-0.2:0.25" "0.3,1,-0.5:0.27" "0.5,-1,0.2:0.27") $(BONE=Xtail HEADUP=0,0,0 sp c4x Fidget:0.9 "1,0.2,-0.3:0.18") $(BONE=XCENTER HEADUP=0,0.02,0.05 sp c5x Standing:0.5 "0.5,0.8,0.6:0.18")"
for m in ${1:-inst_a red_a}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 900 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_fish_reduce_claude/review/viewer/?model=$m" $P/review/shots/$m $F $B $C 2>&1 | tail -1
  cd $P
done
