#!/bin/bash
# first gates on the quick rig (project folder). Writes review/gates0/*.
G=$PWD/../claude_shared/gltf_venv/bin/python; g=${1:-work/quick_skirt.glb}; o=${2:-review/gates0}; mkdir -p $o
$G -W ignore scripts/collapse_gate.py $g $o/collapse.json > $o/collapse.txt 2>&1 &
$G -W ignore scripts/arm_hand_gate.py $g $o/arm.json --side L=' L ' --side R=' R ' --outer-only --exact > $o/arm.txt 2>&1 &
$G -W ignore scripts/skirt_gate.py $g $o/skirt.json > $o/skirt.txt 2>&1 &
wait
