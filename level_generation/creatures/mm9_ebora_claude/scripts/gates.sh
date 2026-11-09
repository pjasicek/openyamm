#!/bin/bash
# all numeric gates on the final GLB into review/gates/ (project folder)
G=../claude_shared/gltf_venv/bin/python; g=${GLB:-export/mm9_ebora.glb}; O=${OUT:-review/gates}; mkdir -p $O
$G -W ignore scripts/collapse_gate.py $g $O/collapse.json 2>&1 | grep -v Unexpected > $O/collapse.txt
$G -W ignore scripts/arm_hand_gate.py $g $O/arm_hand.json --side L=" L " --side R=" R " --outer-only 2>&1 | grep -v Unexpected > $O/arm_hand.txt
$G -W ignore scripts/jitter_gate.py work/half.glb work/ref_half.glb $O/jitter.json --side L=' L ' --side R=' R ' 2>&1 | grep -v Unexpected > $O/jitter.txt
$G -W ignore ../claude_shared/flat_shading_check.py $g 2>&1 | grep -v Unexpected | tail -8 > $O/flat.txt
$G -W ignore ../claude_shared/detached_parts_audit.py $g 2>&1 | grep -v Unexpected | tail -30 > $O/detached.txt
$G -W ignore ../claude_shared/bone_length_audit.py $g 2>&1 | grep -v Unexpected > $O/bones.txt
$G -W ignore ../../decorations/mm8_3d/animated/scripts/check_winding.py $g 2>&1 | grep -v Unexpected | tail -2 > $O/winding.txt
$G -W ignore ../claude_shared/texture_quality.py $g 2>&1 | grep -v Unexpected | tail -30 > $O/texture_quality.txt
echo DONE > $O/done
