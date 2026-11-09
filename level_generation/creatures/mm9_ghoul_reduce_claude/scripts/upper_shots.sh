#!/bin/bash
# Upper-body viewer shots (torso, shoulders, arms, hands: where most of the cut is), framed on a point fixed in the head bone
# 25 cm under the head joint: u0-u2 Standing front/3-4/back, u3 AttackMelee 3/4, u4 Hit2 3/4, u5 Fidget back.
# Usage: scripts/upper_shots.sh [models] -> review/shots/<model>/u*.png (one model at a time, at most 2 shot scripts on the machine)
cd "$(dirname "$0")/.."; P=$PWD; G=../claude_shared/gltf_venv/bin/python; g=before/mm9_ghoul.glb
spec() { HEADUP=0,-0.30,0.0 $G -W ignore scripts/head_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | sed 's/^u0:/'"$1"':/' | tr '\n' ' '; }
U="$(HEADUP=0,-0.30,0.0 $G -W ignore scripts/head_specs.py $g u Standing:0.5 "0,0.1,1:1.7" "0.75,0.1,0.75:1.7" "0,0.15,-1:1.7" 2>/dev/null | grep -v Unexpected | tr '\n' ' ')"
U="$U $(HEADUP=0,-0.30,0.0 $G -W ignore scripts/head_specs.py $g x AttackMelee:0.3 "0.75,0.1,0.75:1.8" 2>/dev/null | grep -v Unexpected | sed 's/^x0/u3/')"
U="$U $(HEADUP=0,-0.30,0.0 $G -W ignore scripts/head_specs.py $g x Hit2:0.5 "0.75,0.1,0.75:1.8" 2>/dev/null | grep -v Unexpected | sed 's/^x0/u4/')"
U="$U $(HEADUP=0,-0.30,0.0 $G -W ignore scripts/head_specs.py $g x Fidget:1.9 "-0.5,0.2,-1:1.8" 2>/dev/null | grep -v Unexpected | sed 's/^x0/u5/')"
for m in ${1:-inst_a red_a inst_c red_c}; do
  while [ "$(ps -eo args | grep -c '^node .*viewer_shots.mjs')" -ge 2 ]; do sleep 5; done
  cd /home/pjasicek/github/OpenYAMM
  timeout 900 node level_generation/creatures/mm9_ghoul_reduce_claude/scripts/viewer_shots.mjs \
    "http://127.0.0.1:8912/level_generation/creatures/mm9_ghoul_reduce_claude/review/viewer/?model=$m" $P/review/shots/$m $U 2>&1 | tail -2
  cd $P
done
echo UPPERDONE
