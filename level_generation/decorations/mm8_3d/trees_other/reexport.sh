#!/usr/bin/env bash
# Re-export an already built species against the current shared atlases (shared/*.png, which the tree.blend
# references by path) and install it: the GLB then embeds the same atlas bytes as every other species, so the cooker
# stores them once. Geometry, COLOR_0, clump atlas and impostor are unchanged (no renders).
# Usage: reexport.sh <id> [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
id="$1"; shift
cd "$here/scripts"
/snap/bin/blender --background --python export_tree.py -- "$id" 2>&1 | grep -E "EXPORTED|Error|Traceback"
python3 post_process.py "$id" "$@" | grep -E "VALID LOD|INSTALLED|Error|Traceback"
