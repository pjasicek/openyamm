#!/bin/bash
# The PeasantDM2's own numeric gates (../mm9_peasantdm2_claude/scripts/gates.sh: arm and hand --outer-only, jitter vs MM9's
# untouched clips work/mm9_pdm2_clips.glb, detached parts, flat shading, texture quality, bone lengths, winding) plus the
# PeasantF3 reduction's collapse gate and this project's lining gate (lining vertices outside the outer cloth) on one runtime
# GLB, plus the creature's sleeve poke gate and DM4's beard gate (stretch, torso contact). Clips, skeleton, images, materials: same_clips.py (byte-identical to the installed file).
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt   (see-through: scripts/see_through.sh)
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_peasantdm2_claude/scripts
export PYTHONPATH=/usr/lib/python3/dist-packages
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
$G $S/arm_hand_gate.py $glb $out/arm_hand.json --side "L= L " --side "R= R " --outer-only > $out/arm_hand.txt 2>&1 &
$G $S/jitter_gate.py $glb $C/mm9_peasantdm2_claude/work/mm9_pdm2_clips.glb $out/jitter.json --side "L= L " --side "R= R " > $out/jitter.txt 2>&1 &
$G scripts/sleeve_poke_gate.py $glb $out/sleeve_poke.json > $out/sleeve_poke.txt 2>&1 &
$G scripts/beard_gate.py $glb $out/beard.json > $out/beard.txt 2>&1 &
wait
$G scripts/lining_gate.py $glb $out/lining.json > $out/lining.txt 2>&1
$G $C/claude_shared/detached_parts_audit.py $glb > $out/detached.txt 2>&1
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_peasantdm2_reduce_claude/before/mm9_peasantdm2.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
