#!/bin/bash
# all numeric gates on the final GLB into review/gates/ (project folder)
. scripts/env.sh
G=$PYG; g=export/mm9_nosferatu.glb; O=review/gates; mkdir -p $O
$G -W ignore scripts/collapse_gate.py $g $O/collapse.json 2>&1 | grep -v Unexpected > $O/collapse.txt
$G -W ignore scripts/cloth_gate.py $g work/uv_final.npz $O/cloth.json 2>&1 | grep -v Unexpected > $O/cloth.txt
$G -W ignore scripts/arm_hand_gate.py $g $O/arm_hand.json --side L=" L " --side R=" R " --outer-only --exact 2>&1 | grep -v Unexpected > $O/arm_hand.txt
$G -W ignore scripts/half_keys.py work/ref_clips.glb work/ref_half.glb 2>&1 | grep -E 'Traceback|Error'
$G -W ignore scripts/jitter_gate.py work/arm2.glb work/ref_half.glb $O/jitter.json --side L=' L ' --side R=' R ' 2>&1 | grep -v Unexpected > $O/jitter.txt
$G -W ignore ../claude_shared/flat_shading_check.py $g 2>&1 | grep -v Unexpected | tail -6 > $O/flat.txt
$G -W ignore ../claude_shared/detached_parts_audit.py $g 2>&1 | grep -v Unexpected | tail -30 > $O/detached.txt
python3 ../claude_shared/floor/floor_audit.py --world mm9 --match 'MM9 Nosferatu*' 2>&1 | tail -5 > $O/floor.txt
$G -W ignore ../claude_shared/bone_length_audit.py $g > $O/bone_length.txt 2>&1
$G -W ignore ../claude_shared/texture_quality.py $g 2>&1 | grep -v Unexpected | tail -20 > $O/texture_quality.txt
echo DONE > $O/done
