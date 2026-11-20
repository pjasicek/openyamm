#!/usr/bin/env bash
# (h05 copy of h04's) Filmstrips of clips of a GLB with its props baked in flat grey (review only).
#   PROPS=Node=file.glb,... scripts/render_review.sh <glb> <out prefix> <clip,clip> [render_clip.py options...]
# (prop files relative to assets_source/worlds/mm6/models/)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="$(cd -- "$here/../../../.." && pwd)"
glb="$1"; prefix="$2"; clips="$3"; shift 3
review="$here/work/$(basename "${glb%.glb}")_review.glb"
args=()
if [[ -n ${PROPS:-} ]]; then
    IFS=, read -ra pairs <<< "$PROPS"
    for p in "${pairs[@]}"; do args+=("${p%%=*}=$root/assets_source/worlds/mm6/models/${p#*=}:0.62,0.62,0.68"); done
fi
python3 "$here/scripts/review_glb.py" "$glb" "$review" "${args[@]}" > /dev/null
/snap/bin/blender --background --factory-startup --python "$here/scripts/render_clip.py" -- "$review" "$prefix" \
    "$clips" "$@" 2>&1 | grep -e Error || true
python3 "$here/scripts/sheet.py" "$prefix" ${clips//,/ }
