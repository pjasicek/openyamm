#!/usr/bin/env bash
# Fast colour calibration of one palm: quick build (LOD0-2) + LOD0 front render (qv_Plant_front.png), then the
# contrast and tint calibrations against the sprite, until neither moves (at most 6 passes). Run build.sh after it.
# Usage: scripts/calibrate_loop.sh <id>
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$here"
for pass in 1 2 3 4 5 6; do
    /snap/bin/blender --background --python scripts/build_palm.py -- "$1" 2>&1 | grep -E 'Error|Traceback' || true
    /snap/bin/blender --background --python scripts/render_review.py -- "work/$1/plant.blend" "work/$1/qv" 512 front Plant \
        2>&1 | grep -E 'Error|Traceback' || true
    out=$(RENDER=qv_Plant_front.png python3 scripts/calibrate_contrast.py "$1"; RENDER=qv_Plant_front.png python3 scripts/calibrate_tint.py "$1")
    echo "pass $pass: $(grep -E 'LEAF' <<< "$out" | tr '\n' ' ')"
    grep -q CHANGED <<< "$out" || break
done
RENDER=qv_Plant_front.png python3 scripts/contrast.py "$1"
