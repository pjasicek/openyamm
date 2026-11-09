#!/bin/bash
# Numeric gates of the Evil Sorcerer's own project (../mm9_evilsorcerer_claude/scripts/gates.sh) on one GLB, run in place
# from that project's scripts (read only). Clip-only gates (jitter, orient, bone lengths) are skipped: the clips are byte
# for byte the installed ones (checked by build_export.sh). Floor: lod_check.py (lowest point per clip and LOD).
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt
set -u
glb=$1; out=review/gates_$2; mkdir -p $out
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_evilsorcerer_claude/scripts
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
$G $S/collapse_gate.py $glb $out/collapse.json 2>&1 | grep -v Unexpected > $out/collapse.txt &
$G $S/panel_gate.py $glb $out/panel_gate.json 2>&1 | grep -v Unexpected > $out/panel_gate.txt &
wait
$G $S/arm_hand_gate.py $glb $out/arm_hand.json --side L=" L " --side R=" R " --outer-only 2>&1 | grep -v Unexpected > $out/arm_hand.txt &
$G $C/claude_shared/detached_parts_audit.py $glb 2>&1 | grep -v Unexpected | tail -30 > $out/detached.txt &
wait
$G $C/claude_shared/flat_shading_check.py $glb 2>&1 | grep -v Unexpected | tail -6 > $out/flat.txt
$G $C/claude_shared/texture_quality.py $glb 2>&1 | grep -v Unexpected | tail -20 > $out/texture_quality.txt
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
echo GATESDONE > $out/done.txt
