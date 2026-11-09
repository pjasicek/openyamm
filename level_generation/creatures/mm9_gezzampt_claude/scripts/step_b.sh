#!/bin/bash
# hands -> weld. Project folder.
R=$PWD
cd /home/pjasicek/github/OpenYAMM; P=level_generation/creatures/mm9_gezzampt_claude; T=$(cat $P/work/token); cd $P
cd ../../..; out=$(tools/run_creature_blender.sh --token $T $P/scripts/graft_hands.py $R/scripts/graft_gezz.json 2>&1 </dev/null); L=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1); grep -E '^THUMB|Traceback|Error|^  File' $L | cut -c1-300; cd $P
F='^(WRIST)' W=240 scripts/run.sh wrist_weld.py $R/work/hands_raw.blend $R/work/hands_v1.json $R/work/hands_v1.blend
