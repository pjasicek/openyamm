#!/usr/bin/env bash
# Texture pass, from the graded paint to the viewer: compose -> export -> runtime -> viewer tiers -> shots.
# Usage: TOKEN=<lease> rebuild_texpass.sh [--install]. The one-time steps before it are in the README.
set -euo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"; cd "$repo"
P=level_generation/creatures/mm9_terror_claude
python3 $P/scripts/compose.py terror | tail -1 | cut -c1-500
tools/run_creature_blender.sh --token "$TOKEN" $P/scripts/build_export.py $P/work/uv_v3.blend terror $P/work/anim_v3.blend $P/export/mm9_terror_lod0.glb $P/work/clips_v3.json | tail -1
python3 tools/creature_workspace.py run --project $P --token "$TOKEN" -- $P/scripts/build_runtime.sh terror ${1:-} 2>&1 | grep -E "WINDING|LOD triangles|Traceback|Error|Installed|installed"
python3 $P/scripts/viewer_tiers.py terror > /dev/null
python3 $P/scripts/make_viewer_manifest.py r3_terror_texpass_20261030 "terror_a=Amphibious Terror (A)=$P/review/viewer/terror_a.glb" \
  "terror_b=Desert Terror (B)=$P/review/viewer/terror_b.glb" "terror_c=Reptilian Terror (C)=$P/review/viewer/terror_c.glb" > /dev/null
TOKEN="$TOKEN" $P/scripts/texpass_shots.sh after | tail -1
