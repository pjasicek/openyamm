#!/bin/bash
# Kira's numeric gates (mm9_kira_claude/scripts/gates.sh) on one runtime GLB, for the installed (before) and the reduced (after) model
# alike. Usage (project folder): scripts/gates.sh <glb> <out dir>
set -u
glb=$1; D=$2; mkdir -p $D
K=../mm9_kira_claude; export PYTHONPATH=/usr/lib/python3/dist-packages
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore"
$G $K/scripts/collapse_gate.py $glb $D/collapse.json > $D/collapse.txt 2>&1 &
$G $K/scripts/arm_hand_gate.py $glb $D/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact > $D/arm_hand.txt 2>&1 &
$G $K/scripts/skirt_gate.py $glb $D/skirt.json > $D/skirt.txt 2>&1 &
wait
$G $K/scripts/jitter_gate.py $glb $K/work/kira_clips0.glb $D/jitter.json --side L=' L ' --side R=' R ' > $D/jitter.txt 2>&1
$G ../claude_shared/detached_parts_audit.py $glb --fps 24 > $D/detached.txt 2>&1
$G ../claude_shared/flat_shading_check.py $glb > $D/flat.txt 2>&1
$G ../claude_shared/bone_length_audit.py $glb > $D/bones.txt 2>&1
$G $K/scripts/sleeve_poke_gate.py $glb $D/sleeve_poke_inside.json --hand-pos $K/work/hand_pos.npy --past 0.0 > $D/sleeve_poke_inside.txt 2>&1
$G $K/scripts/sleeve_poke_gate.py $glb $D/sleeve_poke.json --hand-pos $K/work/hand_pos.npy > $D/sleeve_poke.txt 2>&1
$G ../claude_shared/texture_quality.py $glb > $D/texture_quality.txt 2>&1
python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $D/winding.txt 2>&1
echo DONE > $D/done.txt
