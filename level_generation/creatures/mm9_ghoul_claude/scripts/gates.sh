#!/bin/bash
# all numeric gates on the runtime GLB (project folder). Writes review/gates/*. Reference for jitter: MM9's clips with the helper keys, before arm and floor corrections.
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_ghoul_claude; mkdir -p review/gates
G=$PWD/../claude_shared/gltf_venv/bin/python; g=export/mm9_ghoul.glb
$G scripts/collapse_gate.py $g review/gates/collapse.json 2>&1 | grep -v Unexpected > review/gates/collapse.txt &
PYTHONPATH=scripts $G scripts/arm_hand_gate.py $g review/gates/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact --hand-names Hand,Finger --arm-names Clavicle,UpperArm,Forearm,Hand,Finger 2>&1 | grep -v Unexpected > review/gates/arm_hand.txt &
$G scripts/jitter_gate.py $g work/ghoul_clips1.glb review/gates/jitter.json --side L=' L ' --side R=' R ' 2>&1 | grep -v Unexpected > review/gates/jitter.txt &
$G scripts/flap_gate.py $g review/gates/flap.json 2>&1 | grep -v Unexpected > review/gates/flap.txt &
$G ../claude_shared/detached_parts_audit.py $g --fps 24 2>&1 | grep -v Unexpected > review/gates/detached.txt &
$G ../claude_shared/flat_shading_check.py $g 2>&1 | grep -v Unexpected > review/gates/flat.txt &
wait
$G ../claude_shared/texture_quality.py export/mm9_ghoul.glb 2>&1 | grep -v Unexpected > review/gates/texture_quality.txt
$G ../claude_shared/bone_length_audit.py $g 2>&1 | grep -v Unexpected > review/gates/bone_length.txt; $G scripts/prim_cover.py $g 2>&1 | grep -v Unexpected > review/gates/prim_cover.txt
echo GATES DONE
