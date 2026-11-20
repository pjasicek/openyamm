#!/bin/bash
# Kira's numeric gates (the creature's own: ../mm9_kira_claude/scripts/gates.sh, read in place) on one runtime GLB, installed or
# candidate alike, plus the shared audits and same_clips.py (clips, skin, images, materials byte-identical to the installed file).
# Usage (any folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); D=review/gates_$2; mkdir -p $D
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; K=$C/mm9_kira_claude
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
$G $K/scripts/collapse_gate.py $glb $D/collapse.json > $D/collapse.txt 2>&1 &
$G $K/scripts/arm_hand_gate.py $glb $D/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact > $D/arm_hand.txt 2>&1 &
$G $K/scripts/skirt_gate.py $glb $D/skirt.json > $D/skirt.txt 2>&1 &
wait
$G $K/scripts/jitter_gate.py $glb $K/work/kira_clips0.glb $D/jitter.json --side L=' L ' --side R=' R ' > $D/jitter.txt 2>&1 &
$G $K/scripts/sleeve_poke_gate.py $glb $D/sleeve_poke_inside.json --hand-pos $K/work/hand_pos.npy --past 0.0 > $D/sleeve_poke_inside.txt 2>&1 &
$G $K/scripts/sleeve_poke_gate.py $glb $D/sleeve_poke.json --hand-pos $K/work/hand_pos.npy > $D/sleeve_poke.txt 2>&1 &
wait
$G $C/claude_shared/detached_parts_audit.py $glb --fps 24 > $D/detached.txt 2>&1
$G $C/claude_shared/flat_shading_check.py $glb > $D/flat.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $D/bones.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $D/texture_quality.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $D/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_kira_reduce_claude/before/mm9_kira.glb $glb > $D/same_clips.txt 2>&1
echo GATESDONE > $D/done.txt
