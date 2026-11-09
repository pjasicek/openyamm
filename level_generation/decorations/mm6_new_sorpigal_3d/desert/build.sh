#!/usr/bin/env bash
# Rebuild one desert plant (or all): textures -> Blender plant (LOD0-2) -> impostor bake -> export (+ LOD3 quad) ->
# material modes, LOD link, card cut, validation [--install] -> review renders and sheets.
# Usage: build.sh <id|all> [--install]     ids: 6tree21 cac19 cac18 cac24 cac17 cac23 cac3
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender=/snap/bin/blender
id="$1"; shift
cd "$here"
if [ "$id" = all ]; then
    python3 scripts/make_textures.py
    for x in 6tree21 cac19 cac18 cac24 cac17 cac23 cac3; do "$0" "$x" --no-textures "$@"; done
    exit 0
fi
if [[ " $* " != *" --no-textures "* ]]; then python3 scripts/make_textures.py; fi
install_flag=""; [[ " $* " == *" --install "* ]] && install_flag="--install"
"$blender" --background --python scripts/build_plant.py -- "$id" 2>&1 | grep -E '^LOD|Error|Traceback' || true
"$blender" --background --python scripts/bake_impostor.py -- "$id" 2>&1 | grep -E 'Error|Traceback' || true
python3 scripts/finish_impostor.py "$id"
"$blender" --background --python scripts/export_plant.py -- "$id" 2>&1 | grep -E 'EXPORTED|Error|Traceback' || true
python3 scripts/post_process.py "$id" $install_flag | grep -E 'VALID|INSTALLED|LINKED'
w="work/$id"
"$blender" --background --python scripts/render_review.py -- "$w/export.blend" "$w/rv" 512 front,three_quarter,back Plant \
    2>&1 | grep -E 'Error|Traceback' || true
"$blender" --background --python scripts/render_review.py -- "$w/export.blend" "$w/lc" 400 front all noshadow \
    2>&1 | grep -E 'Error|Traceback' || true
python3 scripts/sheet.py "$id" $(cat "$w/tris.txt")
# impostor tone against LOD0; re-finish once when it moved
if python3 scripts/calibrate_impostor.py "$id" | tee /dev/stderr | grep -q CHANGED; then
    python3 scripts/finish_impostor.py "$id"
    "$blender" --background --python scripts/export_plant.py -- "$id" 2>&1 | grep -E 'Error|Traceback' || true
    python3 scripts/post_process.py "$id" $install_flag | grep -E 'VALID mm6|INSTALLED'
    "$blender" --background --python scripts/render_review.py -- "$w/export.blend" "$w/lc" 400 front all noshadow \
        2>&1 | grep -E 'Error|Traceback' || true
    python3 scripts/sheet.py "$id" $(cat "$w/tris.txt")
fi
