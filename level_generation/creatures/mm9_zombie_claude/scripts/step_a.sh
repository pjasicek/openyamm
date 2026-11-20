#!/bin/bash
# fit_pose -> head parts -> graft. Usage: TOKEN=.. scripts/step_a.sh
cd /home/pjasicek/github/OpenYAMM
P=level_generation/creatures/mm9_zombie_claude; R=$PWD/$P; B="tools/run_creature_blender.sh --token $TOKEN"
run() { local out; out=$($B "$@" 2>&1); log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1); grep -E '^(PARTS|SYM|floor|OFFSET|rings|BRIDGE|FINAL|BELOW|body loops|face loops|KINDS|HAIR)|Traceback|Error|^  File' "$log" | cut -c1-260; }
run $P/scripts/fit_pose.py $R/meshy/zombie_smart_v1/model_urls_glb.glb $R/source/z1/zombie1_true.glb $R/scripts/fit_config.json $R/work/pose_v1.blend
[ "$1" = nohead ] || run $P/scripts/head_prep.py $R/meshy/zombie_head_smart_v1/model_urls_glb.glb $R/work/head_parts.blend
run $P/scripts/graft_head.py $R/work/pose_v1.blend $R/work/head_parts.blend $R/work/graft_v1.blend
