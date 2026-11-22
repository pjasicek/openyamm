#!/usr/bin/env bash
# Build pieces: high (statues: build_high.py; props: build_props.py) -> LOD0 + UVs + bakes -> maps -> LODs + export
# -> linked GLB in export/ -> winding check. Blender goes through lane S's serialising wrapper.
# Usage: build.sh <id> [<id> ...]   (statues: fire air earth water; props: see scripts/props.json)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender="$here/../../creatures/xeen_tiers_claude/bin/blender"
cd "$here"
for id in "$@"; do
    if python3 -c "import json,sys; sys.exit(0 if '$id' in json.load(open('scripts/statues.json')) else 1)"; then
        conf=statues.json; stage1=scripts/build_high.py
    else
        conf=props.json; stage1=scripts/build_props.py
    fi
    name=$(python3 -c "import json; print(json.load(open('scripts/$conf'))['$id']['name'])")
    mkdir -p "work/$id"
    "$blender" --background --factory-startup --python "$stage1" -- "$id" > "work/$id/high.log" 2>&1
    grep -E "FIGURE scale|^LOW |BOUNDS|STREAM|SEAT|Traceback|Error" "work/$id/high.log" || true
    "$blender" --background --factory-startup --python scripts/lowbake.py -- "$conf" "$id" > "work/$id/lowbake.log" 2>&1
    grep -E "LOD0|FALLBACK|SPARROW best|^UV charts|LOWBAKE_DONE|Traceback|Error" "work/$id/lowbake.log" || true
    python3 scripts/finish_maps.py "$id"
    "$blender" --background --factory-startup --python scripts/export_model.py -- "$conf" "$id" 2>&1 \
        | grep -E "LOD_TRI|EXPORTED|Error|Traceback"
    if [[ $(python3 -c "import json; print(len(json.load(open('scripts/$conf'))['$id'].get('lod_ratios', [1])))") == 0 ]]; then
        cp "work/$id/${name}_raw.glb" "export/$name.glb"
    else
        python3 ../../../tools/link_static_model_lods.py "work/$id/${name}_raw.glb" "export/$name.glb"
    fi
    python3 ../mm8_3d/animated/scripts/check_winding.py "export/$name.glb" | tail -1
done
