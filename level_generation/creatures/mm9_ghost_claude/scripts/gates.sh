#!/bin/bash
# all numeric gates on export/mm9_ghost.glb, from the project folder; output review/gates/
V=../claude_shared/gltf_venv/bin/python
mkdir -p review/gates
$V -W ignore scripts/collapse_gate.py export/mm9_ghost.glb review/gates/collapse.json 2>&1 | tee review/gates/collapse.txt | cut -c1-210
$V -W ignore ../claude_shared/flat_shading_check.py export/mm9_ghost.glb 2>&1 | tail -6 | cut -c1-120
python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py export/mm9_ghost.glb | tail -1
$V -W ignore scripts/mirror_glb.py work/mm9_ghost_clips.glb work/ref_mirrored.glb | tail -1
$V -W ignore scripts/gate_alias.py work/ref_mirrored.glb work/ref_alias.glb
# the arm gate reads the build before finish_blend.py: the robe lining sits on the outer faces with flipped normals, so any point near the robe reads as deep inside it
H="--side L=\" L \" --side R=\" R \" --outer-only --exact --hand-names Hand,Finger,Thumb,Index,Middle,Ring,Pinky --arm-names Clavicle,UpperArm,Forearm,Hand,Finger,Thumb,Index,Middle,Ring,Pinky"
$V -W ignore scripts/gate_alias.py export/mm9_ghost_mirrored.glb work/ghost_alias.glb
$V -W ignore scripts/gate_alias.py export/mm9_ghost_mirrored.glb work/ghost_alias_nh.glb --no-head
eval "$V -W ignore scripts/arm_hand_gate.py work/ghost_alias_nh.glb review/gates/arm_hand_nohead.json $H" 2>&1 | tail -15 | tee review/gates/arm_hand_nohead.txt | cut -c1-170
eval "$V -W ignore scripts/arm_hand_gate.py work/ghost_alias.glb review/gates/arm_hand.json $H" 2>&1 | tail -15 | tee review/gates/arm_hand.txt | cut -c1-170
$V -W ignore scripts/jitter_gate.py work/ghost_alias.glb work/ref_alias.glb review/gates/jitter.json --side "L= L " --side "R= R " --clips Standing,Walking,Fidget,Fidget2,Aware,Taunt,AttackMelee,AttackMelee2,AttackRanged,Hit,Hit2 2>&1 | tail -18 | tee review/gates/jitter.txt | cut -c1-170
$V -W ignore scripts/order_gate.py export/mm9_ghost.glb review/gates/order.json 2>/dev/null | tee review/gates/order.txt | cut -c1-140
$V -W ignore scripts/wrist_gate.py export/mm9_ghost.glb 2>/dev/null > review/gates/wrist.txt
$V -W ignore ../claude_shared/detached_parts_audit.py export/mm9_ghost.glb --fps 24 --json review/gates/detached.json --md review/gates/detached.md 2>&1 | tail -8 | cut -c1-170
