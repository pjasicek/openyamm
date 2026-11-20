#!/bin/bash
# Upper-body viewer shots installed vs reduced (the viewer's focus framings sit low on this 2.5 m body): mane from behind,
# from the side-back and above, chest and shoulders front and back, both fists, AttackMelee and Taunt mane/nape.
# Usage: scripts/upper_shots.sh [models] -> review/shots_upper/<model>/
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python; g=before/mm9_basilisk.glb
sp() { $G -W ignore scripts/bone_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
M=$(HEADUP=0.015,0.05,0.05 sp m Standing:0.5 "0,0.25,-1:1.5" "-1,0.4,-0.6:1.5" "0.2,1,-0.3:1.5")
T=$(HEADUP=0.015,-0.55,0.15 sp t Standing:0.5 "0,0.15,1:2.0" "0,0.25,-1:2.0" "1,0.2,0.4:2.0")
A=$(HEADUP=0.015,0.05,0.05 sp n AttackMelee:0.3 "-0.6,0.3,-1:1.6")
U=$(HEADUP=0.015,0.05,0.05 sp u Taunt:0.5 "0.6,0.3,-1:1.6")
L=$(BONE='Bip01 L Hand' HEADUP=0,0,0 sp l Standing:0.5 "0.3,0.2,1:0.7" "1,0.1,-0.3:0.7")
R=$(BONE='Bip01 R Hand' HEADUP=0,0,0 sp r Standing:0.5 "-0.3,0.2,1:0.7" "-1,0.1,-0.3:0.7")
for m in ${1:-inst_a red_a inst_c red_c}; do
  cd /home/pjasicek/github/OpenYAMM
  timeout 900 node level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_basilisk_reduce_claude/review/viewer/?model=$m" $P/review/shots_upper/$m $M $T $A $U $L $R 2>&1 | tail -1
  cd $P
done
