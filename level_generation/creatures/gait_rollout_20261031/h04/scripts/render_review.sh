#!/usr/bin/env bash
# (h04) Filmstrips of clips of a GLB with its staff baked in flat grey when the model has one (review only).
#   scripts/render_review.sh <m> <glb> <out prefix> <clip,clip> [render_clip.py options...]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
m="$1"; glb="$2"; prefix="$3"; clips="$4"; shift 4
staff="$root/assets_source/worlds/mm6/models/mm6_${m}_staff.glb"
review="$here/work/$(basename "${glb%.glb}")_review.glb"
if [[ -f $staff ]]; then
    python3 "$here/scripts/review_glb.py" "$glb" "$review" "Staff=$staff:0.62,0.62,0.68" > /dev/null
else
    cp "$glb" "$review"
fi
/snap/bin/blender --background --factory-startup --python "$here/scripts/render_clip.py" -- "$review" "$prefix" \
    "$clips" "$@" 2>&1 | grep -e Error || true
python3 "$here/scripts/sheet.py" "$prefix" ${clips//,/ }
