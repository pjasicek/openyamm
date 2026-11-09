#!/bin/bash
# PeasantF3's own numeric gates (../mm9_peasantf3_claude/scripts/gates_pass2.sh + headwear_gate_pf3.py) on one runtime GLB
# (installed or candidate; place it under this project's export/ or before/ so headwear_gate finds work/uv_tex2.npz, a copy of
# the creature's). Clips, skeleton, sockets, images and materials: same_clips.py (byte-identical to the installed file).
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt   (see-through: scripts/see_through.sh)
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_peasantf3_claude/scripts
export PYTHONPATH=/usr/lib/python3/dist-packages
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
$G $S/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
$G $S/robe_gate.py $glb $out/robe_gate.json > $out/robe_gate.txt 2>&1 &
$G $S/arm_hand_gate.py $glb $out/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm_hand.txt 2>&1 &
wait
$G $S/jitter_gate.py $glb $C/mm9_peasantf3_claude/work/ref_half.glb $out/jitter.json --side L=' L ' --side R=' R ' > $out/jitter.txt 2>&1 &
$G $S/sleeve_poke_pf1.py $glb $out/sleeve_poke.json > $out/sleeve_poke.txt 2>&1 &
$G $S/headwear_gate_pf3.py $glb $out/headwear.json > $out/headwear.txt 2>&1 &
wait
$G $C/claude_shared/detached_parts_audit.py $glb > $out/detached.txt 2>&1
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_peasantf3_reduce_claude/before/mm9_peasantf3.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
