#!/usr/bin/env bash
# Build the Enchanted Boulder: rock + face relief -> high/low meshes -> LOD0 UVs and bakes -> maps -> LODs, export,
# link, winding check, texture measures. Blender goes through lane S's serialising wrapper (one Blender at a time).
# Usage: build.sh [--from maps] [--review]     (--from maps reuses work/low.blend and the bakes)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender="$here/../../creatures/xeen_tiers_claude/bin/blender"
cd "$here"
from=mesh; review=0
while [[ $# -gt 0 ]]; do
    case $1 in --from) from=$2; shift;; --review) review=1;; esac; shift
done
mkdir -p work export review
if [[ $from == mesh ]]; then
    "$blender" -b --factory-startup --python scripts/build_mesh.py > work/mesh.log 2>&1
    grep -E "ROCK|FACE|RELIEF|HIGH|LOW|BOUNDS|Traceback|Error" work/mesh.log || true
    "$blender" -b --factory-startup --python scripts/lowbake.py > work/lowbake.log 2>&1
    grep -E "^UV charts|BAKED|LOWBAKE_DONE|FALLBACK|Traceback|Error" work/lowbake.log || true
fi
python3 scripts/finish_maps.py
"$blender" -b --factory-startup --python scripts/export_boulder.py 2>&1 | grep -E "LOD_TRI|EXPORTED|Error|Traceback"
python3 ../../../tools/link_static_model_lods.py work/xeen_deco_boulder_raw.glb export/xeen_deco_boulder.glb
python3 ../mm8_3d/animated/scripts/check_winding.py export/xeen_deco_boulder.glb | tail -1
python3 ../../creatures/claude_shared/texture_quality.py export/xeen_deco_boulder.glb --json work/texture_quality.json
if [[ $review == 1 ]]; then
    "$blender" -b --factory-startup --python scripts/review_render.py -- work/xeen_deco_boulder_raw.glb review/renders \
        2>&1 | grep -E "REVIEW_DONE|Error|Traceback"
    python3 scripts/sheet.py review/renders_sheet.jpg 4 640 review/renders/{front_300,front_1000,front_3000,face_close,three_quarter,side,back,lod0,lod1,lod2,lod3}.png
fi
