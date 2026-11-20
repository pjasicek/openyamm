#!/bin/bash
# From the repo root: cleaned Meshy -> rig -> skull, hems, reduction. TOKEN=<lease>
P=level_generation/creatures/mm9_lich_claude
A=$PWD/$P
run() { out=$(tools/run_creature_blender.sh --token $TOKEN "$@" 2>&1 | tail -1); lg=$(echo "$out" | cut -d' ' -f3); grep -E '^(STEP1|HAND|RIBBON|FIT|PREP)|Traceback|Error:' -A3 "$lg" | cut -c1-${CUT:-700}; }
run $P/scripts/step1_clean.py $A/meshy/smart_topology_v1/model_urls_glb.glb $A/source/mm9/lich.glb $A/work/step1.blend $A/work/step1.json
run $P/scripts/fit_lich.py $A/work/step1.blend $A/source/mm9/lich.glb $A/work/rig_v1.blend $A/work/fit.json $A/scripts/fit_config.json
run $P/scripts/prep_v2.py $A/work/rig_v1.blend $A/meshy/skull_topology_v1/model_urls_glb.glb $A/work/prep_v2.blend $A/work/prep_v2.json $A/scripts/prep_config.json
