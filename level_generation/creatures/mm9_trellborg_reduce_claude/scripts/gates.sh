#!/bin/bash
# The Trellborg project's numeric gates (../mm9_trellborg_claude/scripts/final.sh plus grip, wrist and bone gates) on one runtime GLB,
# run from the creature project (its gates read work/fist.json, work/cuff.json, work/trell_clips0c.glb, source/; read only; grip_gate
# is a copy in scripts/creature_gates/ that writes here). Usage (this project folder): scripts/gates.sh <glb> <tag> -> review/gates_<tag>/
set -u
here=$(cd "$(dirname "$0")/.." && pwd); glb=$(realpath "$1"); out=$here/review/gates_$2; mkdir -p $out
C=$here/..; G="$here/scripts/cap.sh $C/claude_shared/gltf_venv/bin/python"
cd $C/mm9_trellborg_claude
$G scripts/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
$G scripts/jitter_gate.py $glb work/trell_clips0c.glb $out/jitter.json --side L=' L ' --side R=' R ' > $out/jitter.txt 2>&1 &
NOCLOTH=1 $G scripts/arm_hand_gate.py $glb $out/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm_hand.txt 2>&1 &
wait
$G scripts/club_gate.py $glb > $out/club.txt 2>&1 &
$G $here/scripts/creature_gates/grip_gate.py $glb $out/grip.txt > /dev/null 2>&1 &
$G scripts/wrist_gate.py $glb > $out/wrist.txt 2>&1 &
wait
$G scripts/orient_gate.py $glb source/true/trellborg1_true.glb $out/orient.json > $out/orient.txt 2>&1
$G scripts/handedness.py $glb > $out/handedness.txt 2>&1
$G ../claude_shared/detached_parts_audit.py $glb --fps 24 > $out/detached.txt 2>&1
$G ../claude_shared/bone_length_audit.py $glb > $out/bones.txt 2>&1
$G ../claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G ../claude_shared/texture_quality.py $glb > $out/texq.txt 2>&1
$G ../../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
echo GATESDONE > $out/done.txt
