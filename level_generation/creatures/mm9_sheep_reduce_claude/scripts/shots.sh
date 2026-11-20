#!/bin/bash
# Viewer shots for the sheep reduction review, installed and reduced (one tier, sheep_a; one shot script at a time; Cow copy):
# face sheet f0-f4 (front close-up, 3/4, true profile, low 3/4, party; framed on a point fixed in Xhead at the face centre),
# body b0-b5 (Standing front/3-4/back, Walking 3/4, Running 3/4, Death 3/4) and bone-framed close shots of the cut body:
# n (neck/chest side and from above-front), m (AttackMelee 0.15 = the ladder's worst frame, side), u (belly from below-side),
# r (back/rump from the rear-above), h/k (front and hind legs and hooves), t (tail).
# Usage: scripts/shots.sh [models]  -> review/shots/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python; g=before/mm9_sheep.glb
spec() { BONE=Xhead HEADUP=0,-0.01,0.0 $G -W ignore scripts/head_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
sp() { $G -W ignore scripts/bone_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
F=$(spec f Standing:0.5 "0,0.1,1:0.9" "0.75,0.1,0.75:0.9" "1,0.05,0:0.9" "0.7,-0.45,0.7:0.85" "0,0.42,1:3.0")
B="b0:Standing:0.5:front:body b1:Standing:0.5:quarter:body b2:Standing:0.5:back:body b3:Walking:0.5:quarter:body b4:Running:0.2:quarter:body b5:Death:1.6:quarter:body"
N=$(BONE=Xneckbase HEADUP=0,-0.1,0.05 sp n Standing:0.5 "1,0.2,0.2:0.9" "0.4,0.8,0.8:0.9")
M=$(BONE=XCENTER HEADUP=0,0,0 sp m AttackMelee:0.15 "1,0.25,0.3:1.6")
U=$(BONE=XCENTER HEADUP=0,-0.3,0 sp u Standing:0.5 "0.9,-0.4,0.3:1.0")
R=$(BONE=XbackC HEADUP=0,0,0 sp r Standing:0.5 "0.3,0.7,-1:1.3")
H=$(BONE=Xffoot HEADUP=0,0.1,0 sp h Standing:0.5 "1,0.3,0.6:0.6")
K=$(BONE=Xbfoot HEADUP=0,0.1,0 sp k Standing:0.5 "1,0.3,-0.6:0.6")
T=$(BONE=Xtail HEADUP=0,-0.05,-0.05 sp t Standing:0.5 "1,0.3,-0.6:0.7")
for m in ${1:-inst_a red_a}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 900 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_sheep_reduce_claude/review/viewer/?model=$m" $P/review/shots/$m $F $B $N $M $U $R $H $K $T 2>&1 | tail -1
  cd $P
done
