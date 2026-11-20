#!/usr/bin/env bash
# PeasantDF's own numeric gates (../mm9_peasantdf_claude/scripts/gates_pdf.sh + sleeve_poke_gate.py + robe_gate.py) on one
# runtime GLB of design <n> (installed or candidate), plus same_clips.py (clips, skin, nodes, materials, images byte-identical
# to the installed design). The see-through gate (Blender) is scripts/see_through_df.sh.
# Usage (project folder): scripts/gates_df.sh <glb> <n> <tag> -> review/gates_<tag>/d<n>/*.txt
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); n=$2; out=review/gates_$3/d$n; mkdir -p $out
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_peasantdf_claude/scripts
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"; Y="scripts/cap.sh python3"
$Y $S/arm_hand_gate.py $glb $out/arm_hand_gate.json --side "L= L " --side "R= R " --outer-only > $out/arm_hand_gate.txt 2>&1 &
$Y $S/jitter_gate.py $glb $C/mm9_peasantdf_claude/work/mm9_pdf${n}_clips.glb $out/jitter_gate.json --side "L= L " --side "R= R " > $out/jitter_gate.txt 2>&1 &
$Y $S/sleeve_poke_gate.py $glb $out/sleeve_poke.json > $out/sleeve_poke.txt 2>&1 &
wait
$Y $S/robe_gate.py $glb $out/robe_gate.json > $out/robe_gate.txt 2>&1 &
$Y $C/claude_shared/detached_parts_audit.py $glb > $out/detached.txt 2>&1 &
$Y $C/claude_shared/flat_shading_check.py $glb > $out/flat_shading.txt 2>&1 &
wait
$Y $C/claude_shared/texture_quality.py $glb --json $out/texture_quality.json > $out/texture_quality.txt 2>&1
$Y $C/claude_shared/bone_length_audit.py $glb > $out/bones.txt 2>&1
python3 $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_peasantdf_reduce_claude/before/mm9_peasantdf$n.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
