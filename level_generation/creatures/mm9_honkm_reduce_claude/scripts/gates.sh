#!/bin/bash
# The Honk male's own numeric gates (../mm9_honkmale_claude/scripts/gates_all.sh: jitter against the arm-offset reference,
# arm/hand --outer-only --exact, detached, flat shading, collapse, robe, sleeve (Blender), forearm poke from the female project; the hair gate is the female's braids only),
# plus texture quality, bone length, winding and same_clips.py. Usage (project folder): scripts/gates.sh <glb> <tag> [noblender]
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out; out=$(realpath $out)
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; F=$C/mm9_honkmale_claude; M=$C/mm9_honkmale_claude/scripts
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
$G $F/v2/scripts/jitter_gate.py $glb $F/v2/work/mm9_honkm_clips.glb $out/jitter.json --side "L= L " --side "R= R " > $out/jitter.txt 2>&1 &
$G $F/v2/scripts/arm_hand_gate.py $glb $out/arm_hand.json --side "L= L " --side "R= R " --outer-only --exact > $out/arm_hand.txt 2>&1 &
$G $C/claude_shared/detached_parts_audit.py $glb > $out/detached.txt 2>&1 &
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1 &
wait
$G $M/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
$G $M/robe_gate.py $glb $out/robe.json > $out/robe.txt 2>/dev/null &
$G $C/mm9_honkfemale_claude/scripts/forearm_poke.py $glb $out/forearm_poke.json > $out/forearm_poke.txt 2>&1 &
wait
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_honkm_reduce_claude/before/mm9_honkm.glb $glb > $out/same_clips.txt 2>&1
if [[ "${3:-}" != noblender ]]; then
  scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1 \
    --python $F/v2/scripts/sleeve_gate.py -- $glb $out/sleeve_gate.json Bip01 24 front,above34,below,q34 > $out/sleeve.txt 2>&1
  tail -12 $out/sleeve.txt | grep -v "^$" > $out/sleeve_tail.txt
fi
echo GATESDONE > $out/done.txt
