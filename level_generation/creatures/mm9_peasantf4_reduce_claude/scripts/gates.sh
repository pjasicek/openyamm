#!/bin/bash
# PeasantF4's own gates (../mm9_peasantf4_claude/scripts/gates_pf4.sh, scripts only read) on a runtime GLB, under the 12G cap.
# Jitter is not re-run: clips are byte-identical (same_clips.py). gate_pf4.py runs as gate_rt.py on the runtime GLB.
# Usage (project folder): scripts/gates.sh <glb> <out dir> [--see]   (--see adds the Blender see-through gate and lod_check)
set -u
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"; export PYTHONPATH=/usr/lib/python3/dist-packages
S=../mm9_peasantf4_claude/scripts; g=$1; O=$2; mkdir -p $O
$G $S/collapse_gate.py $g $O/collapse.json 2>&1 | grep -v Unexpected > $O/collapse.txt &
$G $S/robe_gate.py $g $O/robe_gate.json 2>&1 | grep -v Unexpected > $O/robe_gate.txt &
$G $S/arm_hand_gate.py $g $O/arm_hand.json --side L=" L " --side R=" R " --outer-only --exact 2>&1 | grep -v Unexpected > $O/arm_hand.txt &
wait
$G ../claude_shared/flat_shading_check.py $g 2>&1 | grep -v Unexpected | tail -6 > $O/flat.txt
$G ../claude_shared/detached_parts_audit.py $g 2>&1 | grep -v Unexpected | tail -30 > $O/detached.txt
$G ../claude_shared/texture_quality.py $g 2>&1 | grep -v Unexpected | tail -30 > $O/texture_quality.txt
$G ../claude_shared/bone_length_audit.py $g 2>&1 | grep -v Unexpected > $O/bone_length.txt
$G $S/sleeve_poke_pf1.py $g $O/sleeve_poke.json 2>&1 | grep -v Unexpected > $O/sleeve_poke.txt
$G scripts/gate_rt.py $g $O/hood_sleeve.json 2>&1 | grep -v Unexpected > $O/hood_sleeve.txt
$G ../../decorations/mm8_3d/animated/scripts/check_winding.py $g 2>&1 | grep -v Unexpected | tail -1 > $O/winding.txt
if [[ "${3:-}" == "--see" ]]; then
  BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
  $BL --python $S/see_through_gate.py -- "$PWD/$g" "$PWD/$O/see_through.json" > $O/see.log 2>&1
  REA_NODE=PeasantF4 $BL --python scripts/lod_check.py -- "$PWD/$g" "$(basename $O)" > $O/lod_check.log 2>&1
fi
echo GATES DONE $O
