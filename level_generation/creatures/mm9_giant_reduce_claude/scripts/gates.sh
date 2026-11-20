#!/bin/bash
# Numeric gates of the Giant's own project (../mm9_giant_claude/scripts/gates.sh plus grip_gate and mallet_gate) on one GLB.
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt
set -u
glb=$1; out=review/gates_$2; mkdir -p $out
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python"; ref=$C/mm9_giant_claude/work/gi_ref_clips.glb
$G scripts/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
$G scripts/jitter_gate.py $glb $ref $out/jitter.json --side L=' L ' --side R=' R ' > $out/jitter.txt 2>&1 &
wait
PYTHONPATH=scripts NOCLOTH=1 NOWEAPON=1 $G scripts/arm_hand_gate.py $glb $out/arm_hand_skin.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm_hand_skin.txt 2>&1 &
$G scripts/grip_gate.py $glb $out/grip.json > $out/grip.txt 2>&1 &
wait
$G scripts/mallet_gate.py $glb $out/mallet.json > $out/mallet.txt 2>&1
$G $C/claude_shared/detached_parts_audit.py $glb --fps 24 > $out/detached.txt 2>&1
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
python3 $C/claude_shared/bone_length_audit.py $C/mm9_giant_claude/source/t2/giant2.glb $glb > $out/bones.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
echo GATESDONE > $out/done.txt
