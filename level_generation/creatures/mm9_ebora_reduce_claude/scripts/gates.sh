#!/bin/bash
# Ebora's gate set (mm9_ebora_claude/scripts/gates.sh) on any GLB: GLB=<glb> OUT=<dir> scripts/gates.sh  (project folder)
# jitter: against Ebora's MM9 reference clips (her work/ref_half.glb), as her own gates ran it
G=../claude_shared/gltf_venv/bin/python; E=../mm9_ebora_claude/scripts; g=$GLB; O=$OUT; mkdir -p $O
run() { systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 "$@"; }
run $G -W ignore $E/collapse_gate.py $g $O/collapse.json 2>&1 | grep -v Unexpected > $O/collapse.txt
run $G -W ignore $E/arm_hand_gate.py $g $O/arm_hand.json --side L=" L " --side R=" R " --outer-only 2>&1 | grep -v Unexpected > $O/arm_hand.txt
run $G -W ignore $E/jitter_gate.py $g ../mm9_ebora_claude/work/ref_half.glb $O/jitter.json --side L=' L ' --side R=' R ' 2>&1 | grep -v Unexpected > $O/jitter.txt
$G -W ignore ../claude_shared/flat_shading_check.py $g 2>&1 | grep -v Unexpected | tail -8 > $O/flat.txt
run $G -W ignore ../claude_shared/detached_parts_audit.py $g 2>&1 | grep -v Unexpected | tail -30 > $O/detached.txt
$G -W ignore ../claude_shared/bone_length_audit.py $g 2>&1 | grep -v Unexpected > $O/bones.txt
$G -W ignore ../../decorations/mm8_3d/animated/scripts/check_winding.py $g 2>&1 | grep -v Unexpected | tail -2 > $O/winding.txt
$G -W ignore ../claude_shared/texture_quality.py $g 2>&1 | grep -v Unexpected | tail -30 > $O/texture_quality.txt
echo DONE > $O/done
