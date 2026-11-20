#!/usr/bin/env bash
# Viewer GLBs, manifest and identical-camera shots of the new GLB into review/shots_after (overwritten by name).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"
PY=$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python
cd "$here"
$PY scripts/viewer_variants.py export/mm6_ttn.glb hands 2>&1 | grep -c VIEWER
$PY scripts/viewer_manifest.py 2>&1 | grep MANIFEST
cd "$repo"; P=level_generation/creatures/$(basename "$here")
SPECS=$(python3 $P/scripts/shot_specs.py "$@")
mkdir -p $P/review/shots_after
python3 level_generation/creatures/claude_shared/texpass_viewer_shots.py shots $P $P/review/shots_after ttn_a_hands $SPECS | tail -1
for x in $P/review/shots_after/ttn_a_hands_*.png; do mv "$x" "${x/ttn_a_hands_/ttn_a_}"; done
