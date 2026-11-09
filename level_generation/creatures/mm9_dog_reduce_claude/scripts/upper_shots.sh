#!/bin/bash
# Close viewer shots installed vs reduced framed on bones (the viewer's focus framings miss this 1.2 m body; imp-reduce-20261104):
# cranium and horns from behind, side-back and above (m), torso front/back/side (t), AttackMelee and Taunt shoulders from behind
# (n, u), both hands (l, r: the trident fist), left foot (k), left shin (w: tier B's wrap), tail (s).
# Usage: scripts/upper_shots.sh [models] -> review/shots_upper/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python; g=before/mm9_imp.glb
sp() { $G -W ignore scripts/bone_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
M=$(HEADUP=0.02,0.18,0.07 sp m Standing:0.5 "0,0.25,-1:0.8" "-1,0.4,-0.6:0.8" "0.2,1,-0.3:0.8")
T=$(HEADUP=0.02,-0.25,-0.08 sp t Standing:0.5 "0,0.15,1:1.2" "0,0.25,-1:1.2" "1,0.2,0.4:1.2")
A=$(HEADUP=0.02,0.0,-0.1 sp n AttackMelee:0.3 "-0.6,0.3,-1:1.0")
U=$(HEADUP=0.02,0.0,-0.1 sp u Taunt:0.5 "0.6,0.3,-1:1.0")
pp() { $G -W ignore scripts/part_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
L=$(pp l Standing:0.5 "L Hand,L Finger" "0.3,0.2,1:0.4" "1,0.1,-0.3:0.4")
R=$(pp r Standing:0.5 "R Hand,R Finger" "-0.3,0.2,1:0.4" "-1,0.1,-0.3:0.4")
K=$(pp k Standing:0.5 "L Foot,L Toe" "0.5,0.4,1:0.45")
W=$(pp w Standing:0.5 "L Calf" "0.6,0.2,1:0.55")
S=$(BONE='Bip01 Tail2' HEADUP=0,0,0 sp s Standing:0.5 "1,0.5,-0.3:0.9")
for m in ${1:-inst_a red_a inst_b red_b inst_c red_c}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 900 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_imp_reduce_claude/review/viewer/?model=$m" $P/review/shots_upper/$m $M $T $A $U $L $R $K $W $S 2>&1 | tail -1
  cd $P
done
