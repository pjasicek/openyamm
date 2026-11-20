#!/usr/bin/env bash
# The Green Man's own gates (../mm9_greenman_claude/scripts/gates.sh) on one GLB: arm and hand (--outer-only, staff excluded),
# staff grip, jitter vs the creature's pre-floor clips and the grounded Death, detached parts (fps 10 and 6), flat shading,
# texture quality, bone lengths, winding; plus same_clips. Usage (project folder): scripts/gates.sh <glb> <tag> -> review/gates_<tag>/
set -u
cd "$(dirname "$0")/.."; P=$PWD; glb=$(realpath $1); O=$P/review/gates_$2; mkdir -p $O
C=$P/../mm9_greenman_claude; cd $C
CAP="$P/scripts/cap.sh"
$CAP python3 scripts/arm_hand_gate.py $glb $O/arm_hand_gate.json --side "L= L " --side "R= R " --outer-only --exclude-joints Bone01 > $O/arm_hand_gate.txt 2>&1 &
$CAP python3 scripts/arm_hand_gate.py $glb $O/staff_grip_gate.json --side "R= R " --only-joints Bone01 > $O/staff_grip_gate.txt 2>&1 &
wait
$CAP python3 scripts/jitter_gate.py $glb work/mm9_gm_clips.glb $O/jitter_gate.json --side "L= L " --side "R= R " > $O/jitter_gate.txt 2>&1 &
$CAP python3 scripts/jitter_gate.py $glb export/mm9_gm_extras_d.glb $O/jitter_gate_death.json --side "L= L " --side "R= R " --clips Death,Dead > $O/jitter_gate_death.txt 2>&1 &
wait
$CAP python3 ../claude_shared/detached_parts_audit.py $glb --fps 10 > $O/detached.txt 2>&1 &
$CAP python3 ../claude_shared/detached_parts_audit.py $glb --fps 6 > $O/detached6.txt 2>&1 &
wait
python3 ../claude_shared/flat_shading_check.py $glb > $O/flat_shading.txt 2>&1
python3 ../claude_shared/texture_quality.py $glb --json $O/texture_quality.json > $O/texture_quality.txt 2>&1
python3 ../claude_shared/bone_length_audit.py $glb > $O/bones.txt 2>&1
python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $O/winding.txt 2>&1
cd $P; ../claude_shared/gltf_venv/bin/python -W ignore scripts/same_clips.py $P/before/mm9_greenman.glb $glb > $O/same_clips.txt 2>&1
echo GATES DONE $2
