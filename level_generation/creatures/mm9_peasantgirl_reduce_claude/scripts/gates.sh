#!/bin/bash
# The peasant girls' own numeric gates (../mm9_peasantgirl_claude/scripts: collapse, robe + robe ray check, arm/hand --outer-only
# --exact, jitter vs the creature's ref_half, sleeve poke (this project's copy: labels by vertex key, so reduced GLBs work),
# detached parts, flat shading, texture quality, bone lengths, winding, same clips) on one runtime GLB.
# Usage (project folder): scripts/gates.sh <glb> <tag> h|e  -> review/gates_<tag>/*.txt   (see-through: scripts/see_through.sh)
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; v=$3; mkdir -p $out
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_peasantgirl_claude/scripts
[[ $v == h ]] && src=before/mm9_peasantgirl.glb || src=before/mm9_peasantgirl1e.glb
export PYTHONPATH=/usr/lib/python3/dist-packages
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
$G $S/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
$G $S/robe_gate.py $glb $out/robe_gate.json > $out/robe_gate.txt 2>&1 &
$G $S/arm_hand_gate.py $glb $out/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm_hand.txt 2>&1 &
wait
$G $S/jitter_gate.py $glb $C/mm9_peasantgirl_claude/work/ref_half_$v.glb $out/jitter.json --side L=' L ' --side R=' R ' > $out/jitter.txt 2>&1 &
$G scripts/sleeve_poke_pg.py $glb $out/sleeve_poke.json > $out/sleeve_poke.txt 2>&1 &
$G $S/robe_ray_check.py $glb > $out/robe_ray.txt 2>&1 &
wait
$G $C/claude_shared/detached_parts_audit.py $glb > $out/detached.txt 2>&1
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $src $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
