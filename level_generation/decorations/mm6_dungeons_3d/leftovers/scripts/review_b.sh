#!/usr/bin/env bash
# Review renders + sheet for one batch-B corpse: review_b.sh <corpse> <yaw> [elevation]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$here"
/snap/bin/blender --background --python scripts/review.py -- "$1" "work/$1_export.glb" "$2" "${3:-6}" 2>&1 \
  | grep -E 'REVIEW|Error|Traceback' || true
python3 scripts/sheet.py "$1" "$1_p143.png"
