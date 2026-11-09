#!/bin/bash
# numeric gates (project folder). Writes review/gates/*.
mkdir -p review/gates
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python; g=work/dwarf_final_clips.glb
$G scripts/collapse_gate.py $g review/gates/collapse.json > review/gates/collapse.txt 2>&1 &
$G scripts/arm_hand_gate.py $g review/gates/arm_hand.json --side L=' L ' --side R=' R ' --outer-only --exact > review/gates/arm_hand.txt 2>&1 &
$G scripts/jitter_gate.py $g work/dwarf_clips0.glb review/gates/jitter.json --side L=' L ' --side R=' R ' > review/gates/jitter.txt 2>&1 &
$G scripts/skirt_gate.py $g review/gates/skirt.json > review/gates/skirt.txt 2>&1 &
$G scripts/skirt_bunch.py $g > review/gates/skirt_bunch.txt 2>&1 &
wait
$G scripts/grip_gate.py $g review/gates/grip.txt > review/gates/grip_log.txt 2>&1 &
$G scripts/blade_gate.py $g review/gates/blade.json RHand1 ' R ' > review/gates/blade.txt 2>&1 &
wait
$G scripts/orient_gate.py export/mm9_dwarf.glb source/true/dwarf_true.glb review/gates/orient.json > review/gates/orient.txt 2>&1
$G scripts/handedness.py source/true/dwarf_true.glb source/true/dwarf_true.glb export/mm9_dwarf.glb > review/gates/handedness.txt 2>&1
python3 ../claude_shared/bone_length_audit.py export/mm9_dwarf.glb > review/gates/bone_length.txt 2>&1
$G ../claude_shared/detached_parts_audit.py export/mm9_dwarf.glb --fps 24 > review/gates/detached.txt 2>&1
$G ../claude_shared/flat_shading_check.py export/mm9_dwarf.glb > review/gates/flat.txt 2>&1
$G ../claude_shared/texture_quality.py export/mm9_dwarf.glb > review/gates/texture_quality.txt 2>&1
NOCLOTH=1 $G scripts/arm_hand_gate.py $g review/gates/arm_hand_skin.json --side L=' L ' --side R=' R ' --outer-only --exact > review/gates/arm_hand_skin.txt 2>&1
$G scripts/wrist_gap_gate.py $g > review/gates/wrist_gap.txt 2>&1     # run 2: glove against the bracer's mouth
$G scripts/rim_gate.py $g review/gates/rim.json > review/gates/rim.txt 2>&1      # run 2: helmet by layer, replaces the HEADMAT blade gate (it counted the neck tube in the collar)
$G scripts/beard_gate.py $g > review/gates/beard.txt 2>&1
(cd ../../..; python3 level_generation/creatures/claude_shared/floor/floor_audit.py --world mm9 --match 'MM9 Dwarf*' > level_generation/creatures/mm9_dwarf_claude/review/gates/floor.txt 2>&1)
