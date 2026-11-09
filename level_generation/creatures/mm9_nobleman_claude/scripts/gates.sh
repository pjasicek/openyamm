#!/bin/bash
# numeric gates (project folder). Writes review/gates/*.
mkdir -p review/gates
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python; g=work/nb_final_clips.glb; e=export/mm9_nobleman.glb
$G -W ignore scripts/collapse_gate.py $g review/gates/collapse.json > review/gates/collapse.txt 2>&1 &
$G -W ignore scripts/arm_hand_gate.py $g review/gates/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact > review/gates/arm_hand.txt 2>&1 &
$G -W ignore scripts/skirt_gate.py $g review/gates/skirt.json > review/gates/skirt.txt 2>&1 &
wait
$G -W ignore scripts/jitter_gate.py $g work/nb_clips0.glb review/gates/jitter.json --side L=' L ' --side R=' R ' > review/gates/jitter.txt 2>&1
$G -W ignore scripts/orient_gate.py $e source/true/nobleman1_true.glb review/gates/orient.json > review/gates/orient.txt 2>&1
$G -W ignore scripts/handedness.py source/n1/nobleman1.glb source/true/nobleman1_true.glb $e > review/gates/handedness.txt 2>&1
$G -W ignore ../claude_shared/detached_parts_audit.py $e --fps 24 > review/gates/detached.txt 2>&1
$G -W ignore ../claude_shared/flat_shading_check.py $e > review/gates/flat.txt 2>&1
$G -W ignore ../claude_shared/texture_quality.py $e > review/gates/texture_quality.txt 2>&1
$G -W ignore ../claude_shared/bone_length_audit.py $e > review/gates/bones.txt 2>&1
$G -W ignore ../claude_shared/bone_length_audit.py source/n1/nobleman1.glb > review/gates/bones_raw.txt 2>&1
NOCLOTH=1 $G -W ignore scripts/arm_hand_gate.py $g review/gates/arm_hand_skin.json --side L=' L ' --side R=' R ' --outer-only --exact > review/gates/arm_hand_skin.txt 2>&1
echo DONE > review/gates/done.txt
