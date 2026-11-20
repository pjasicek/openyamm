#!/usr/bin/env bash
# Rebuild the MM6 succulents from scratch: procedural textures -> Blender models (4 LODs each) -> review renders and
# sheets -> finish (material modes, LOD link, card cutting, validation) [--install copies them to
# assets_dev/worlds/mm6/models as mm6_deco_<id>.glb]. Usage: build.sh [--install] [id ...]  (default: all eight)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender=/snap/bin/blender
cd "$here"
install=()
ids=()
failed=()
for arg in "$@"; do
  if [[ "$arg" == --install ]]; then install=(--install); else ids+=("$arg"); fi
done
[[ ${#ids[@]} -gt 0 ]] || ids=(cac8 cac5 cac16 cac7 cac10 cac15 cac27 snoweed1)
mkdir -p work/logs review
python3 scripts/make_textures.py
for id in "${ids[@]}"; do
  "$blender" --background --python scripts/build_model.py -- "$id" > "work/logs/$id.log" 2>&1 &
done
wait
for id in "${ids[@]}"; do
  grep -qE "^EXPORTED" "work/logs/$id.log" || { echo "build failed: $id (work/logs/$id.log)"; exit 1; }
  tris=$(grep -E '^LOD' "work/logs/$id.log" | awk '{print $4}' | tr '\n' ' ')
  "$blender" --background --python scripts/review.py -- "$id" > "work/logs/${id}_review.log" 2>&1
  echo "== $id LOD triangles: $tris"
  python3 scripts/sheet.py "$id" $tris | grep -vE '^SHEET'
  python3 scripts/finish.py "$id" "${install[@]}" | grep -E '^(VALID|INVALID|INSTALLED)' | cut -c1-160 || failed+=("$id")
done
python3 scripts/bounds.py "${ids[@]}"
[[ ${#failed[@]} -eq 0 ]] || { echo "invalid (not installed): ${failed[*]}"; exit 1; }
