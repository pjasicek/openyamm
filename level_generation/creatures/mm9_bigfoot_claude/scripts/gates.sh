#!/bin/bash
# numeric gates (project folder). Writes review/gates/*.
mkdir -p review/gates
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python; g=work/bf_final_clips.glb
$G scripts/collapse_gate.py $g review/gates/collapse.json > review/gates/collapse.txt 2>&1 &
# run 2: against MM9's clips with the same half-joint helpers (bf_clips0 had none: every helper-skinned vertex differed); strict, relative, and the hand corrections alone against the abducted clips they start from
$G scripts/jitter_gate.py $g work/bf_ref_clips.glb review/gates/jitter.json --side L=' L ' --side R=' R ' > review/gates/jitter.txt 2>&1 &
$G scripts/jitter_gate.py $g work/bf_ref_clips.glb review/gates/jitter_rel.json --side L=' L ' --side R=' R ' --rel 0.25 > review/gates/jitter_rel.txt 2>&1 &
$G scripts/jitter_gate.py $g work/bf_clips2.glb review/gates/jitter_corrections.json --side L=' L ' --side R=' R ' > review/gates/jitter_corrections.txt 2>&1 &
wait
$G scripts/handedness.py source/t1/bigfoot1.glb source/true/bigfoot1_true.glb export/mm9_bigfoot.glb > review/gates/handedness.txt 2>&1
$G ../claude_shared/detached_parts_audit.py export/mm9_bigfoot.glb --fps 24 > review/gates/detached.txt 2>&1
$G ../claude_shared/flat_shading_check.py export/mm9_bigfoot.glb > review/gates/flat.txt 2>&1
$G ../claude_shared/texture_quality.py export/mm9_bigfoot.glb > review/gates/texture_quality.txt 2>&1
PYTHONPATH=scripts NOCLOTH=1 $G scripts/arm_hand_gate.py $g review/gates/arm_hand_skin.json --side L=' L ' --side R=' R ' --outer-only --exact > review/gates/arm_hand_skin.txt 2>&1
python3 ../claude_shared/bone_length_audit.py source/t1/bigfoot1.glb export/mm9_bigfoot.glb > review/gates/bones.txt 2>&1
for c in Walking Running; do $G scripts/stride.py export/mm9_bigfoot.glb $c 'Bip01 L Foot' 'Bip01 R Foot'; done > review/gates/stride.txt 2>&1
$G ../../decorations/mm8_3d/animated/scripts/check_winding.py export/mm9_bigfoot.glb > review/gates/winding.txt 2>&1
echo GATESDONE > review/gates/done.txt
