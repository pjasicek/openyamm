#!/bin/bash
# The Colloidal Warrior's own numeric gates (../mm9_colloidalwarrior_claude/scripts/gates.sh) on a runtime GLB.
# Usage (project folder): scripts/gates.sh <glb> <out dir>. Jitter twice: against MM9's reference clips (as the creature's
# project) and against the installed file (before/), so a change from the mesh alone shows.
set -u
glb=$1; out=$2; mkdir -p $out
CW=../mm9_colloidalwarrior_claude; S=$CW/scripts
G="scripts/cap.sh /home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python"
export PYTHONPATH=$S
$G $S/collapse_gate.py $glb $out/collapse.json > $out/collapse.txt 2>&1 &
$G $S/jitter_gate.py $glb $CW/work/cw_ref_clips.glb $out/jitter.json --side L=' L ' --side R=' R ' > $out/jitter.txt 2>&1 &
$G $S/jitter_gate.py $glb before/mm9_colloidalwarrior.glb $out/jitter_inst.json --side L=' L ' --side R=' R ' > $out/jitter_inst.txt 2>&1 &
wait
NOCLOTH=1 $G $S/arm_hand_gate.py $glb $out/arm_hand_skin.json --side L=' L ' --side R=' R ' --outer-only --exact > $out/arm_hand_skin.txt 2>&1
$G ../claude_shared/detached_parts_audit.py $glb --fps 24 > $out/detached.txt 2>&1
$G ../claude_shared/flat_shading_check.py $glb > $out/flat.txt 2>&1
$G ../claude_shared/texture_quality.py $glb > $out/texture_quality.txt 2>&1
$G $S/handedness.py $CW/source/t1/colloidal1.glb $CW/source/true/colloidal1_true.glb $glb > $out/handedness.txt 2>&1
python3 ../claude_shared/bone_length_audit.py $CW/source/t1/colloidal1.glb $glb > $out/bones.txt 2>&1
$G ../../decorations/mm8_3d/animated/scripts/check_winding.py $glb > $out/winding.txt 2>&1
echo GATESDONE > $out/done.txt
