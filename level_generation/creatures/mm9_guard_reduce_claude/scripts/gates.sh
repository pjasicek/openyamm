#!/bin/bash
# The Guard project's own gates (../mm9_guard_claude/work/third.sh: arm/hand, collapse, skirt, jitter, detached on the runtime
# body; grip and blade on a GLB with the halberd, here merge_halberd.py) plus flat shading, texture quality, bone length,
# winding and same_clips.py (clips, skin, nodes, materials, variants, images byte-identical to the installed file).
# Run from the creature project (its gates read ../claude_shared relative paths and work/guard_clips.glb; read only).
# Usage (any folder): scripts/gates.sh <body glb> <tag> -> review/gates_<tag>/ ; done.txt is written last.
set -u
here=$(cd "$(dirname "$0")/.." && pwd); glb=$(realpath "$1"); out=$here/review/gates_$2; mkdir -p $out
C=$here/..; G="$here/scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
$G $here/scripts/merge_halberd.py $glb $here/before/mm9_guard_halberd.glb $out/with_halberd.glb > $out/merge.txt 2>&1
cd $C/mm9_guard_claude
SIDES=(--side "L= L " --side "R= R ")
$G scripts/arm_hand_gate.py $glb $out/arm_hand.json "${SIDES[@]}" --outer-only --exact --forearm Forearm --hand-names "Hand,Finger,Thumb,Index,Middle,Ring,Pinky" > $out/arm_hand.txt 2>&1 &
$G scripts/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
$G scripts/skirt_gate.py $glb $out/skirt.json > $out/skirt.txt 2>&1 &
wait
$G scripts/jitter_gate.py $glb work/guard_clips.glb $out/jitter.json "${SIDES[@]}" > $out/jitter.txt 2>&1 &
$G ../claude_shared/detached_parts_audit.py $glb --fps 24 > $out/detached.txt 2>&1 &
$G scripts/grip_gate.py $out/with_halberd.glb $out/grip.txt > /dev/null 2>&1 &
wait
$G scripts/blade_gate.py $out/with_halberd.glb $out/blade.json > $out/blade.txt 2>&1 &
$G ../claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1 &
$G ../claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1 &
wait
$G ../claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G ../../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G $here/scripts/same_clips.py $here/before/mm9_guard.glb $glb > $out/same_clips.txt 2>&1
rm -f $out/with_halberd.glb
echo GATESDONE > $out/done.txt
