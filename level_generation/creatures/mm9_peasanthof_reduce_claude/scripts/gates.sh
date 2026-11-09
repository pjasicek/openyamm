#!/bin/bash
# The half-orc women's own gates (../mm9_peasanthof_claude/scripts/finish_gates.sh + gates_phof.sh: arm/hand --outer-only,
# jitter vs the retargeted clips, detached, flat, texture quality, bones, winding, sleeve poke, robe, HOF2 robe_diag) + same_clips
# on one GLB (installed or candidate), read-only use of the creature's scripts. See-through: scripts/see_through.sh.
# Usage (project folder): M=1|2 scripts/gates.sh <glb> <tag>  -> review/hof$M/gates_<tag>/*
set -u
cd "$(dirname "$0")/.."; : "${M:?M=1|2}"
glb=$(realpath $1); out=review/hof$M/gates_$2; mkdir -p $out
S=../mm9_peasanthof_claude/scripts; C=..
CAP="scripts/cap.sh"; PY="$CAP python3"; G="$CAP $C/claude_shared/gltf_venv/bin/python -W ignore"
sha256sum $glb > $out/glb.sha256
$PY $S/arm_hand_gate.py $glb $out/arm_hand.json --side "L= L " --side "R= R " --outer-only > $out/arm_hand.txt 2>&1 &
$PY $S/jitter_gate.py $glb work/hof$M/ref_clips.glb $out/jitter.json --side "L= L " --side "R= R " > $out/jitter.txt 2>&1 &
$PY $S/sleeve_poke_gate.py $glb $out/sleeve.json > $out/sleeve.txt 2>&1 &
$PY $S/robe_gate.py $glb $out/robe.json > $out/robe.txt 2>&1 &
wait
if [[ $M == 2 ]]; then $PY $S/robe_diag.py $glb all 2>&1 | grep ROBE_DIAG > $out/robe_visible.txt; fi
$PY $C/claude_shared/detached_parts_audit.py $glb > $out/detached.txt 2>&1
$PY $C/claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$PY $C/claude_shared/texture_quality.py $glb --json $out/texture_quality.json > $out/texture_quality.txt 2>&1
$PY $C/claude_shared/bone_length_audit.py $glb > $out/bones.txt 2>&1
python3 $C/../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
$G scripts/same_clips.py before/mm9_peasanthof$M.glb $glb > $out/same_clips.txt 2>&1
echo GATESDONE > $out/done.txt
