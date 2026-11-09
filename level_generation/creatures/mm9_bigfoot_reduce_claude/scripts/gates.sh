#!/bin/bash
# Bigfoot's own numeric gates (../mm9_bigfoot_claude/scripts/gates.sh: collapse, jitter strict / relative 0.25 against MM9's
# clips with helpers, arm/hand skin-only outer exact, detached, flat shading, texture quality, bone lengths, winding) on one
# runtime GLB, plus same_clips.py against the installed file. Handedness, stride and orientation read only the clips, which
# same_clips.py proves byte-identical. Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out; echo RUNNING > $out/done.txt
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; B=$C/mm9_bigfoot_claude; S=$B/scripts
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
PYTHONPATH=$S NOCLOTH=1 $G $S/arm_hand_gate.py $glb $out/arm.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm.txt 2>&1 &
$G $S/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
wait
$G $S/jitter_gate.py $glb $B/work/bf_ref_clips.glb $out/jitter.json --side L=' L ' --side R=' R ' > $out/jitter.txt 2>&1 &
$G $S/jitter_gate.py $glb $B/work/bf_ref_clips.glb $out/jitter_rel.json --side L=' L ' --side R=' R ' --rel 0.25 > $out/jitter_rel.txt 2>&1 &
wait
$G $C/claude_shared/detached_parts_audit.py $glb --fps 24 > $out/detached.txt 2>&1
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $B/source/t1/bigfoot1.glb $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_bigfoot_reduce_claude/before/mm9_bigfoot.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
