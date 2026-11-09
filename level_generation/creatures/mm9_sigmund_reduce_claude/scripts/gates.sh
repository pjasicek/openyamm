#!/bin/bash
# Sigmund's own numeric gates (../mm9_sigmund_claude/scripts/gates.sh: arm/hand --outer-only, jitter vs its pre-fix clips
# work/mm9_sig_clips.glb, detached, flat, texture quality, bones, winding; plus its sleeve_poke_gate.py; read in place) and
# PeasantM2d's collapse gate, on one runtime GLB (installed or candidate). same_clips.py: clips/skin/materials/images unchanged.
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt   (see-through: scripts/see_through.sh)
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_sigmund_claude/scripts
G="$C/mm9_sigmund_reduce_claude/scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
cd $C/mm9_sigmund_claude
$G $C/mm9_peasantm2d_claude/scripts/collapse_gate.py $glb $C/mm9_sigmund_reduce_claude/$out/collapse.json > $C/mm9_sigmund_reduce_claude/$out/collapse.txt 2>&1 &
PYTHONPATH=$S $G $S/arm_hand_gate.py $glb $C/mm9_sigmund_reduce_claude/$out/arm_hand.json --side "L= L " --side "R= R " --outer-only > $C/mm9_sigmund_reduce_claude/$out/arm_hand.txt 2>&1 &
wait
$G $S/jitter_gate.py $glb work/mm9_sig_clips.glb $C/mm9_sigmund_reduce_claude/$out/jitter.json --side "L= L " --side "R= R " > $C/mm9_sigmund_reduce_claude/$out/jitter.txt 2>&1 &
PYTHONPATH=$S $G $S/sleeve_poke_gate.py $glb $C/mm9_sigmund_reduce_claude/$out/sleeve_poke.json > $C/mm9_sigmund_reduce_claude/$out/sleeve_poke.txt 2>&1 &
wait
cd $C/mm9_sigmund_reduce_claude
$G $C/claude_shared/detached_parts_audit.py $glb > $out/detached.txt 2>&1
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_sigmund_reduce_claude/before/mm9_sigmund.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
