#!/usr/bin/env bash
# Re-run only the impostor finishing (impostor_tone / dilation from species/<id>.json), export, link and review of an
# already built species: the tree, its LODs and the raw impostor renders are reused. Usage: retail.sh <id> [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
id="$1"; shift
cd "$here/scripts"
python3 finish_impostor.py "$id"
python3 shrink_far_maps.py "$id"
/snap/bin/blender --background --python export_tree.py -- "$id" 2>&1 | grep -E "EXPORTED|Error|Traceback"
python3 post_process.py "$id" "$@" | grep -E "VALID LOD|INSTALLED|Error|Traceback"
python3 review.py "$id" > /dev/null
python3 lod_check.py "$id" | grep -E "^Tree"
python3 stack_sheet.py "$id" > /dev/null
