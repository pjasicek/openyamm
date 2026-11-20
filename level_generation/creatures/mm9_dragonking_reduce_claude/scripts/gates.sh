#!/bin/bash
# The Dragon King's own numeric gates (../mm9_dragonking_claude/scripts/gates.py: edge stretch per material, lowest point
# and loop seams per clip; clip_heights.py) plus the shared checks (detached parts, flat shading, texture quality, bone
# lengths, winding, LOD bounds/floor/stretch), the wing attachment and surface jitter (surface_gates.py) and same_clips.py
# (clips, skeleton, nodes, images and materials byte-identical to the installed file) on one runtime GLB.
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out; echo RUNNING > $out/done.txt
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_dragonking_claude/scripts
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
$G $S/gates.py $glb $out/gates.json > $out/gates.txt 2>&1 &
$G $C/claude_shared/detached_parts_audit.py $glb --fps 24 > $out/detached.txt 2>&1 &
$G $S/clip_heights.py $glb > $out/clip_heights.txt 2>&1 &
wait
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_dragonking_reduce_claude/before/mm9_dragonking.glb $glb > $out/same_clips.txt 2>&1
$G scripts/surface_gates.py $glb $out/surface_gates.json > $out/surface_gates.txt 2>&1
REA_NODE=DragonKing $BL -P scripts/lod_check.py -- $glb $2 > $out/lod_check.txt 2>&1
echo GATESDONE > $out/done.txt
