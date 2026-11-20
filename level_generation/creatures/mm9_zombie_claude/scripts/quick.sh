#!/bin/bash
# blend -> reduce -> clips -> collapse gate. Usage: TOKEN=.. scripts/quick.sh [tag]
cd /home/pjasicek/github/OpenYAMM
P=level_generation/creatures/mm9_zombie_claude; R=$PWD/$P; B="tools/run_creature_blender.sh --token $TOKEN"; G=$PWD/level_generation/creatures/claude_shared/gltf_venv/bin/python
run() { local out; out=$($B "$@" 2>&1); log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1); grep -E '^(protected|DEC|REDUCED|RINGS|BRIDGE|LIFT|EXPORTED|RIGGED|BRANCHES|zero)|Traceback|Error|^  File' "$log" | cut -c1-220; }
run $P/scripts/rig_zombie.py $R/work/graft_v1.blend $R/source/z1/zombie1_true.glb $R/work/rig_v1.blend
run $P/scripts/reduce_zombie.py $R/work/rig_v1.blend $R/work/red_v1.blend
run $P/scripts/export_quick.py $R/work/red_v1.blend $R/work/quick_body.glb
cd $P; $G scripts/clips_mm9.py work/quick_body.glb work/quick_clips.glb scripts/roles_zombie.json work/clips.json 2>&1 | grep -v Unexpected | cut -c1-260; python3 scripts/clip_heights.py work/quick_clips.glb | head -3
