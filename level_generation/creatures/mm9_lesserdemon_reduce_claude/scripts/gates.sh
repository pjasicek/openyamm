#!/bin/bash
# The Lesser Demon's own numeric gates (../mm9_stage1demon_claude/scripts/gates.sh) on any runtime GLB -> review/gates_<tag>/.
# Usage (project folder): scripts/gates.sh <glb> <tag>. Jitter reference: MM9's clips with the helper keys (its work/clips1.glb).
set -u; cd "$(dirname "$0")/.."; g=$(realpath "$1"); o=review/gates_$2; mkdir -p $o
S=../mm9_stage1demon_claude/scripts; G="scripts/cap.sh $PWD/../claude_shared/gltf_venv/bin/python -W ignore"
$G $S/collapse_gate.py $g $o/collapse.json > $o/collapse.txt 2>&1 &
PYTHONPATH=$S $G $S/arm_hand_gate.py $g $o/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact --hand-names Hand,Finger --arm-names Clavicle,UpperArm,Forearm,Hand,Finger > $o/arm_hand.txt 2>&1 &
$G $S/jitter_gate.py $g ../mm9_stage1demon_claude/work/clips1.glb $o/jitter.json --side L=' L ' --side R=' R ' > $o/jitter.txt 2>&1 &
wait
$G ../claude_shared/detached_parts_audit.py $g --fps 24 > $o/detached.txt 2>&1 &
$G ../claude_shared/flat_shading_check.py $g > $o/flat.txt 2>&1 &
$G ../claude_shared/bone_length_audit.py $g > $o/bone_length.txt 2>&1 &
$G ../../decorations/mm8_3d/animated/scripts/check_winding.py $g > $o/winding.txt 2>&1 &
wait
$G ../claude_shared/texture_quality.py $g > $o/texture_quality.txt 2>&1
echo GATES DONE $o
