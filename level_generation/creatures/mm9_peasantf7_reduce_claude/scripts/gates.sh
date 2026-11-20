#!/bin/bash
# PeasantF7's own gates (../mm9_peasantf7_claude/scripts/gates.sh and its README "Checks"): collapse, robe (legs through the
# skirt), arm/hand --outer-only --exact, jitter (against the creature's work/ref_half.glb, MM9's untouched clips), sleeve poke
# (MPFB upper arm through the short sleeve, 30 fps), flat shading, detached parts, texture quality, bone length, winding,
# same_clips, uv_escape; then (one Blender at a time) the see-through gate (double=1, as the creature's r16-r37) and lod_check.
# Usage (project folder): scripts/gates.sh <glb> <tag> [noblender]
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out; out=$(realpath $out)
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; F=$C/mm9_peasantf7_claude
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
export PYTHONPATH=/usr/lib/python3/dist-packages
$G $F/scripts/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
$G $F/scripts/robe_gate.py $glb $out/robe.json > $out/robe.txt 2>&1 &
$G $F/scripts/arm_hand_gate.py $glb $out/arm_hand.json --side "L= L " --side "R= R " --outer-only --exact > $out/arm_hand.txt 2>&1 &
$G $F/scripts/jitter_gate.py $glb $F/work/ref_half.glb $out/jitter.json --side "L= L " --side "R= R " > $out/jitter.txt 2>&1 &
wait
$G $F/scripts/sleeve_poke_pf1.py $glb $out/sleeve_poke.json 30 > $out/sleeve_poke.txt 2>&1 &
$G $C/claude_shared/detached_parts_audit.py $glb > $out/detached.txt 2>&1 &
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1 &
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1 &
wait
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_peasantf7_reduce_claude/before/mm9_peasantf7.glb $glb > $out/same_clips.txt 2>&1
$G scripts/uv_escape.py $C/mm9_peasantf7_reduce_claude/before/mm9_peasantf7.glb $glb > $out/uv_escape.txt 2>&1
if [[ "${3:-}" != noblender ]]; then
  BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
  $BL --python scripts/see_through_gate.py -- $glb $out/see_through.json double=1 > $out/see_through.txt 2>&1
  REA_NODE=PeasantF7 $BL -P scripts/lod_check.py -- $glb $2 > $out/lod_check.log 2>&1
fi
echo GATESDONE > $out/done.txt
