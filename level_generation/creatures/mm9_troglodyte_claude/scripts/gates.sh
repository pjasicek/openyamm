#!/bin/bash
# All numeric gates on export/mm9_troglodyte.glb into review/gates/. Project folder.
. scripts/env.sh; R=review/gates; mkdir -p $R; g=export/mm9_troglodyte.glb
HEADREF=work/head_ref.npz $G scripts/collapse_gate.py $g $R/collapse.json 2>/dev/null > $R/collapse.txt &
$G scripts/arm_hand_gate.py $g $R/arm.json --side L=' L ' --side R=' R ' --outer-only --exact 2>/dev/null > $R/arm.txt &
$G scripts/pierce_gate.py $g $R/pierce.json 2>/dev/null > $R/pierce.txt &
$G scripts/jitter_gate.py $g work/raw_clips.glb $R/jitter.json --side L=' L ' --side R=' R ' 2>/dev/null > $R/jitter.txt &
$G ../claude_shared/detached_parts_audit.py $g --fps 24 --md $R/detached.md > $R/detached.txt 2>&1 &
wait
$G ../mm9_imp_claude/scripts/stride.py $g Walking 'Bip02 L Toe0' 'Bip02 R Toe0' 2>/dev/null > $R/stride.txt
$G ../mm9_imp_claude/scripts/stride.py $g Running 'Bip02 L Toe0' 'Bip02 R Toe0' 2>/dev/null >> $R/stride.txt
echo GATESDONE > $R/done.txt
