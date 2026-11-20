#!/usr/bin/env bash
# preview.sh <glb> <tag> [shot names]: viewer GLBs per tier for <glb> as <tag>, manifest, tier A shots (OUT dir)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"
PY=$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python
glb=$(realpath "$1"); tag=$2; shift 2; out=${OUT:-$here/review/followup/shots}; mkdir -p "$out"
cd "$here"
$PY scripts/viewer_variants.py "$glb" $tag 2>&1 | grep -c VIEWER >/dev/null
python3 followup/viewer_manifest.py work/before_followup/mm6_ttn.glb $tag >/dev/null
cd "$repo"; P=level_generation/creatures/$(basename "$here")
python3 level_generation/creatures/claude_shared/texpass_viewer_shots.py shots $P "$out" ${TIERS:-ttn_a_$tag} $(python3 $P/followup/shot_specs.py "$@") | tail -1
