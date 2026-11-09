#!/bin/bash
# Yanmir's own numeric gates (../mm9_yanmir_claude/scripts/gates.sh) on one runtime GLB (installed or candidate), run from this
# project folder (the creature's scripts use ../claude_shared relative paths). Jitter against the creature's reference clips
# work/yan_ref_clips.glb. Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_yanmir_claude/scripts; Y=$C/mm9_yanmir_claude
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
$G $S/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
$G $S/jitter_gate.py $glb $Y/work/yan_ref_clips.glb $out/jitter.json --side L=' L ' --side R=' R ' > $out/jitter.txt 2>&1 &
$G $S/jitter_gate.py $glb $Y/work/yan_ref_clips.glb $out/jitter_rel.json --side L=' L ' --side R=' R ' --rel 0.25 > $out/jitter_rel.txt 2>&1 &
wait
$G $S/staff_gate.py $glb $out/staff.json Ystaff 'Bip01 R ' > $out/staff.txt 2>&1 &
PYTHONPATH=$S NOCLOTH=1 $G $S/arm_hand_gate.py $glb $out/arm_hand_skin.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm_hand_skin.txt 2>&1 &
$G $S/staff_gate.py $glb $out/beard.json 'Bip01 Ponytail1' 'Bip01 Head ' > $out/beard.txt 2>&1 &
wait
$G $C/claude_shared/detached_parts_audit.py $glb --fps 24 > $out/detached.txt 2>&1
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
python3 $C/claude_shared/bone_length_audit.py $Y/source/raw/yanmir.glb $Y/source/true/yanmir_true.glb $glb > $out/bones.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_yanmir_reduce_claude/before/mm9_yanmir.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
