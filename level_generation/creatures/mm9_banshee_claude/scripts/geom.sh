#!/bin/bash
# upper -> head -> assemble (repo root). TOKEN=<lease>
P=level_generation/creatures/mm9_banshee_claude; A=$PWD/$P
run() { out=$(tools/run_creature_blender.sh --token $TOKEN "$@" 2>&1); log=$(echo "$out"| grep -o '/tmp/openyamm[^ ]*log'|head -1); grep -E "UPPER|WAIST|BRIDGE|HAND|HEAD|Body|Cloak|Hair |SAVED|Error|Traceback|^  File" $log | cut -c1-240 | tail -${N:-14}; }
N=3 run $P/scripts/step1_body.py $A/meshy/body_st_v1/model_urls_glb.glb $A/work/upper.blend $A/work/upper.json
N=3 run $P/scripts/step3_head.py $A/meshy/head_st_v2/model_urls_glb.glb $A/work/upper.blend $A/work/head1.blend
run $P/scripts/assemble.py $A/work/head1.blend $A/source/skinA/bansheeA.glb $A/work/assembled.blend $A/work/assembled.json
