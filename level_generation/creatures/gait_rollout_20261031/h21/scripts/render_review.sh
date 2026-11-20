#!/usr/bin/env bash
# Filmstrips of clips of a candidate export with its held prop baked in flat grey (review only).
#   scripts/render_review.sh <export.glb> <out prefix> <clip,clip> [node=prop.glb[:r,g,b] ...] [-- render_clip.py options]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
glb="$1"; prefix="$2"; clips="$3"; shift 3
props=(); while [[ $# -gt 0 && $1 != -- ]]; do props+=("$1"); shift; done; [[ ${1:-} == -- ]] && shift
review="$here/work/$(basename "${glb%.glb}")_review.glb"
python3 "$here/scripts/review_glb.py" "$glb" "$review" "${props[@]}" > /dev/null
/snap/bin/blender --background --factory-startup --python "$here/scripts/render_clip.py" -- "$review" "$prefix" \
    "$clips" "$@" 2>&1 | grep -e RENDER -e Error || true
python3 "$here/scripts/sheet.py" "$prefix" ${clips//,/ }
