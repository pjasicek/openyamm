#!/bin/bash
# Skraelos' own numeric gates (../mm9_skraelos_claude/scripts/gates_sk.sh + gates2.sh: collapse, arm/hand --outer-only --exact, prop gate,
# flat, detached, texture quality, bone length) and the reduction checks (winding, same_clips) on one runtime GLB (installed or
# candidate). Jitter is not re-run: the clips are the installed bytes (same_clips). Floor: lod_check.py (lowest point per clip).
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt   (see-through: scripts/see_through.sh)
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_skraelos_claude/scripts
export PYTHONPATH=/usr/lib/python3/dist-packages
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
$G $S/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
$G $S/arm_hand_gate.py $glb $out/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm_hand.txt 2>&1 &
$G $S/prop_gate.py $glb $out/prop_gate.json > $out/prop_gate.txt 2>&1 &
wait
$G $C/claude_shared/detached_parts_audit.py $glb > $out/detached.txt 2>&1
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_skraelos_reduce_claude/before/mm9_skraelos.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
