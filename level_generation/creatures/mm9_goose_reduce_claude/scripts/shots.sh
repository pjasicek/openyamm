#!/bin/bash
# Viewer shots for the goose reduction review, installed and reduced (Ram copy; one shot script at a time): face sheet f0-f4
# (front close-up, 3/4, true profile, low 3/4, party; framed on a point fixed in Xhead), body b0-b5 (Standing front/3-4/back,
# Walking 3/4, Running 3/4, Death 3/4) and bone-framed close shots of the cut regions: n (neck/breast side, neck from above-front),
# w (wing and flank side), u (belly from below-side), r (back and tail from the rear-above), t (tail side), h (feet).
# Usage: scripts/shots.sh [models]  -> review/shots/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python; g=before/mm9_goose.glb
spec() { BONE=Xhead HEADUP=0,0.0,0.015 $G -W ignore scripts/head_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
sp() { $G -W ignore scripts/bone_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
F=$(spec f Standing:0.5 "0,0.1,1:0.36" "0.75,0.1,0.75:0.36" "1,0.05,0:0.36" "0.7,-0.45,0.7:0.34" "0,0.42,1:2.2")
B="b0:Standing:0.5:front:body b1:Standing:0.5:quarter:body b2:Standing:0.5:back:body b3:Walking:0.25:quarter:body b4:Running:0.15:quarter:body b5:Death:1.6:quarter:body"
N=$(BONE=XneckC HEADUP=0,0.0,0.0 sp n Standing:0.5 "1,0.2,0.4:0.5" "0.4,0.8,0.8:0.5")
W=$(BONE=XCENTER HEADUP=0,0.05,0 sp w Standing:0.5 "1,0.15,-0.1:0.7")
U=$(BONE=XCENTER HEADUP=0,-0.1,0 sp u Standing:0.5 "0.9,-0.5,0.3:0.7")
R=$(BONE=Xback HEADUP=0,0,0 sp r Standing:0.5 "0.3,0.7,-1:0.7")
T=$(BONE=Xtail HEADUP=0,0,0 sp t Fidget:0.9 "1,0.2,-0.4:0.45")
H=$(BONE=Xfoot HEADUP=0,0.03,0 sp h Standing:0.5 "1,0.4,0.6:0.4")
for m in ${1:-inst_a red_a inst_b red_b}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 900 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_goose_reduce_claude/review/viewer/?model=$m" $P/review/shots/$m $F $B $N $W $U $R $T $H 2>&1 | tail -1
  cd $P
done
