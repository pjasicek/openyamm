#!/usr/bin/env bash
# Rebuild one flower: atlas -> Blender plant (3 LODs) -> link + cut + validate [--install] -> review renders/sheets.
# Usage: build.sh 6flower02|6flower07 [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender=/snap/bin/blender
id="$1"; shift
cd "$here"
python3 scripts/make_atlas.py "$id"
tris=$("$blender" --background --python scripts/build_plant.py -- "$id" 2>&1 | grep -E '^LOD' | awk '{print $4}' | tr '\n' ' ')
echo "LOD triangles before cutting: $tris"
python3 scripts/post_process.py "$id" "$@"
"$blender" --background --python scripts/render_review.py -- "$id" 2>&1 | grep -c RENDERED >/dev/null
python3 scripts/sheet.py "$id" $tris
