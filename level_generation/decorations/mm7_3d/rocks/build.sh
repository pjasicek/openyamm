#!/usr/bin/env bash
# Rebuild the MM7 scan rocks (see README.md): scripts/build_rock.py with rocks.json -> review renders and sheet ->
# link LODs -> validate; --install then installs each with tools/install_model.py as engine/models/mm7_deco_<rock>.glb.
# Usage: build.sh [--install] [--regrade] [rock...]   (no rock names: all of them)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd -- "$here/../../../.." && pwd)"
blender=/snap/bin/blender
install=; regrade=
while [[ "${1:-}" == --* ]]; do
  case "$1" in --install) install=1 ;; --regrade) regrade=--regrade ;; *) echo "unknown $1"; exit 1 ;; esac; shift
done
rocks=("$@")
if (( ${#rocks[@]} == 0 )); then mapfile -t rocks < <(python3 -c "import json; print('\n'.join(json.load(open('$here/rocks.json'))))"); fi
cd "$here/scripts"
for rock in "${rocks[@]}"; do
  mkdir -p "$here/work/$rock"
  "$blender" --background --python-exit-code 1 --python build_rock.py -- "$rock" $regrade > "$here/work/$rock/build.log" 2>&1 \
    || { tail -20 "$here/work/$rock/build.log"; exit 1; }
  grep -E '^BUILD (high|lod|albedo|exported)' "$here/work/$rock/build.log"
  "$blender" --background --python-exit-code 1 --python review_render.py -- "$rock" > "$here/work/$rock/review.log" 2>&1
  python3 review_sheet.py "$rock"
  cp "$here/work/$rock/review/${rock}_review.png" "$here/review/${rock}_review.png"
  python3 "$repo/tools/link_static_model_lods.py" "$here/work/$rock/${rock}_export.glb" "$here/work/$rock/${rock}_linked.glb"
  python3 validate_glb.py "$here/work/$rock/${rock}_linked.glb"
  if [[ -n "$install" ]]; then
    python3 "$repo/tools/install_model.py" "$here/work/$rock/${rock}_linked.glb" --engine --name "mm7_deco_${rock}.glb"
  fi
done
