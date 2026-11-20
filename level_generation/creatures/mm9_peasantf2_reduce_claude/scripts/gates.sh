#!/bin/bash
# PeasantF2's own numeric gates (../mm9_peasantf2_claude/scripts/gates.sh + README: skin poke, see-through double=1) on one
# runtime GLB. Jitter runs on the GLB itself against the creature's MM9 reference (work/ref_half.glb); run it on the installed
# file too for the before numbers. same_clips.py proves clips, skeleton, images, materials byte-identical to the installed file.
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_peasantf2_claude/scripts
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"; export PYTHONPATH=/usr/lib/python3/dist-packages
$G $S/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
$G $S/robe_gate.py $glb $out/robe_gate.json > $out/robe_gate.txt 2>&1 &
$G $S/arm_hand_gate.py $glb $out/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm_hand.txt 2>&1 &
wait
$G $S/jitter_gate.py $glb $C/mm9_peasantf2_claude/work/ref_half.glb $out/jitter.json --side L=' L ' --side R=' R ' > $out/jitter.txt 2>&1 &
$G $S/skin_poke_gate.py $glb $out/skin_poke.json > $out/skin_poke.txt 2>&1 &
$G $C/claude_shared/detached_parts_audit.py $glb > $out/detached.txt 2>&1 &
wait
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_peasantf2_reduce_claude/before/mm9_peasantf2.glb $glb > $out/same_clips.txt 2>&1
[[ -z "${NOST:-}" ]] && scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1 --python $S/see_through_gate.py -- $glb $PWD/$out/seethrough/st.json double=1 > $out/seethrough.txt 2>&1
echo GATESDONE > $out/done.txt
