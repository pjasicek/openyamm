#!/bin/bash
# numeric gates (project folder). Writes review/gates/*. Jitter against MM9's clips with the same fist, staff fix and helpers (work/yan_ref_clips.glb).
mkdir -p review/gates
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python; g=work/yan_final_clips.glb; e=export/mm9_yanmir.glb
$G scripts/collapse_gate.py $g review/gates/collapse.json > review/gates/collapse.txt 2>&1 &
$G scripts/jitter_gate.py $g work/yan_ref_clips.glb review/gates/jitter.json --side L=' L ' --side R=' R ' > review/gates/jitter.txt 2>&1 &
$G scripts/jitter_gate.py $g work/yan_ref_clips.glb review/gates/jitter_rel.json --side L=' L ' --side R=' R ' --rel 0.25 > review/gates/jitter_rel.txt 2>&1 &
$G scripts/staff_gate.py $g review/gates/staff.json Ystaff 'Bip01 R ' > review/gates/staff.txt 2>&1 &
wait
PYTHONPATH=scripts NOCLOTH=1 $G scripts/arm_hand_gate.py $g review/gates/arm_hand_skin.json --side L=' L ' --side R=' R ' --outer-only --exact > review/gates/arm_hand_skin.txt 2>&1 &
$G scripts/staff_gate.py $g review/gates/beard.json 'Bip01 Ponytail1' 'Bip01 Head ' > review/gates/beard.txt 2>&1 &      # the beard (Ponytail1) against the chest and shoulders
$G scripts/handedness.py source/raw/yanmir.glb source/true/yanmir_true.glb $e > review/gates/handedness.txt 2>&1
$G ../claude_shared/detached_parts_audit.py $e --fps 24 > review/gates/detached.txt 2>&1
$G ../claude_shared/detached_parts_audit.py $e --fps 24 --clips $(python3 -c "import json,struct;d=open('$e','rb').read();n=struct.unpack('<I',d[12:16])[0];print(','.join(a['name'] for a in json.loads(d[20:20+n])['animations'] if a['name']!='AttackMeleeSave'))") > review/gates/detached_no_save.txt 2>&1
$G ../claude_shared/flat_shading_check.py $e > review/gates/flat.txt 2>&1
$G ../claude_shared/texture_quality.py $e > review/gates/texture_quality.txt 2>&1
python3 ../claude_shared/bone_length_audit.py source/raw/yanmir.glb source/true/yanmir_true.glb $e > review/gates/bones.txt 2>&1
for c in Walking Running; do $G scripts/stride.py $e $c 'Bip01 L Foot' 'Bip01 R Foot'; done > review/gates/stride.txt 2>&1
$G ../../decorations/mm8_3d/animated/scripts/check_winding.py $e > review/gates/winding.txt 2>&1
wait
echo GATESDONE > review/gates/done.txt
