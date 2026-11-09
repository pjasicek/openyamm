#!/bin/bash
# The Mummy's own numeric gates (../mm9_mummy_claude/work/gates.sh) on one runtime GLB, plus flat shading, texture quality, bone
# length, winding and same_clips.py (clips, skeleton, images, materials byte-identical to the installed file). The arm/hand gate
# runs on the runtime GLB here (the creature ran it on its strip-less skin), for the installed file and the candidate alike.
# Jitter and orientation gates read bones only: the clips are byte-identical, so they are not rerun.
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_mummy_claude/scripts
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
$G $S/collapse_gate.py $glb $out/collapse.json 2>&1 | grep -v frozen > $out/collapse.txt &
$G $S/arm_hand_gate.py $glb $out/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact 2>&1 | grep -v frozen > $out/arm_hand.txt &
$G $S/strip_gate.py $glb $out/strip.json 2>&1 | grep -v frozen > $out/strip.txt &
wait
$G $S/strip_gate.py $glb $out/strip_torso.json "" torso 2>&1 | grep -v frozen > $out/strip_torso.txt &
$G $C/claude_shared/detached_parts_audit.py $glb --fps 24 > $out/detached.txt 2>&1 &
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1 &
wait
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_mummy_reduce_claude/before/mm9_mummy.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
