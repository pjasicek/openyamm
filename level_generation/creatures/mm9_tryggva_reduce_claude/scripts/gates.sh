#!/bin/bash
# Numeric gates on one runtime GLB (installed or candidate), PeasantM1 reduce project's gates.sh adapted: the creature's own
# arm/hand, jitter (vs its MM9-clip reference work/mm9_try_clips.glb) and sleeve-poke gates (../mm9_tryggva_claude/scripts, read in place), the
# PeasantM2d family's collapse gate (../mm9_peasantm2d_claude/scripts, read in place) and the shared audits. Clips, skeleton,
# images and materials: same_clips.py (byte-identical to the installed file). See-through: scripts/see_through.sh.
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_tryggva_claude/scripts; S2=$C/mm9_peasantm2d_claude/scripts
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
$G $S2/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
$G $S/arm_hand_gate.py $glb $out/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm_hand.txt 2>&1 &
wait
$G $S/jitter_gate.py $glb $C/mm9_tryggva_claude/work/mm9_try_clips.glb $out/jitter.json --side L=' L ' --side R=' R ' > $out/jitter.txt 2>&1 &
$G $S/sleeve_poke_gate.py $glb $out/sleeve_poke.json > $out/sleeve_poke.txt 2>&1 &
wait
$G $C/claude_shared/detached_parts_audit.py $glb --fps 24 > $out/detached.txt 2>&1
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_tryggva_reduce_claude/before/mm9_tryggva.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
