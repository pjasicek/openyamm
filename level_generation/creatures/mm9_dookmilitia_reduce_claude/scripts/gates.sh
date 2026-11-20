#!/bin/bash
# The Half-Orc project's numeric gates (../mm9_dookmilitia_claude/scripts/gates_run2.sh) on one GLB, run from the creature
# project (read only: its gates read work/dook_clips0.glb, work/hand_poses.json, source/true/dook1_true.glb).
# Usage (this project folder): scripts/gates.sh <glb> <tag> -> review/gates_<tag>/ (done.txt last; new tag for a rerun)
set -u
here=$(cd "$(dirname "$0")/.." && pwd); glb=$(realpath "$1"); out=$here/review/gates_$2; mkdir -p $out
C=$here/..; G="$here/scripts/cap.sh $C/claude_shared/gltf_venv/bin/python"
cd $C/mm9_dookmilitia_claude
$G scripts/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
$G scripts/arm_hand_gate.py $glb $out/arm.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm.txt 2>&1 &
NOCLOTH=1 $G scripts/arm_hand_gate.py $glb $out/arm_skin.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm_skin.txt 2>&1 &
$G scripts/jitter_gate.py $glb work/dook_clips0.glb $out/jitter.json --side L=' L ' --side R=' R ' > $out/jitter.txt 2>&1 &
wait
$G scripts/skirt_gate.py $glb $out/skirt.json > $out/skirt.txt 2>&1 &
$G scripts/cloth_torso_gate.py $glb $out/cloth_torso.json > $out/cloth_torso.txt 2>&1 &
$G scripts/blade_gate.py $glb $out/sword.json Ybasesword ' X ' > $out/sword.txt 2>&1 &
$G scripts/grip_gate.py $glb $out/grip.txt > $out/grip.log 2>&1 &
wait
$G ../claude_shared/detached_parts_audit.py $glb --fps 24 --md $out/detached.md > $out/detached.txt 2>&1 &
$G ../claude_shared/bone_length_audit.py $glb > $out/bones.txt 2>&1 &
$G scripts/orient_gate.py $glb source/true/dook1_true.glb $out/orient.json > $out/orient.txt 2>&1 &
$G scripts/handedness.py work/merged1.glb source/true/dook1_true.glb $glb > $out/handedness.txt 2>&1 &
wait
$G ../claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G ../claude_shared/texture_quality.py $glb > $out/texq.txt 2>&1
$G ../../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/clip_floor.py $glb > $out/clip_floor.txt 2>&1
echo GATESDONE > $out/done.txt
