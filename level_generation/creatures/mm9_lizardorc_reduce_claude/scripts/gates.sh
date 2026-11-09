#!/bin/bash
# The Lizard-Orc project's numeric gates (../mm9_lizardorc_claude/scripts/gates.sh, plus plate_gate and grip_gate) on one GLB,
# run from the creature project (its gates read work/shell_pos.npy, work/hand_poses.json, work/ref_half.glb; read only).
# Usage (this project folder): scripts/gates.sh <glb, absolute or relative to this project> <tag>  -> review/gates_<tag>/
# done.txt is written last; use a new tag for a rerun.
set -u
here=$(cd "$(dirname "$0")/.." && pwd); glb=$(realpath "$1"); out=$here/review/gates_$2; mkdir -p $out
C=$here/..; G="$here/scripts/cap.sh $C/claude_shared/gltf_venv/bin/python"
cd $C/mm9_lizardorc_claude
export PYTHONPATH=$(python3 -c "import yaml,os;print(os.path.dirname(os.path.dirname(yaml.__file__)))")
$G scripts/collapse_gate.py $glb $out/collapse.json 2>/dev/null > $out/collapse.txt &
$G scripts/arm_hand_gate.py $glb $out/arm.json --side L=' L ' --side R=' R ' --outer-only --exact 2>/dev/null > $out/arm.txt &
$G scripts/jitter_gate.py $glb work/ref_half.glb $out/jitter.json --side L=' L ' --side R=' R ' 2>/dev/null > $out/jitter.txt &
wait
$G scripts/skirt_gate.py $glb $out/skirt.json 2>/dev/null > $out/skirt.txt &
$G scripts/plate_gate.py $glb $out/plate.txt > /dev/null 2>&1 &
$G ../claude_shared/detached_parts_audit.py $glb --fps 24 --md $out/detached.md > $out/detached.txt 2>&1 &
wait
$G scripts/grip_gate.py $glb $out/grip.txt > /dev/null 2>&1
$G scripts/blade_gate.py $glb $out/blade.json Bone07 ' R ' 2>/dev/null > $out/blade.txt
$G scripts/orient_gate.py $glb source/true/lizardorc_true.glb $out/orient.json 2>/dev/null > $out/orient.txt
$G ../claude_shared/bone_length_audit.py $glb > $out/bones.txt 2>&1
$G ../claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G ../claude_shared/texture_quality.py $glb > $out/texq.txt 2>&1
$G ../mm9_imp_claude/scripts/stride.py $glb Walking 'Bip01 L Foot' 'Bip01 R Foot' 2>/dev/null > $out/stride.txt
$G ../mm9_imp_claude/scripts/stride.py $glb Running 'Bip01 L Foot' 'Bip01 R Foot' 2>/dev/null >> $out/stride.txt
$G ../../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
echo GATESDONE > $out/done.txt
