#!/usr/bin/env bash
# The Skeleton Warrior's own gates (../mm9_skeletonwarrior_claude README "Checks" and "Skirt fix"; scripts copied here) on one
# runtime GLB: winding, flat shading, texture quality, arm/hand (--outer-only --exact), skirt (thigh through plates, 48 fps),
# detached parts (24 fps). Clips and skin are byte-identical to the installed file, so jitter, bone lengths and handedness
# are not rerun. Project folder. Usage: scripts/gates.sh <glb> <out dir>
set -uo pipefail
cd "$(dirname "$0")/.."; X=$1; R=$2; mkdir -p $R
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -I"
$G ../../decorations/mm8_3d/animated/scripts/check_winding.py $X 2>&1 | grep -E 'INVERTED|WINDING|inverted' > $R/g_winding.txt
$G ../claude_shared/flat_shading_check.py $X 2>&1 | grep -v frozen | tail -4 > $R/g_flat.txt
$G ../claude_shared/texture_quality.py $X 2>&1 | grep -v frozen | tail -8 > $R/g_texture.txt
$G scripts/arm_hand_gate.py $X $R/arm_hand_gate.json --side L=' L ' --side R=' R ' --outer-only --exact 2>&1 | grep -v frozen > $R/arm_hand_gate.txt
$G scripts/skirt_gate.py $X $R/skirt_gate.json 2>&1 | grep -v frozen > $R/skirt_gate.txt
$G ../claude_shared/detached_parts_audit.py $X --fps 24 --json $R/detached.json --md $R/detached.md 2>&1 | grep -v frozen > $R/detached.txt
echo gates done > $R/done.txt
