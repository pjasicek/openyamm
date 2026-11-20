#!/bin/bash
# all numeric gates on the final GLB into review/gates/<tag>/ (project folder). Usage: scripts/gates.sh <tag>
G=../claude_shared/gltf_venv/bin/python; g=${GLB:-export/mm9_lichking.glb}; O=review/gates/$1; mkdir -p $O
python3 ../claude_shared/bone_length_audit.py $g > $O/bone_length.txt 2>&1
$G -W ignore scripts/collapse_gate.py $g $O/collapse.json 2>&1 | grep -v Unexpected > $O/collapse.txt
$G -W ignore scripts/cloth_gate2.py $g $O/cloth.json 2>&1 | grep -v Unexpected > $O/cloth.txt
$G -W ignore scripts/grip_gate.py $g $O/grip.json --mirrored 2>&1 | grep -v Unexpected > $O/grip.txt
$G -W ignore scripts/staff_gate.py $g $O/staff.json 2>&1 | grep -v Unexpected > $O/staff.txt          # 2026-11-01: staff against body, head, floor
$G -W ignore scripts/head_gate.py $g 2>&1 | grep -v Unexpected > $O/staff_head.txt
$G -W ignore scripts/arm_hand_gate.py $g $O/arm_hand.json --side L=" L " --side R=" R " --outer-only 2>&1 | grep -v Unexpected > $O/arm_hand.txt
$G -W ignore scripts/jitter_gate.py work/arms.glb work/coat.glb $O/jitter.json --side L=' L ' --side R=' R ' 2>&1 | grep -v Unexpected > $O/jitter.txt
$G -W ignore ../claude_shared/flat_shading_check.py $g 2>&1 | grep -v Unexpected | tail -6 > $O/flat.txt
$G -W ignore ../claude_shared/detached_parts_audit.py $g 2>&1 | grep -v Unexpected > $O/detached.txt   # r9: full output (tail -30 cut the summary line)
$G -W ignore ../claude_shared/texture_quality.py $g 2>&1 | grep -v Unexpected | tail -30 > $O/texture_quality.txt
$G -W ignore ../../decorations/mm8_3d/animated/scripts/check_winding.py $g > $O/winding.txt 2>&1
echo DONE > $O/done
