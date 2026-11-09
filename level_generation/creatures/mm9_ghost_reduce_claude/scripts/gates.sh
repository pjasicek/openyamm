#!/bin/bash
# The Ghost's own numeric gates (../mm9_ghost_claude/scripts/gates.sh) on a candidate, outputs only in this project.
# Usage (project folder): scripts/gates.sh <final.glb> <pre-finish mirrored.glb> <label>  -> review/gates_<label>/
set -u
G=$1; M=$2; L=$3; O=review/gates_$L; mkdir -p "$O" work/gates_$L
V=../claude_shared/gltf_venv/bin/python; S=../mm9_ghost_claude/scripts
$V -W ignore $S/collapse_gate.py "$G" "$O/collapse.json" > "$O/collapse.txt" 2>&1
$V -W ignore ../claude_shared/flat_shading_check.py "$G" > "$O/flat.txt" 2>&1
python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py "$G" > "$O/winding.txt" 2>&1
H="--side L=\" L \" --side R=\" R \" --outer-only --exact --hand-names Hand,Finger,Thumb,Index,Middle,Ring,Pinky --arm-names Clavicle,UpperArm,Forearm,Hand,Finger,Thumb,Index,Middle,Ring,Pinky"
$V -W ignore $S/gate_alias.py "$M" work/gates_$L/alias.glb
$V -W ignore $S/gate_alias.py "$M" work/gates_$L/alias_nh.glb --no-head
eval "$V -W ignore $S/arm_hand_gate.py work/gates_$L/alias_nh.glb $O/arm_hand_nohead.json $H" > "$O/arm_hand_nohead.txt" 2>&1
eval "$V -W ignore $S/arm_hand_gate.py work/gates_$L/alias.glb $O/arm_hand.json $H" > "$O/arm_hand.txt" 2>&1
$V -W ignore $S/jitter_gate.py work/gates_$L/alias.glb ../mm9_ghost_claude/work/ref_alias.glb "$O/jitter.json" --side "L= L " --side "R= R " --clips Standing,Walking,Fidget,Fidget2,Aware,Taunt,AttackMelee,AttackMelee2,AttackRanged,Hit,Hit2 > "$O/jitter.txt" 2>&1
$V -W ignore $S/order_gate.py "$G" "$O/order.json" > "$O/order.txt" 2>/dev/null
$V -W ignore $S/wrist_gate.py "$G" > "$O/wrist.txt" 2>/dev/null
$V -W ignore ../claude_shared/detached_parts_audit.py "$G" --fps 24 --json "$O/detached.json" --md "$O/detached.md" > "$O/detached.txt" 2>&1
$V -W ignore ../claude_shared/texture_quality.py "$G" > "$O/texture_quality.txt" 2>&1 || true
echo "GATES written to $O"
