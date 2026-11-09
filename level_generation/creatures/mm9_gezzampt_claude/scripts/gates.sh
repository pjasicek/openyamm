#!/bin/bash
# numeric gates (project folder). Writes review/gates/*.
mkdir -p review/gates
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python; g=work/gezz_final_clips.glb
$G scripts/collapse_gate.py $g review/gates/collapse.json > review/gates/collapse.txt 2>&1 &
$G scripts/jitter_gate.py $g work/gezz_clips0.glb review/gates/jitter.json --side L=' L ' --side R=' R ' > review/gates/jitter.txt 2>&1 &
wait
$G scripts/orient_gate.py export/mm9_gezzampt.glb source/true/gezzampt1_true.glb review/gates/orient.json > review/gates/orient.txt 2>&1
$G scripts/handedness.py source/t1/gezzampt1.glb source/true/gezzampt1_true.glb export/mm9_gezzampt.glb > review/gates/handedness.txt 2>&1
$G ../claude_shared/detached_parts_audit.py export/mm9_gezzampt.glb --fps 24 > review/gates/detached.txt 2>&1
$G ../claude_shared/flat_shading_check.py export/mm9_gezzampt.glb > review/gates/flat.txt 2>&1
$G ../claude_shared/texture_quality.py export/mm9_gezzampt.glb > review/gates/texture_quality.txt 2>&1
NOCLOTH=1 $G scripts/arm_hand_gate.py $g review/gates/arm_hand_skin.json --side L=' L ' --side R=' R ' --outer-only --exact > review/gates/arm_hand_skin.txt 2>&1
