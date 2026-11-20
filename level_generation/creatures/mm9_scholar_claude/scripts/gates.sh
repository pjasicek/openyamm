#!/bin/bash
# all numeric gates on the final GLB into review/gates/ (project folder)
G=../claude_shared/gltf_venv/bin/python; g=export/mm9_monk.glb; O=review/gates; mkdir -p $O; rm -f $O/done
$G -W ignore scripts/collapse_gate.py $g $O/collapse.json 2>&1 | grep -v Unexpected > $O/collapse.txt &
$G -W ignore scripts/robe_gate.py $g $O/robe_gate.json 2>&1 | grep -v Unexpected > $O/robe_gate.txt &
$G -W ignore scripts/arm_hand_gate.py $g $O/arm_hand.json --side L=" L " --side R=" R " --outer-only 2>&1 | grep -v Unexpected > $O/arm_hand.txt &
wait
$G -W ignore scripts/half_keys.py work/clips_o.glb work/ref_half.glb 2>&1 | grep -E 'Traceback|Error'
$G -W ignore scripts/jitter_gate.py work/half.glb work/ref_half.glb $O/jitter.json --side L=' L ' --side R=' R ' 2>&1 | grep -v Unexpected > $O/jitter.txt
$G -W ignore ../claude_shared/flat_shading_check.py $g 2>&1 | grep -v Unexpected | tail -6 > $O/flat.txt
$G -W ignore ../claude_shared/detached_parts_audit.py $g 2>&1 | grep -v Unexpected | tail -30 > $O/detached.txt
$G -W ignore scripts/orient_gate.py export/mm9_monk_sock.glb source/mk1/mk1.glb $O/orient.json 2>&1 | grep -v Unexpected > $O/orient.txt
$G -W ignore ../claude_shared/texture_quality.py $g 2>&1 | grep -v Unexpected | tail -20 > $O/texture_quality.txt
$G -W ignore ../claude_shared/bone_length_audit.py $g 2>&1 | grep -v Unexpected > $O/bone_length.txt
echo DONE > $O/done
