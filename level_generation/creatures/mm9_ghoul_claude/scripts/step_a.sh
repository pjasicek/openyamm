#!/bin/bash
# fit -> head parts -> graft. Usage: TOKEN=.. scripts/step_a.sh [nohead]
cd /home/pjasicek/github/OpenYAMM
P=level_generation/creatures/mm9_ghoul_claude; R=$PWD/$P; B="tools/run_creature_blender.sh --token $TOKEN"
run() { local out; out=$($B "$@" 2>&1); log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1); grep -E '^(HOLES|FLAP|PARTS|SYM|floor|OFFSET|rings|BRIDGE|FINAL|BELOW|body loops|face loops|KINDS|HAIR|PALM|VISIBLE)|Traceback|Error|^  File' "$log" | cut -c1-200; }
run $P/scripts/fit_ghoul.py $R/meshy/ghoul_smart_v1/model_urls_glb.glb $R/source/g1/ghoul1_true.glb $R/scripts/fit_config.json $R/work/pose_v1.blend
[ "$1" = nohead ] || run $P/scripts/head_ghoul.py $R/meshy/ghoul_head_smart_v1/model_urls_glb.glb $R/work/head_parts.blend
run $P/scripts/graft_ghoul.py $R/work/pose_v1.blend $R/work/head_parts.blend $R/work/graft_v1.blend
