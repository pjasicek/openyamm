#!/bin/bash
# The Lich King's own gates (../mm9_lichking_claude/scripts/gates.sh: bone length, collapse, cloth_gate2, grip_gate --mirrored,
# staff_gate, head_gate, arm_hand_gate --outer-only, jitter, flat shading, detached parts, texture quality, winding) on one runtime
# GLB, installed or candidate. They run with the creature project as the working directory (grip_gate reads its work/rig.json; read
# only, every output goes to this project). Jitter: the GLB against the creature's uncorrected-clip file work/coat.glb, as its gates
# did (mirror-invariant magnitudes; clips are byte-identical anyway, same_clips.py). tube_gate.py needs the raw rig_out vertex order,
# so the see-through gate (scripts/see_through.sh) stands in for it.
# Usage (project folder): scripts/gates.sh <glb> <tag>  -> review/gates_<tag>/*.txt
set -u
cd "$(dirname "$0")/.."
P=$PWD; glb=$(realpath $1); out=$P/review/gates_$2; mkdir -p $out
C=/home/pjasicek/github/OpenYAMM/level_generation/creatures; S=$C/mm9_lichking_claude/scripts
G="$P/scripts/cap.sh $C/claude_shared/gltf_venv/bin/python -W ignore"
cd $C/mm9_lichking_claude
$G $S/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
$G $S/cloth_gate2.py $glb $out/cloth.json > $out/cloth.txt 2>&1 &
$G $S/arm_hand_gate.py $glb $out/arm_hand.json --side L=" L " --side R=" R " --outer-only > $out/arm_hand.txt 2>&1 &
wait
$G $S/grip_gate.py $glb $out/grip.json --mirrored > $out/grip.txt 2>&1 &
$G $S/staff_gate.py $glb $out/staff.json > $out/staff.txt 2>&1 &
$G $S/head_gate.py $glb > $out/staff_head.txt 2>&1 &
$G $S/jitter_gate.py $glb work/coat.glb $out/jitter.json --side L=' L ' --side R=' R ' > $out/jitter.txt 2>&1 &
wait
$G $C/claude_shared/detached_parts_audit.py $glb > $out/detached.txt 2>&1
$G $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G $C/claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $C/claude_shared/bone_length_audit.py $glb > $out/bone_length.txt 2>&1
$G $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
cd $P
$G scripts/same_clips.py $P/before/mm9_lichking.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
