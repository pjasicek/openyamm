#!/bin/bash
# The Scholars' own numeric gates (../mm9_scholar_claude/scripts/gates_sc.sh: collapse, robe, arm/hand --outer-only --exact, flat,
# detached, texture quality, bone length; plus its sleeve_poke_gate.py) and the reduction checks (winding, same_clips, lining_gate)
# on one runtime GLB (installed or candidate). Jitter is not re-run: the clips are the installed bytes (same_clips).
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt   (see-through: scripts/see_through.sh)
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_scholar_claude/scripts
export PYTHONPATH=/usr/lib/python3/dist-packages
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
$G $S/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
$G $S/robe_gate.py $glb $out/robe_gate.json > $out/robe_gate.txt 2>&1 &
$G $S/arm_hand_gate.py $glb $out/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm_hand.txt 2>&1 &
wait
$G $S/sleeve_poke_gate.py $glb $out/sleeve_poke.json > $out/sleeve_poke.txt 2>&1 &
$G scripts/lining_gate.py $glb $out/lining.json > $out/lining.txt 2>&1 &
wait
$G $C/claude_shared/detached_parts_audit.py $glb > $out/detached.txt 2>&1
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_scholar_reduce_claude/before/mm9_scholar.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
