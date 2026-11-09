#!/bin/bash
# The Terror's own numeric gates (../mm9_terror_claude/scripts/gates.py: edge stretch, floor, loop seams; seat_check.py --texpass:
# eyes, teeth, tongue and mouth interior) plus the Gezzampt's collapse gate and the shared checks, on one runtime GLB. The Terror
# has no arms or hands (no arm/hand, sleeve or grip gates) and its project ran no jitter gate. same_clips.py proves clips,
# skeleton, sockets, images and materials byte-identical to the installed file.
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out; echo RUNNING > $out/done.txt
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_terror_claude/scripts
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
$G $S/gates.py $glb $out/gates.json > $out/gates.txt 2>&1 &
$G $C/mm9_gezzampt_claude/scripts/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
wait
$G $S/seat_check.py $glb $out/seat_check.json --texpass > $out/seat_check.txt 2>&1 &
$G $C/claude_shared/detached_parts_audit.py $glb --fps 24 > $out/detached.txt 2>&1 &
wait
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_terror_reduce_claude/before/mm9_terror.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
