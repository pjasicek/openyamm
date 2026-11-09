#!/usr/bin/env bash
# Texture pass rebuild after the textures changed: compose (ramps on the graded paint) -> export -> runtime -> viewer.
# Usage: scripts/texpass_rebuild.sh <lease token> [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$repo"
T=$1; P=level_generation/creatures/mm9_basilisk_claude
python3 $P/scripts/compose.py basilisk
tools/run_creature_blender.sh --token "$T" $P/scripts/build_export.py $P/work/uv_v2.blend basilisk $P/work/anim_v2.blend \
  $P/export/mm9_basilisk_lod0.glb $P/work/clips_v2.json
python3 tools/creature_workspace.py run --project $P --token "$T" -- $P/scripts/build_runtime.sh basilisk ${2:-}
python3 $P/scripts/viewer_tiers.py basilisk
python3 $P/scripts/make_viewer_manifest.py r2_basilisk_texpass_20261030 \
  "basilisk_a=Basilisk / Fibrase Basilisk (A, B)=$P/review/viewer/basilisk_a.glb" \
  "basilisk_c=King Basilisk (C)=$P/review/viewer/basilisk_c.glb"
