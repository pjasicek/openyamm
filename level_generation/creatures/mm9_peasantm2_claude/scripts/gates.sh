#!/bin/bash
# numeric gates (project folder). Writes review/${GD:-gates}/*.
D=review/${GD:-gates}; mkdir -p $D
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python; g=work/pm2_final_clips.glb; e=export/mm9_peasantm2.glb
$G -W ignore scripts/collapse_gate.py $g $D/collapse.json > $D/collapse.txt 2>&1 &
$G -W ignore scripts/arm_hand_gate.py $g $D/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact > $D/arm_hand.txt 2>&1 &
$G -W ignore scripts/skirt_gate.py $g $D/skirt.json > $D/skirt.txt 2>&1 &
wait
$G -W ignore scripts/jitter_gate.py $g work/pm2_ref_h.glb $D/jitter.json --side L=' L ' --side R=' R ' > $D/jitter.txt 2>&1
$G -W ignore scripts/orient_gate.py $e source/true/pm2_src.glb $D/orient.json > $D/orient.txt 2>&1
$G -W ignore scripts/handedness.py source/merged/pm2_a_merged.glb source/true/pm2_a_true.glb $e > $D/handedness.txt 2>&1
$G -W ignore ../claude_shared/detached_parts_audit.py $e --fps 24 > $D/detached.txt 2>&1
$G -W ignore ../claude_shared/flat_shading_check.py $e > $D/flat.txt 2>&1
$G -W ignore ../claude_shared/texture_quality.py $e > $D/texture_quality.txt 2>&1
$G -W ignore ../claude_shared/bone_length_audit.py $e > $D/bones.txt 2>&1
$G -W ignore ../claude_shared/bone_length_audit.py source/true/pm2_a_true.glb > $D/bones_raw.txt 2>&1
echo DONE > $D/done.txt
