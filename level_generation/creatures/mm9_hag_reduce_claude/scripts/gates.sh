#!/bin/bash
# Old Hag's numeric gates (the creature's own v2 scripts, read in place: ../mm9_hag_claude/v2/scripts) on one runtime GLB, installed
# or candidate alike, plus the shared audits, the sleeve-lining gate and same_clips.py (clips, skin, images, materials byte-identical).
# Blender gates (sleeve_gate, poke_gate x2) run one at a time. Usage (any folder): scripts/gates.sh <glb> <tag> -> review/gates_<tag>/
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); D=review/gates_$2; mkdir -p $D
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; Y=$C/mm9_hag_claude/v2
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
$G $Y/scripts/arm_hand_gate.py $glb $D/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact > $D/arm_hand.txt 2>&1 &
$G $Y/scripts/jitter_gate.py $glb $Y/work/mm9_hag_clips.glb $D/jitter.json --side L=' L ' --side R=' R ' > $D/jitter.txt 2>&1 &
$G scripts/lining_gate.py $glb $D/lining.json 24 > $D/lining.txt 2>&1 &
wait
$G $C/claude_shared/detached_parts_audit.py $glb --fps 48 > $D/detached.txt 2>&1
$G $C/claude_shared/flat_shading_check.py $glb > $D/flat.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $D/bones.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $D/texture_quality.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $D/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_hag_reduce_claude/before/mm9_hag.glb $glb > $D/same_clips.txt 2>&1
if [[ "${NOBLENDER:-0}" != 1 ]]; then
  $BL -P $Y/scripts/sleeve_gate.py -- $glb $PWD/$D/sleeve_gate.json FHP > $D/sleeve_gate.log 2>&1
  # the Hag's own project ran sleeve_gate and its see_through_gate (pdm2), not poke_gate
  $BL -P $C/mm9_hag_claude/scripts/see_through_gate.py -- $glb $PWD/$D/see_through.json > $D/see_through.log 2>&1
fi
echo GATESDONE > $D/done.txt
