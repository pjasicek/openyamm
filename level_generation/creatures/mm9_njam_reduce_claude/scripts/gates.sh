#!/bin/bash
# Njam's own numeric gates (../mm9_njam_claude/scripts/gates.sh, from the Nobleman reduction's copy) on one runtime GLB (bare hands:
# no blade/grip gates); + orient against MM9's source, the lining gate (lining re-emitted) and same_clips.
# Orient, handedness and bone length read only the clips: same_clips.py proves clips, skeleton, sockets, images and
# materials byte-identical to the installed file instead (LOD heights, floor and stretch per LOD: lod_check.py).
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_njam_claude/scripts
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
$G $S/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
$G $S/arm_hand_gate.py $glb $out/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm_hand.txt 2>&1 &
$G $S/skirt_gate.py $glb $out/skirt.json > $out/skirt.txt 2>&1 &
wait
$G $S/jitter_gate.py $glb $C/mm9_njam_claude/work/nj_clips0.glb $out/jitter.json --side L=' L ' --side R=' R ' > $out/jitter.txt 2>&1 &
NOCLOTH=1 $G $S/arm_hand_gate.py $glb $out/arm_hand_skin.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm_hand_skin.txt 2>&1 &
$G $C/claude_shared/detached_parts_audit.py $glb --fps 24 > $out/detached.txt 2>&1 &
wait
$G $S/orient_gate.py $glb $C/mm9_njam_claude/source/true/njam_src.glb $out/orient.json > $out/orient.txt 2>&1 &
$G scripts/lining_gate.py $glb $out/lining.json > $out/lining.txt 2>&1 &
wait
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_njam_reduce_claude/before/mm9_njam.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
