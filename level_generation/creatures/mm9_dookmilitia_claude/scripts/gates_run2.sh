#!/bin/bash
# Every gate on the final build (run 2). Project folder. Writes review/gates/*. Floor audit and regression need the install (run after it).
mkdir -p review/gates
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python; g=work/dook_final_clips.glb; e=export/mm9_dookmilitia.glb
$G scripts/collapse_gate.py $g review/gates/collapse.json > review/gates/collapse.txt 2>&1 &
$G scripts/arm_hand_gate.py $g review/gates/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact > review/gates/arm_hand.txt 2>&1 &
NOCLOTH=1 $G scripts/arm_hand_gate.py $g review/gates/arm_hand_skin.json --side L=' L ' --side R=' R ' --outer-only --exact > review/gates/arm_hand_skin.txt 2>&1 &
$G scripts/jitter_gate.py $g work/dook_clips0.glb review/gates/jitter.json --side L=' L ' --side R=' R ' > review/gates/jitter.txt 2>&1 &
wait
$G scripts/skirt_gate.py $g review/gates/skirt.json > review/gates/skirt.txt 2>&1 &
$G scripts/cloth_torso_gate.py $g review/gates/cloth_torso.json > review/gates/cloth_torso.txt 2>&1 &
$G scripts/blade_gate.py $g review/gates/sword.json Ybasesword ' X ' > review/gates/sword.txt 2>&1 &
$G scripts/grip_gate.py $g review/gates/grip.txt > review/gates/grip.log 2>&1 &
wait
$G ../claude_shared/detached_parts_audit.py $e --fps 24 > review/gates/detached.txt 2>&1 &
$G ../claude_shared/bone_length_audit.py $e > review/gates/bones.txt 2>&1 &
$G scripts/orient_gate.py $e source/true/dook1_true.glb review/gates/orient.json > review/gates/orient.txt 2>&1 &
$G scripts/handedness.py work/merged1.glb source/true/dook1_true.glb $e > review/gates/handedness.txt 2>&1 &
wait
$G ../claude_shared/flat_shading_check.py $e > review/gates/flat.txt 2>&1
$G ../claude_shared/texture_quality.py $e > review/gates/texture_quality.txt 2>&1
$G ../../decorations/mm8_3d/animated/scripts/check_winding.py $e > review/gates/winding.txt 2>&1
$G scripts/clip_floor.py $e > review/gates/clip_floor.txt 2>&1
echo GATESDONE
