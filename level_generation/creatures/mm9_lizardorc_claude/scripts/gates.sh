#!/bin/bash
# All numeric gates on export/mm9_lizardorc.glb into review/gates/. Project folder.
. scripts/env.sh; R=review/gates; mkdir -p $R; g=export/mm9_lizardorc.glb; rm -f $R/done.txt
$G scripts/collapse_gate.py $g $R/collapse.json 2>/dev/null > $R/collapse.txt &
$G scripts/arm_hand_gate.py $g $R/arm.json --side L=' L ' --side R=' R ' --outer-only --exact 2>/dev/null > $R/arm.txt &
$G scripts/skirt_gate.py $g $R/skirt.json 2>/dev/null > $R/skirt.txt &
$G scripts/jitter_gate.py $g work/ref_half.glb $R/jitter.json --side L=' L ' --side R=' R ' 2>/dev/null > $R/jitter.txt &
$G ../claude_shared/detached_parts_audit.py $g --fps 24 --md $R/detached.md > $R/detached.txt 2>&1 &
wait
$G scripts/grip_gate.py $g $R/grip.txt > /dev/null 2>&1
$G scripts/blade_gate.py $g $R/blade.json Bone07 ' R ' 2>/dev/null > $R/blade.txt
$G scripts/orient_gate.py $g source/true/lizardorc_true.glb $R/orient.json 2>/dev/null > $R/orient.txt
$G ../claude_shared/bone_length_audit.py $g > $R/bones.txt 2>&1
$G ../claude_shared/flat_shading_check.py $g > $R/flat.txt 2>&1
$G ../mm9_imp_claude/scripts/stride.py $g Walking 'Bip01 L Foot' 'Bip01 R Foot' 2>/dev/null > $R/stride.txt
$G ../mm9_imp_claude/scripts/stride.py $g Running 'Bip01 L Foot' 'Bip01 R Foot' 2>/dev/null >> $R/stride.txt
echo GATESDONE > $R/done.txt
