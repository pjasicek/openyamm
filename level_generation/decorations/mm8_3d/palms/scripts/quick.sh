#!/usr/bin/env bash
# Quick colour check without export: build LOD0-2, render LOD0 front (with sun shadows) -> work/<id>/qv_Plant_front.png,
# print the luminance spread against the sprite. Usage: scripts/quick.sh <id> ['{json trial settings}']
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"
/snap/bin/blender --background --python scripts/build_palm.py -- "$1" "${2:-}" 2>&1 | grep -E 'Error|Traceback' || true
/snap/bin/blender --background --python scripts/render_review.py -- "work/$1/plant.blend" "work/$1/qv" 512 front Plant 2>&1 | grep -E 'Error|Traceback' || true
RENDER=qv_Plant_front.png python3 scripts/contrast.py "$1"
