#!/bin/bash
# The Dwarf's own numeric gates (../mm9_dwarf_claude/scripts/gates.sh, scripts copied here) on one GLB.
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt
set -u
glb=$1; out=review/gates_$2; mkdir -p $out review/gates
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python"; D=$C/mm9_dwarf_claude
$G scripts/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
$G scripts/arm_hand_gate.py $glb $out/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm_hand.txt 2>&1 &
wait
$G scripts/jitter_gate.py $glb $D/work/dwarf_clips0.glb $out/jitter.json --side L=' L ' --side R=' R ' > $out/jitter.txt 2>&1 &
$G scripts/skirt_gate.py $glb $out/skirt.json > $out/skirt.txt 2>&1 &
wait
$G scripts/skirt_bunch.py $glb > $out/skirt_bunch.txt 2>&1 &
$G scripts/grip_gate.py $glb $out/grip.txt > $out/grip_log.txt 2>&1 &
wait
$G scripts/blade_gate.py $glb $out/blade.json RHand1 ' R ' > $out/blade.txt 2>&1 &
NOCLOTH=1 $G scripts/arm_hand_gate.py $glb $out/arm_hand_skin.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm_hand_skin.txt 2>&1 &
wait
$G scripts/wrist_gap_gate.py $glb > $out/wrist_gap.txt 2>&1 &
$G scripts/rim_gate.py $glb $out/rim.json > $out/rim.txt 2>&1 &
wait
$G scripts/beard_gate.py $glb > $out/beard.txt 2>&1
$G scripts/orient_gate.py $glb $D/source/true/dwarf_true.glb $out/orient.json > $out/orient.txt 2>&1
$G scripts/handedness.py $D/source/true/dwarf_true.glb $D/source/true/dwarf_true.glb $glb > $out/handedness.txt 2>&1
python3 $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/claude_shared/detached_parts_audit.py $glb --fps 24 > $out/detached.txt 2>&1
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
echo GATESDONE > $out/done.txt
