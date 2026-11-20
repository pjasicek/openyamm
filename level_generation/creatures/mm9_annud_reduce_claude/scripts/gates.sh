#!/bin/bash
# Annud's own numeric gates (../mm9_annud_claude/scripts/gates.sh, run in place: arm and hand --outer-only --exact, jitter vs
# MM9's untouched clips v2/work/mm9_annud_clips.glb, sleeve poke) plus detached parts, flat shading, texture quality, bone
# lengths, winding (the creature README's checks), PeasantDM2's lining gate (lining vertices outside the outer cloth) and
# same_clips.py (clips, skeleton, images, materials byte-identical to the installed file). See-through: scripts/see_through.sh.
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; H=$C/mm9_annud_claude
export PYTHONPATH=
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
$G $H/v2/scripts/arm_hand_gate.py $glb $out/arm_hand.json --side "L= L " --side "R= R " --outer-only --exact > $out/arm_hand.txt 2>&1 &
$G $H/v2/scripts/jitter_gate.py $glb $H/v2/work/mm9_annud_clips.glb $out/jitter.json --side "L= L " --side "R= R " > $out/jitter.txt 2>&1 &
$G scripts/sleeve_poke_gate.py $glb $out/sleeve_poke.json > $out/sleeve_poke.txt 2>&1 &
wait
$G scripts/lining_gate.py $glb $out/lining.json > $out/lining.txt 2>&1
$G $C/claude_shared/detached_parts_audit.py $glb > $out/detached.txt 2>&1
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_annud_reduce_claude/before/mm9_annud.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
