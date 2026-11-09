#!/usr/bin/env bash
# Rebuild the MM7 plants from scratch: procedural textures -> Blender models (3 LODs each, in parallel) -> review
# renders and sheets -> finish (material modes, LOD link, card cutting, validation) [--install: tools/install_model.py
# --engine as mm7_deco_<id>.glb]. Usage: build.sh [--install] [id ...]  (default: all fourteen)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender=/snap/bin/blender
cd "$here"
install=()
ids=()
for arg in "$@"; do
  if [[ "$arg" == --install ]]; then install=(--install); else ids+=("$arg"); fi
done
[[ ${#ids[@]} -gt 0 ]] || ids=(bush03 bush10 bush11 bush13 bush16 bush12 bush02 plant01a plant11a plant02a plant01b plant07b
                               plant03b plant04b)
mkdir -p work/logs review
python3 scripts/make_textures.py
for id in "${ids[@]}"; do
  ( "$blender" --background --python scripts/build_model.py -- "$id" > "work/logs/$id.log" 2>&1
    grep -qE "^EXPORTED" "work/logs/$id.log" || { echo "build failed: $id (work/logs/$id.log)"; exit 1; }
    scripts/review_one.sh "$id" > "work/logs/${id}_sheet.txt" 2>&1 ) &
done
wait
failed=()
for id in "${ids[@]}"; do
  echo "== $id $(grep -E 'sprite mean' "work/logs/${id}_sheet.txt")"
  python3 scripts/finish.py "$id" "${install[@]}" | grep -E '^(VALID|INVALID|INSTALLED)' | cut -c1-160 || failed+=("$id")
done
python3 scripts/overview.py
[[ ${#failed[@]} -eq 0 ]] || { echo "invalid (not installed): ${failed[*]}"; exit 1; }
