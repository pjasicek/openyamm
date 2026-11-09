#!/usr/bin/env bash
# Quick iteration for one species: inputs, leaf atlas, tree, review/<id>/quick.png (no LODs, no install).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$here/scripts"
python3 prepare.py "$1" > /dev/null
python3 make_leaf_atlas.py "$1" | tail -1
/snap/bin/blender --background --python build_tree.py -- "$1" 2>&1 | grep -E "ALONG|SKELETON|BARK|CLUMPS|CARDS|^LOD|Error|Traceback"
python3 quick.py "$1"
