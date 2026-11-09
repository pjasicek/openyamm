#!/bin/bash
# numeric gates (project folder). Writes review/gates/*.
mkdir -p review/gates
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python; g=work/gi_final_clips.glb; e=export/mm9_giant.glb
$G scripts/collapse_gate.py $g review/gates/collapse.json > review/gates/collapse.txt 2>&1 &
$G scripts/jitter_gate.py $g work/gi_ref_clips.glb review/gates/jitter.json --side L=' L ' --side R=' R ' > review/gates/jitter.txt 2>&1 &
$G scripts/jitter_gate.py $g work/gi_ref_clips.glb review/gates/jitter_rel.json --side L=' L ' --side R=' R ' --rel 0.25 > review/gates/jitter_rel.txt 2>&1 &      # second pass: also the relative test (as mm9_bigfoot_claude)
PYTHONPATH=scripts NOCLOTH=1 NOWEAPON=1 $G scripts/arm_hand_gate.py $g review/gates/arm_hand_skin.json --side L=' L ' --side R=' R ' --outer-only --exact > review/gates/arm_hand_skin.txt 2>&1 &
wait
$G scripts/handedness.py source/t2/giant2.glb source/true/giant2_true.glb $e > review/gates/handedness.txt 2>&1
$G ../claude_shared/detached_parts_audit.py $e --fps 24 > review/gates/detached.txt 2>&1
$G ../claude_shared/flat_shading_check.py $e > review/gates/flat.txt 2>&1
$G ../claude_shared/texture_quality.py $e > review/gates/texture_quality.txt 2>&1
python3 ../claude_shared/bone_length_audit.py source/t2/giant2.glb $e > review/gates/bones.txt 2>&1
for c in Walking Running; do $G scripts/stride.py $e $c 'Bip01 L Foot' 'Bip01 R Foot'; done > review/gates/stride.txt 2>&1
$G ../../decorations/mm8_3d/animated/scripts/check_winding.py $e > review/gates/winding.txt 2>&1
echo GATESDONE > review/gates/done.txt
