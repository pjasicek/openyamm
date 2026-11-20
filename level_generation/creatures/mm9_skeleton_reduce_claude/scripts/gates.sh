#!/usr/bin/env bash
# The skeleton's own numeric gates (../mm9_skeleton_claude/scripts/final_gates.sh, copied here; scrap and hand-bone
# gates read the creature's pid_dump) plus the detached-parts audit at 24 fps, on one runtime GLB. Project folder.
# Usage: scripts/gates.sh <glb> <out dir>
set -uo pipefail
cd "$(dirname "$0")/.."; X=$1; R=$2; mkdir -p $R
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -I"
$G ../../decorations/mm8_3d/animated/scripts/check_winding.py $X 2>&1 | grep -E 'INVERTED|WINDING' > $R/g_winding.txt
$G ../claude_shared/flat_shading_check.py $X 2>&1 | grep -v frozen | tail -3 > $R/g_flat.txt
$G ../claude_shared/texture_quality.py $X 2>&1 | grep -v frozen | tail -6 > $R/g_texture.txt
$G scripts/collapse_gate.py $X $R/collapse_body.json 0 2>&1 | grep -v frozen > $R/collapse_body.txt
$G scripts/collapse_gate.py $X $R/collapse_head.json 1 2>&1 | grep -v frozen > $R/collapse_head.txt
$G scripts/scrap_gate.py $X 1.1193 $R/scrap_gate.json 2>&1 | grep -v frozen > $R/scrap_gate.txt
$G scripts/hand_bone_gate.py $X 1.1193 $R/hand_bone_gate.json 2>&1 | grep -v frozen > $R/hand_bone_gate.txt
$G scripts/arm_hand_gate.py $X $R/arm_hand_gate.json --side L=' L ' --side R=' R ' --outer-only --exact 2>&1 | grep -v frozen > $R/arm_hand_gate.txt
$G ../claude_shared/detached_parts_audit.py $X --fps 24 --json $R/detached.json --md $R/detached.md 2>&1 | grep -v frozen > $R/detached.txt
echo gates done > $R/done.txt
