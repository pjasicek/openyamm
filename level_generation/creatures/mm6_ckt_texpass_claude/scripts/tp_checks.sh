#!/usr/bin/env bash
# Checks of a texture-pass export against its installed GLB (run from anywhere):
#   tp_checks.sh <before glb> <after glb> <approved prefix> <layout npz>   (TP_CONFIG selects a second world's config)
set -uo pipefail
K="$(cd "$(dirname "$0")" && pwd)"
R="$(cd "$K/../../../.." && pwd)"
B=$(realpath "$1"); A=$(realpath "$2"); AP=$(realpath -m "$3"); LY=$(realpath "$4")
cd "$K"
echo "== diff";      python3 tp_diff.py "$B" "$A" | tail -4
echo "== winding";   python3 "$R/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "$A" | tail -1
echo "== flat";      python3 "$R/level_generation/creatures/claude_shared/flat_shading_check.py" "$A" | tail -1
echo "== quality";   python3 "$R/level_generation/creatures/claude_shared/texture_quality.py" "$B" "$A" | grep -v '^    '
echo "== lod1";      python3 tp_lod1_check.py "$B" "$A"
echo "== tiers";     python3 tp_tier_tone.py "$A" "$AP" "$LY" | python3 -c "
import json,sys
for m,v in json.load(sys.stdin).items():
    for c,x in v.items(): print(m, c, x['share'], x['approved'], x['pass'], 'sd', x['sd'])"
