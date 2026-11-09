#!/bin/bash
# Dog copy (2026-11-05) of the Ram reduction's gates; the creature's own gates.py and fold_measure.py. The ram project's own gates on one runtime GLB (../mm9_ram_claude README "Checks", review/gates_extra; the sheep's fold_measure.py):
# gates.py (edge stretch, lowest point per clip, loop seams), extra_clip_gates.py on every clip (floor min/max per frame, i.e.
# hoof contact, jitter p99, bone length, body-in-body), fold_measure.py (fold-overs outside the head), detached parts,
# flat shading, texture quality, winding; same_clips.py proves clips, skeleton, images, materials and variants
# byte-identical to the installed file. No arms/hands, no see-through fix, no held props on the ram (rigid horns).
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt
set -u
cd "$(dirname "$0")/.."
glb=$(realpath $1); out=review/gates_$2; mkdir -p $out; echo RUNNING > $out/done.txt
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_dog_claude/scripts; SH=$S
G="scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
ALL=Standing,Walking,Running,Fidget,AttackMelee,Hit,Death,Dead,WalkSniff,WalkBark,RunAway,Sit
$G $S/gates.py $glb $out/gates.json > $out/gates.txt 2>&1 &
$G $C/claude_shared/extra_clip_gates.py $glb --clips $ALL --ref-clips Standing --out $out/clip_gates --frames 6 > $out/clip_gates.txt 2>&1 &
wait
$G $SH/fold_measure.py $glb $out/fold.json > $out/fold.txt 2>&1 &
$G $C/claude_shared/detached_parts_audit.py $glb --fps 24 > $out/detached.txt 2>&1 &
wait
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py $C/mm9_dog_reduce_claude/before/mm9_dog.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
