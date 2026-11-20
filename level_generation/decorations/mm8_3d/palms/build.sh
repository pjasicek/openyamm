#!/usr/bin/env bash
# Rebuild one MM8 palm (or all): [textures] -> Blender palm (LOD0-2) -> impostor bake -> export (+ LOD3 quad) ->
# material modes, LOD link, card cut, validation [--install] -> review renders and sheets -> impostor tone check.
# Usage: build.sh <id|all> [--install] [--textures]     ids: tree01 ... tree09 (palm_common.ORDER)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender=/snap/bin/blender
id="$1"; shift
cd "$here"
if [[ " $* " == *" --textures "* ]]; then python3 scripts/make_textures.py; fi
if [ "$id" = all ]; then
    for x in $(python3 -c "import sys; sys.path.insert(0, 'scripts'); import palm_common as p; print(*p.ORDER)"); do
        "$0" "$x" $(echo "$@" | sed 's/--textures//'); done
    exit 0
fi
install_flag=""; [[ " $* " == *" --install "* ]] && install_flag="--install"
"$blender" --background --python scripts/build_palm.py -- "$id" 2>&1 | grep -E '^LOD|^SCALE|Error|Traceback' || true
"$blender" --background --python scripts/bake_impostor.py -- "$id" 2>&1 | grep -E 'Error|Traceback' || true
python3 scripts/finish_impostor.py "$id"
w="work/$id"
export_and_review() {
    "$blender" --background --python scripts/export_plant.py -- "$id" 2>&1 | grep -E 'EXPORTED|Error|Traceback' || true
    python3 scripts/post_process.py "$id" | grep -E 'VALID mm8|LINKED'
    "$blender" --background --python scripts/render_review.py -- "$w/export.blend" "$w/rv" 512 front,three_quarter,back Plant \
        2>&1 | grep -E 'Error|Traceback' || true
    "$blender" --background --python scripts/render_review.py -- "$w/export.blend" "$w/lc" 400 front all noshadow \
        2>&1 | grep -E 'Error|Traceback' || true
    python3 scripts/sheet.py "$id" $(cat "$w/tris.txt")
}
export_and_review
# leaf contrast (luminance spread) and tint (mean) against the sprite; rebuild while they move (at most three times)
for pass in 1 2 3; do
out=$(python3 scripts/calibrate_contrast.py "$id"; python3 scripts/calibrate_tint.py "$id"); echo "$out"
if ! grep -q CHANGED <<< "$out"; then break; fi
    "$blender" --background --python scripts/build_palm.py -- "$id" 2>&1 | grep -E '^LOD|^SCALE|Error|Traceback' || true
    "$blender" --background --python scripts/bake_impostor.py -- "$id" 2>&1 | grep -E 'Error|Traceback' || true
    python3 scripts/finish_impostor.py "$id"
    export_and_review
done
# impostor tone against LOD0; re-finish once when it moved
out=$(python3 scripts/calibrate_impostor.py "$id"); echo "$out"
if grep -q CHANGED <<< "$out"; then
    python3 scripts/finish_impostor.py "$id"
    export_and_review
fi
if [ -n "$install_flag" ]; then python3 scripts/post_process.py "$id" --install | grep -E 'VALID mm8|INSTALLED|source:'; fi
