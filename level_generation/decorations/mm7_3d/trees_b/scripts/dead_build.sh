#!/usr/bin/env bash
# Build one MM7 bare tree (dead_common.SPECIES): traced sprite skeleton, textures + profile -> procedural wood and twig cards (LOD0-2, or LOD0-3
# for the stump) -> impostor (trees) -> export -> materials, LOD link, validation, card cut [--install] -> review.
# Usage: dead_build.sh <id> [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender=/snap/bin/blender
id="$1"; shift
cd "$here"
python3 trace_skeleton.py "$id"
python3 dead_prepare.py "$id" | grep -E "PROFILE|TEXTURE|NATIVE"
"$blender" --background --python dead_build.py -- "$id" 2>&1 | grep -E "SKELETON|^LOD|SAVED|Error|Traceback|budget"
if [[ "$(python3 -c "import dead_common as d; print(d.SPECIES['$id']['kind'])")" != stump ]]; then
  "$blender" --background --python dead_impostor.py -- "$id" 2>&1 | grep -E "IMPOSTOR size|Error|Traceback"
  python3 dead_finish_impostor.py "$id"
fi
"$blender" --background --python dead_export.py -- "$id" 2>&1 | grep -E "EXPORTED|Error|Traceback"
python3 dead_post.py "$id" "$@" | tee "../work/dead_$id/validation.txt"
python3 dead_review.py "$id"
