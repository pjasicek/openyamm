#!/bin/bash
# Bjarni numeric gates on one runtime GLB (installed or candidate), as the creature's own scripts/gates.sh ran them
# (../mm9_bjarni_claude/scripts, read in place): arm and hand, sleeve poke, jitter (vs MM9's untouched clips work/mm9_bj_clips.glb,
# on the unmirrored GLB: mirror_glb.py is its own inverse), bones, detached, shading, winding, texture quality; plus the beard gate
# (beard_gate_m5.py, painted beard on the face shell vs the chest) and same_clips.py (everything but the geometry is the installed one).
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out work/gates
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_bjarni_claude/scripts
export PYTHONPATH=/usr/lib/python3/dist-packages
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
P="scripts/cap.sh python3 -W ignore"
$P $S/mirror_glb.py $glb work/gates/unmirrored_$2.glb > /dev/null
$G $S/arm_hand_gate.py $glb $out/arm_hand.json --side "L= L " --side "R= R " > $out/arm_hand.txt 2>&1 &
$P $S/sleeve_poke_gate.py $glb $out/sleeve_poke.json > $out/sleeve_poke.txt 2>&1 &
$G $S/jitter_gate.py work/gates/unmirrored_$2.glb $C/mm9_bjarni_claude/work/mm9_bj_clips.glb $out/jitter.json --side "L= L " --side "R= R " > $out/jitter.txt 2>&1 &
wait
$P $C/claude_shared/bone_length_audit.py $glb > $out/bones.txt 2>&1
$P $C/claude_shared/detached_parts_audit.py $glb --json $out/detached.json > $out/detached.txt 2>&1
$P $S/shading_check.py $glb > $out/shading.txt 2>&1
$P $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$P $C/claude_shared/texture_quality.py $glb --json $out/texture_quality.json > $out/texture_quality.txt 2>&1
$G scripts/beard_gate_m5.py $glb $out/beard.json > $out/beard.txt 2>&1
$G scripts/same_clips.py $C/mm9_bjarni_reduce_claude/before/mm9_bjarni.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
