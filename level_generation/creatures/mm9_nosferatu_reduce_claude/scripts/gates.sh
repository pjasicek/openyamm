#!/bin/bash
# The Nosferatu's own numeric gates (../mm9_nosferatu_claude/scripts/gates.sh) on any GLB, outputs only in this project.
# jitter, bone length and orientation read only the clips and skin, which same_clips.py checks are the installed bytes.
# Usage (project folder): scripts/gates.sh <glb> <out dir>
set -u
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"; N=../mm9_nosferatu_claude/scripts
g=$1; O=$2; mkdir -p $O
$G $N/collapse_gate.py $g $O/collapse.json 2>&1 | grep -v Unexpected > $O/collapse.txt &
$G $N/cloth_gate.py $g ../mm9_nosferatu_claude/work/uv_final.npz $O/cloth.json 2>&1 | grep -v Unexpected > $O/cloth.txt &
$G $N/arm_hand_gate.py $g $O/arm_hand.json --side L=" L " --side R=" R " --outer-only --exact 2>&1 | grep -v Unexpected > $O/arm_hand.txt &
wait
$G ../claude_shared/flat_shading_check.py $g 2>&1 | grep -v Unexpected | tail -6 > $O/flat.txt
$G ../claude_shared/detached_parts_audit.py $g 2>&1 | grep -v Unexpected | tail -30 > $O/detached.txt
$G ../claude_shared/texture_quality.py $g 2>&1 | grep -v Unexpected | tail -20 > $O/texture_quality.txt
$G "$(cd ../../.. && pwd)/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" $g 2>&1 | grep -v Unexpected | tail -2 > $O/winding.txt
echo DONE > $O/done
