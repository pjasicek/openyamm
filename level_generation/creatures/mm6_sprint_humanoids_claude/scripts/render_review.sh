#!/usr/bin/env bash
# Filmstrips of clips of a candidate export with its sword baked in flat grey (review only).
#   scripts/render_review.sh <ogr|kni> <export.glb> <out prefix> <clip,clip> [render_clip.py options...]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../.." && pwd)"
model="$1"; glb="$2"; prefix="$3"; clips="$4"; shift 4
review="$here/work/$(basename "${glb%.glb}")_review.glb"
python3 "$here/scripts/review_glb.py" "$glb" "$review" \
    "Sword=$root/assets_source/worlds/mm6/models/mm6_${model}_sword.glb:0.62,0.62,0.68" > /dev/null
/snap/bin/blender --background --factory-startup --python "$here/scripts/render_clip.py" -- "$review" "$prefix" \
    "$clips" "$@" 2>&1 | grep -e RENDER -e Error || true
python3 "$here/scripts/sheet.py" "$prefix" ${clips//,/ }
