#!/bin/bash
# Viewer shots for the cow reduction review, both tiers, installed and reduced (one shot script at a time; Imp copy):
# face sheet f0-f4 (front close-up, 3/4, true profile, low 3/4, party; framed on a point fixed in Xhead at the face centre),
# body b0-b5 (Standing front/3-4/back, Walking 3/4, Running 3/4, Death 3/4) and bone-framed close shots: n (upper neck, the cut
# group: side, from above-behind, Fidget side), u (udder and teats from below-side), r (rump/back from the rear-above, Standup2
# 0.7 = the ladder's worst frame), h (front and hind hooves), t (tail and tassel).
# Usage: scripts/shots.sh [models]  -> review/shots/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python; g=before/mm9_cow.glb
spec() { BONE=Xhead HEADUP=0.016,0.099,-0.044 $G -W ignore scripts/head_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
sp() { $G -W ignore scripts/bone_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
F=$(spec f Standing:0.5 "0,0.1,1:1.1" "0.75,0.1,0.75:1.1" "1,0.05,0:1.1" "0.7,-0.45,0.7:1.0" "0,0.42,1:3.6")
B="b0:Standing:0.5:front:body b1:Standing:0.5:quarter:body b2:Standing:0.5:rear:body b3:Walking:0.5:quarter:body b4:Running:0.2:quarter:body b5:Death:1.6:quarter:body"
N=$(BONE=Xneckbase HEADUP=0,0.05,0.2 sp n Standing:0.5 "1,0.2,0:1.1" "0.3,1,-0.6:1.1")
N2=$(BONE=Xneckbase HEADUP=0,0.05,0.2 sp m Fidget:1.2 "1,0.2,0.3:1.1")
U=$(BONE=XbackC HEADUP=0,-0.6,0 sp u Standing:0.5 "0.9,-0.4,0.3:1.0")
R=$(BONE=XbackC HEADUP=0,0,0 sp r Standing:0.5 "0.3,0.7,-1:1.6")
R2=$(BONE=XbackC HEADUP=0,0,0 sp s Standup2:0.7 "0.6,0.5,-1:1.8")
H=$(BONE=Xffoot HEADUP=0,0,0 sp h Standing:0.5 "1,0.3,0.6:0.6")
H2=$(BONE=Xbfoot HEADUP=0,0,0 sp k Standing:0.5 "1,0.3,-0.6:0.6")
T=$(BONE=XtailE HEADUP=0,0,0 sp t Standing:0.5 "1,0.3,-0.6:0.8")
for m in ${1:-inst_a red_a inst_b red_b}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 900 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_cow_reduce_claude/review/viewer/?model=$m" $P/review/shots/$m $F $B $N $N2 $U $R $R2 $H $H2 $T 2>&1 | tail -1
  cd $P
done
