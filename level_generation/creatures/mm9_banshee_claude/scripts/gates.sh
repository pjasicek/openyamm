#!/bin/bash
# all numeric gates on export/mm9_banshee.glb, from the project folder; output review/gates/
V=../claude_shared/gltf_venv/bin/python
mkdir -p review/gates
$V -W ignore scripts/collapse_gate.py export/mm9_banshee.glb review/gates/collapse.json 2>&1 | tee review/gates/collapse.txt | cut -c1-230
$V -W ignore ../claude_shared/flat_shading_check.py export/mm9_banshee.glb 2>&1 | tail -6 | cut -c1-120
python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py export/mm9_banshee.glb | tail -1
$V -W ignore scripts/mirror_glb.py work/mm9_banshee_clips.glb work/ref_mirrored.glb | tail -1
$V -W ignore scripts/gate_alias.py work/ref_mirrored.glb work/ref_alias.glb
H="--side L=\" L \" --side R=\" R \" --outer-only --exact --hand-names Hand,Index,Middle,Ring,Thumb --arm-names Clavicle,UpperArm,Forearm,Hand,Index,Middle,Ring,Thumb"
$V -W ignore scripts/gate_alias.py export/mm9_banshee_mirrored.glb work/banshee_alias.glb
$V -W ignore scripts/gate_alias.py export/mm9_banshee_mirrored.glb work/banshee_alias_nh.glb --no-head
eval "$V -W ignore scripts/arm_hand_gate.py work/banshee_alias.glb review/gates/arm_hand.json $H" 2>&1 | tail -16 | tee review/gates/arm_hand.txt | cut -c1-170
$V -W ignore scripts/jitter_gate.py work/banshee_alias.glb work/ref_alias.glb review/gates/jitter.json --side "L= L " --side "R= R " --clips Standing,Walking,Fidget,Fidget2,Taunt,AttackMelee,AttackRanged,AttackRanged2,Hit,Hit2 2>&1 | tail -18 | tee review/gates/jitter.txt | cut -c1-170
$V -W ignore scripts/order_gate.py export/mm9_banshee.glb review/gates/order.json 2>/dev/null | tee review/gates/order.txt | cut -c1-200
$V -W ignore scripts/cheek_gate.py ours export/mm9_banshee.glb review/gates/cheek.json 2>/dev/null | tee review/gates/cheek.txt | cut -c1-120
$V -W ignore scripts/fold_gate.py export/mm9_banshee.glb review/gates/fold.json 2>/dev/null | tee review/gates/fold.txt | cut -c1-120
$V -W ignore scripts/neck_gap_gate.py export/mm9_banshee.glb | tail -1
$V -W ignore scripts/bag_gate.py export/mm9_banshee.glb | tail -1
$V -W ignore ../claude_shared/detached_parts_audit.py export/mm9_banshee.glb --fps 24 --json review/gates/detached.json --md review/gates/detached.md 2>&1 | tail -8 | cut -c1-170
