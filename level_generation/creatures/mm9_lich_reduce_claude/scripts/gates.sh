#!/bin/bash
# The Lich's own gates (../mm9_lich_claude/scripts: arm_hand_gate --exact as extra_gates.sh runs it, jitter_gate, sleeve_gate at
# 12 fps front and below as the README's table) plus the shared audits on one runtime GLB; same_clips.py proves clips, skin,
# nodes, materials, variants and images byte-identical to the installed file. LOD heights, floor and stretch: lod_check.py.
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out; out=$(realpath $out)
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_lich_claude/scripts
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
$G $S/arm_hand_gate.py $glb $out/arm_hand.json --side "L= L " --side "R= R " --exact --hand-names Hand,Finger,Tip,Pinky --arm-names Clavicle,UpperArm,Forearm,Hand,Finger,Tip,Pinky > $out/arm_hand.txt 2>&1 &
$G $S/jitter_gate.py $glb $C/mm9_lich_claude/work/mm9_lich_clips.glb $out/jitter.json --side "L= L " --side "R= R " > $out/jitter.txt 2>&1 &
$G $C/claude_shared/detached_parts_audit.py $glb --fps 24 > $out/detached.txt 2>&1 &
wait
$BL -P $S/sleeve_gate.py -- $glb $out/sleeve.json Bip01 12 front,below > $out/sleeve.txt 2>&1
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_lich_reduce_claude/before/mm9_lich.glb $glb > $out/same_clips.txt 2>&1
REA_NODE=Lich $BL -P scripts/lod_check.py -- $glb $2 > $out/lod_check.log 2>&1
echo GATESDONE > $out/done.txt
