#!/usr/bin/env bash
# Skeleton tuning loop: skel.sh <id> <sprite stems...> -> work/<id>/skeleton.png
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$here"; id="$1"; shift
/snap/bin/blender --background --python skeleton_preview.py -- "$id" 2>&1 | grep -E "SKELETON|Error|Traceback" || true
python3 skeleton_sheet.py "$id" "$@"
