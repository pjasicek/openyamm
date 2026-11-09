#!/bin/bash
# Head close-ups in the viewer (Standing 0.5): front, quarter left/right, side left/right, back, and a mouth close-up in
# Taunt and AttackMelee. scripts/head_shots.sh <tier id> <prefix> [dist]   (project folder; shots in review/shots/)
t=$1; p=$2; d=${3:-0.30}; G=../claude_shared/gltf_venv/bin/python; g=export/mm9_ebora.glb
spec() { $G -W ignore scripts/head_specs.py $g "$@" 2>/dev/null | grep -v Unexpected | tr '\n' ' '; }
S=$(spec ${p}h Standing:0.5 "0,0.08,1:$d" "0.75,0.1,0.75:$d" "-0.75,0.1,0.75:$d" "1,0.08,0:$d" "-1,0.08,0:$d" "0,0.1,-1:$d")
S+=$(spec ${p}t Taunt:${TT:-1.0} "0,0.08,1:$d" "0.75,0.1,0.75:$d")
S+=$(spec ${p}m AttackMelee:${TM:-0.4} "0,0.08,1:$d" "0.75,0.1,0.75:$d")
scripts/vs.sh $t review/shots $S
