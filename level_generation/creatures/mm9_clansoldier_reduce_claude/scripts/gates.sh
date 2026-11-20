#!/bin/bash
# The Clan Soldier project's numeric gates (../mm9_clansoldier_claude/scripts/gates.sh plus grip and blade gates) on one runtime GLB,
# run from the creature project (its gates read work/grips.json, work/clan_clips0.glb, source/true/clan1_true.glb; read only).
# Usage (this project folder): scripts/gates.sh <glb> <tag> -> review/gates_<tag>/ ; done.txt is written last.
set -u
here=$(cd "$(dirname "$0")/.." && pwd); glb=$(realpath "$1"); out=$here/review/gates_$2; mkdir -p $out
C=$here/..; G="$here/scripts/cap.sh $C/claude_shared/gltf_venv/bin/python"
cd $C/mm9_clansoldier_claude
$G scripts/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
$G scripts/arm_hand_gate.py $glb $out/arm.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm.txt 2>&1 &
$G scripts/jitter_gate.py $glb work/clan_clips0.glb $out/jitter.json --side L=' L ' --side R=' R ' > $out/jitter.txt 2>&1 &
wait
$G scripts/skirt_gate.py $glb $out/skirt.json > $out/skirt.txt 2>&1 &
NOCLOTH=1 $G scripts/arm_hand_gate.py $glb $out/arm_skin.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm_skin.txt 2>&1 &
$G ../claude_shared/detached_parts_audit.py $glb --fps 24 > $out/detached.txt 2>&1 &
wait
$G scripts/grip_gate.py $glb $out/grip.txt > /dev/null 2>&1 &
$G scripts/blade_gate.py $glb $out/blade_sword.json Ybasesword ' R ' > $out/blade_sword.txt 2>&1 &
$G scripts/blade_gate.py $glb $out/blade_shield.json Ybaseshield ' L ' > $out/blade_shield.txt 2>&1 &
wait
$G scripts/orient_gate.py $glb source/true/clan1_true.glb $out/orient.json > $out/orient.txt 2>&1
$G scripts/handedness.py $glb > $out/handedness.txt 2>&1
$G ../claude_shared/bone_length_audit.py $glb > $out/bones.txt 2>&1
$G ../claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G ../claude_shared/texture_quality.py $glb > $out/texq.txt 2>&1
$G ../../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
echo GATESDONE > $out/done.txt
