#!/bin/bash
# PeasantDM4's own numeric gates (../mm9_peasantdm4_claude/scripts/gates.sh: arm/hand --outer-only --exact, jitter vs the
# mirrored MM9 clips, detached, flat, texture quality, bones, winding; plus its sleeve_poke_gate.py and chest_shear.py), this
# project's beard gate and PeasantF3's lining gate copy, on one runtime GLB. Clips etc.: same_clips.py vs the installed file.
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt   (see-through: scripts/see_through.sh)
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=$PWD/review/gates_$2; mkdir -p $out
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_peasantdm4_claude/scripts
G="$PWD/scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
cd $C/mm9_peasantdm4_claude
$G $S/arm_hand_gate.py $glb $out/arm_hand.json --side "L= L " --side "R= R " --outer-only --exact > $out/arm_hand.txt 2>&1 &
$G $S/jitter_gate.py $glb $C/mm9_peasantdm4_claude/work/mm9_pdm4_clips_mirrored.glb $out/jitter.json --side "L= L " --side "R= R " > $out/jitter.txt 2>&1 &
$G $S/sleeve_poke_gate.py $glb $out/sleeve_poke.json > $out/sleeve_poke.txt 2>&1 &
wait
$G $S/chest_shear.py $glb > $out/chest_shear.txt 2>&1 &
$G $C/mm9_peasantdm4_reduce_claude/scripts/beard_gate_dm4.py $glb $out/beard.json > $out/beard.txt 2>&1 &
$G $C/mm9_peasantdm4_reduce_claude/scripts/lining_gate.py $glb $out/lining.json > $out/lining.txt 2>&1 &
wait
$G $C/claude_shared/detached_parts_audit.py $glb > $out/detached.txt 2>&1
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G $C/mm9_peasantdm4_reduce_claude/scripts/same_clips.py $C/mm9_peasantdm4_reduce_claude/before/mm9_peasantdm4.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
