#!/bin/bash
# numeric gates (project folder). Writes review/${GD:-gates}/*.
D=review/${GD:-gates}; mkdir -p $D
export PYTHONPATH=/usr/lib/python3/dist-packages
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python; g=work/kira_final_clips.glb; e=export/mm9_kira.glb
$G -W ignore scripts/collapse_gate.py $g $D/collapse.json > $D/collapse.txt 2>&1 &
$G -W ignore scripts/arm_hand_gate.py $g $D/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact > $D/arm_hand.txt 2>&1 &
$G -W ignore scripts/skirt_gate.py $g $D/skirt.json > $D/skirt.txt 2>&1 &
wait
$G -W ignore scripts/jitter_gate.py $g work/kira_clips0.glb $D/jitter.json --side L=' L ' --side R=' R ' > $D/jitter.txt 2>&1
$G -W ignore ../claude_shared/detached_parts_audit.py $e --fps 24 > $D/detached.txt 2>&1
$G -W ignore ../claude_shared/flat_shading_check.py $e > $D/flat.txt 2>&1
$G -W ignore ../claude_shared/texture_quality.py $e > $D/texture_quality.txt 2>&1
$G -W ignore ../claude_shared/bone_length_audit.py $e > $D/bones.txt 2>&1
$G -W ignore ../claude_shared/bone_length_audit.py source/true/kira_true.glb > $D/bones_raw.txt 2>&1
$G -W ignore scripts/sleeve_poke_gate.py $g $D/sleeve_poke_inside.json --hand-pos work/hand_pos.npy --past 0.0 > $D/sleeve_poke_inside.txt 2>&1
$G -W ignore scripts/sleeve_poke_gate.py $g $D/sleeve_poke.json --hand-pos work/hand_pos.npy > $D/sleeve_poke.txt 2>&1
(cd /home/pjasicek/github/OpenYAMM && $G -W ignore level_generation/creatures/claude_shared/floor/floor_audit.py --world mm9 --match 'MM9 251*') > $D/floor.txt 2>&1
python3 /home/pjasicek/github/OpenYAMM/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py $e > $D/winding.txt 2>&1
echo DONE > $D/done.txt
