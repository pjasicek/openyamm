#!/bin/bash
# The Troglodyte's own numeric gates (../mm9_troglodyte_claude/scripts/gates.sh: collapse with the open-mouth head reference,
# bind reference, arm/hand outer exact, pierce, jitter vs MM9's raw keys, detached) plus the shared checks, on one runtime GLB.
# same_clips.py proves clips, skeleton, sockets, images and materials byte-identical to the installed file (stride, orient,
# handedness read only the clips). Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out; echo RUNNING > $out/done.txt
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_troglodyte_claude/scripts
export PYTHONPATH=$(python3 -c "import yaml,os;print(os.path.dirname(os.path.dirname(yaml.__file__)))")
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
# (the open-mouth reference work/head_ref.npz has 5,798 head faces, the installed head 5,758: stale, its assert fails on the
# installed file too, so only the bind-reference collapse gate runs; the head primitive is byte-identical anyway)
$G $S/arm_hand_gate.py $glb $out/arm.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm.txt 2>&1 &
$G $S/pierce_gate.py $glb $out/pierce.json > $out/pierce.txt 2>&1 &
wait
$G $S/jitter_gate.py $glb $C/mm9_troglodyte_claude/work/raw_clips.glb $out/jitter.json --side L=' L ' --side R=' R ' > $out/jitter.txt 2>&1 &
$G $C/claude_shared/detached_parts_audit.py $glb --fps 24 > $out/detached.txt 2>&1 &
$G $S/collapse_gate.py $glb $out/collapse_bindref.json > $out/collapse_bindref.txt 2>&1 &
wait
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_troglodyte_reduce_claude/before/mm9_troglodyte.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
