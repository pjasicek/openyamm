#!/usr/bin/env bash
# Texture pass, from the graded paint to the viewer: match_approved -> restore_pebbles -> compose -> export -> runtime -> viewer tiers -> shots.
# Usage: TOKEN=<lease> rebuild_texpass.sh [--install]. The one-time steps before it are in the README.
set -euo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"; cd "$repo"
P=level_generation/creatures/mm9_eye_claude
python3 $P/scripts/match_approved.py | cut -c1-400
python3 $P/scripts/restore_pebbles.py ${PEBBLE_ARGS:-}
python3 $P/scripts/compose.py | tail -1 | cut -c1-500
tools/run_creature_blender.sh --token "$TOKEN" $P/scripts/build_export.py $P/work/uv_v2.blend $P/work/anim_v4.blend $P/export/mm9_eye_lod0.glb $P/work/clips_v4.json | tail -1
python3 tools/creature_workspace.py run --project $P --token "$TOKEN" -- $P/scripts/build_runtime.sh ${1:-} 2>&1 | grep -E "hover 1|WINDING|LOD triangles|Traceback|Error|Installed|installed"
python3 $P/scripts/viewer_tiers.py > /dev/null
python3 $P/scripts/make_viewer_manifest.py r5_eye_pebbles_20261030 "eye_a=Eye (Eye A)=$P/review/viewer/eye_a.glb" \
  "eye_b=Orbus (Eye B)=$P/review/viewer/eye_b.glb" "eye_c=Oculus (Eye C)=$P/review/viewer/eye_c.glb" > /dev/null
python3 $P/scripts/pebble_shots.py restored | tail -1
