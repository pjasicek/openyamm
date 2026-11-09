#!/bin/bash
# PeasantM3's own numeric gates (../mm9_peasantm3_claude/scripts/gates.sh: arm/hand --outer-only, jitter vs MM9's clips
# work/mm9_pm3_clips.glb, detached, flat, texture quality, bones, winding; plus its sleeve_poke_gate.py), run in place (read
# only) on one runtime GLB, with --exact on the arm gate as the other reductions; PeasantDM4's lining gate copy and same_clips.py.
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt   (see-through: scripts/see_through.sh)
set -u
cd "$(dirname "$0")/.."
P=$PWD; glb=$(realpath $1); out=$PWD/review/gates_$2; mkdir -p $out
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_peasantm3_claude/scripts
G="$P/scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
cd $C/mm9_peasantm3_claude
$G $S/arm_hand_gate.py $glb $out/arm_hand.json --side "L= L " --side "R= R " --outer-only --exact > $out/arm_hand.txt 2>&1 &
$G $S/jitter_gate.py $glb $C/mm9_peasantm3_claude/work/mm9_pm3_clips.glb $out/jitter.json --side "L= L " --side "R= R " > $out/jitter.txt 2>&1 &
$G $S/sleeve_poke_gate.py $glb $out/sleeve_poke.json > $out/sleeve_poke.txt 2>&1 &
wait
$G $P/scripts/lining_gate.py $glb $out/lining.json > $out/lining.txt 2>&1
$G $C/claude_shared/detached_parts_audit.py $glb > $out/detached.txt 2>&1
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G $P/scripts/same_clips.py $P/before/mm9_peasantm3.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
