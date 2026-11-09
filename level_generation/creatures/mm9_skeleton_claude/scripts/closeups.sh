#!/usr/bin/env bash
# viewer close-ups: scripts/closeups.sh <glb> <tier id or -> <out sheet> <clip:sec> <joint:ox,oy,oz:dist> ...
set -eo pipefail
cd "$(dirname "$0")/.."; G=../claude_shared/gltf_venv/bin/python
glb=$1; tier=$2; out=$3; cs=$4; shift 4
pre="cu$(date +%s%N | cut -c6-13)_"
specs=$($G scripts/close_specs.py "$glb" "$pre" "$cs" "$@" 2>/dev/null)
url=$(python3 scripts/viewer_url.py "$tier")
node ../mm8_m424_claude/scripts/viewer_shots.mjs "$url" review/shots $specs | tail -1 | cut -c1-120
cd review/shots
/usr/bin/python3 ../../scripts/shots_sheet.py "../$out" 4 ${CELL:-600} ${pre}*.png
