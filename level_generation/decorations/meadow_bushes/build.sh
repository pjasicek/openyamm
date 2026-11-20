#!/usr/bin/env bash
# Rebuild the meadow bushes: shared textures -> Blender models (three LODs each, in parallel) -> review renders and
# sheet -> finish (material modes, LOD link, card cutting, validation) [--install: tools/install_model.py --engine].
# Usage: build.sh [--install] [id ...]   (default: all four)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender=/snap/bin/blender
cd "$here"
install=()
ids=()
for arg in "$@"; do
  if [[ "$arg" == --install ]]; then install=(--install); else ids+=("$arg"); fi
done
[[ ${#ids[@]} -gt 0 ]] || ids=(meadow_bush01 meadow_bush02 meadow_bush03 meadow_bush04)
mkdir -p work/logs review
python3 scripts/make_textures.py
for id in "${ids[@]}"; do
  ( "$blender" --background --python scripts/build_bush.py -- "$id" > "work/logs/$id.log" 2>&1
    grep -qE "^EXPORTED" "work/logs/$id.log" || { echo "build failed: $id (work/logs/$id.log)"; exit 1; }
    "$blender" --background --python scripts/render_review.py -- "$id" > "work/logs/${id}_review.log" 2>&1 ) &
done
wait
for id in "${ids[@]}"; do
  grep -E "^LOD" "work/logs/$id.log"
  python3 scripts/finish.py "$id" "${install[@]}"
done
python3 scripts/sheet.py
"$blender" --background --python scripts/lineup.py > work/logs/lineup.log 2>&1 || echo "lineup render failed (work/logs/lineup.log)"
