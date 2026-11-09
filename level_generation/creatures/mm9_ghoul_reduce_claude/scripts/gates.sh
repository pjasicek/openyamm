#!/bin/bash
# The Ghoul's own numeric gates (../mm9_ghoul_claude/scripts/gates.sh: collapse, arm/hand outer exact, jitter against MM9's clips
# with the helper keys, flaps, detached, flat shading, texture quality, bone lengths, primitive cover) plus winding and
# same_clips.py (clips, skeleton, images, materials, variants byte-identical to the installed file), on one runtime GLB.
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out; echo RUNNING > $out/done.txt
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_ghoul_claude/scripts
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
$G $S/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
PYTHONPATH=$S $G $S/arm_hand_gate.py $glb $out/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact --hand-names Hand,Finger --arm-names Clavicle,UpperArm,Forearm,Hand,Finger > $out/arm_hand.txt 2>&1 &
$G $S/jitter_gate.py $glb $C/mm9_ghoul_claude/work/ghoul_clips1.glb $out/jitter.json --side L=' L ' --side R=' R ' > $out/jitter.txt 2>&1 &
wait
$G $S/flap_gate.py $glb $out/flap.json > $out/flap.txt 2>&1 &
$G $C/claude_shared/detached_parts_audit.py $glb --fps 24 > $out/detached.txt 2>&1 &
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1 &
wait
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $S/prim_cover.py $glb > $out/prim_cover.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_ghoul_reduce_claude/before/mm9_ghoul.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
