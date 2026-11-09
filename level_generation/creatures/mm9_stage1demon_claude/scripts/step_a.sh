#!/bin/bash
# fit -> head -> dump. Usage: TOKEN=.. scripts/step_a.sh   (from anywhere)
cd /home/pjasicek/github/OpenYAMM
P=level_generation/creatures/mm9_stage1demon_claude; R=$PWD/$P; B="tools/run_creature_blender.sh --token $TOKEN"
run() { local out; out=$($B "$@" 2>&1); log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1); grep -E '^(GLOBAL|PARTS|SEG|TORSO|TAIL|DELETE|PALM|TUBES|floor|SYM|HEAD|FIT|ICP 59|SHRUNK|JOINED|DUMPED|DEC|REDUCED)|Traceback|Error|^  File' "$log" | cut -c1-220; }
run $P/scripts/fit_demon.py $R/meshy/body_smart_v1/model_urls_glb.glb $R/work/mm9_true.npz $R/scripts/fit_config.json $R/work/fit_v1.blend
run $P/scripts/place_head.py $R/work/fit_v1.blend $R/meshy/head_smart_v1/model_urls_glb.glb $R/work/mm9_true.npz $R/scripts/fit_config.json $R/work/head_v1.blend
run $P/scripts/dump_mesh.py $R/work/head_v1.blend $R/work/head_v1.npz
run $P/scripts/reduce_demon.py $R/work/head_v1.blend $R/work/red_v1.blend
