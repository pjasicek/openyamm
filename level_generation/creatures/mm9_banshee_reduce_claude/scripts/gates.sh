#!/bin/bash
# The Banshee's own gates (mm9_banshee_claude/scripts/gates.sh) on one GLB, outputs only in this project:
# review/gates_<label>/. Usage: gates.sh <label> <final glb> <mirrored glb (pre-finish)>
set -u
label=$1; glb=$(realpath "$2"); mir=$(realpath "$3")
P="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; B="$P/../mm9_banshee_claude"
O="$P/review/gates_$label"; W="$P/work/gates_$label"; mkdir -p "$O" "$W"
V="$P/../claude_shared/gltf_venv/bin/python"; CAP="$P/scripts/cap.sh"
cd "$B"
$CAP $V -W ignore scripts/collapse_gate.py "$glb" "$O/collapse.json" > "$O/collapse.txt" 2>&1
$CAP $V -W ignore ../claude_shared/flat_shading_check.py "$glb" > "$O/flat.txt" 2>&1
python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py "$glb" > "$O/winding.txt" 2>&1
[ -f "$P/work/ref_alias.glb" ] || { $V -W ignore scripts/mirror_glb.py work/mm9_banshee_clips.glb "$P/work/ref_mirrored.glb" >/dev/null; $V -W ignore scripts/gate_alias.py "$P/work/ref_mirrored.glb" "$P/work/ref_alias.glb"; }
$V -W ignore scripts/gate_alias.py "$mir" "$W/alias.glb"
$CAP $V -W ignore scripts/arm_hand_gate.py "$W/alias.glb" "$O/arm_hand.json" --side L=" L " --side R=" R " --outer-only --exact \
  --hand-names Hand,Index,Middle,Ring,Thumb --arm-names Clavicle,UpperArm,Forearm,Hand,Index,Middle,Ring,Thumb > "$O/arm_hand.txt" 2>&1
$CAP $V -W ignore scripts/jitter_gate.py "$W/alias.glb" "$P/work/ref_alias.glb" "$O/jitter.json" --side "L= L " --side "R= R " \
  --clips Standing,Walking,Fidget,Fidget2,Taunt,AttackMelee,AttackRanged,AttackRanged2,Hit,Hit2 > "$O/jitter.txt" 2>&1
$CAP $V -W ignore scripts/order_gate.py "$glb" "$O/order.json" > "$O/order.txt" 2>/dev/null
$CAP $V -W ignore scripts/cheek_gate.py ours "$glb" "$O/cheek.json" > "$O/cheek.txt" 2>/dev/null
$CAP $V -W ignore scripts/fold_gate.py "$glb" "$O/fold.json" > "$O/fold.txt" 2>/dev/null
$CAP $V -W ignore scripts/neck_gap_gate.py "$glb" > "$O/neck_gap.txt" 2>&1
$CAP $V -W ignore scripts/bag_gate.py "$glb" > "$O/bag.txt" 2>&1
$CAP $V -W ignore ../claude_shared/detached_parts_audit.py "$glb" --fps 24 --json "$O/detached.json" --md "$O/detached.md" > "$O/detached.txt" 2>&1
echo "GATES $label done"
