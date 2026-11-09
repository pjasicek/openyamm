#!/bin/bash
# red blend -> rig -> quick export -> clips -> half keys -> collapse gate. Usage: TOKEN=.. scripts/quick.sh
cd /home/pjasicek/github/OpenYAMM
P=level_generation/creatures/mm9_stage1demon_claude; R=$PWD/$P; B="tools/run_creature_blender.sh --token $TOKEN"; G=$PWD/level_generation/creatures/claude_shared/gltf_venv/bin/python
run() { local out; out=$($B "$@" 2>&1); log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1); grep -E '^(JOINTS|heat|RIGGED|zero|LIFT|EXPORTED)|Traceback|Error|^  File' "$log" | cut -c1-200; }
run $P/scripts/rig_demon.py $R/work/red_v1.blend $R/source/tier1/ldemon_true.glb $R/scripts/fit_config.json $R/work/rig_v1.blend
run $P/scripts/export_quick.py $R/work/rig_v1.blend $R/work/quick_body.glb
cd $P; $G scripts/clips_mm9.py work/quick_body.glb work/quick_clips0.glb scripts/roles_demon.json work/clips.json 2>&1 | grep -v Unexpected | cut -c1-300 | tail -3
$G scripts/half_keys.py work/quick_clips0.glb work/quick_clips.glb 2>&1 | grep -v Unexpected | tail -1
