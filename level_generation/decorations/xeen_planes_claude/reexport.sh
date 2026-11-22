#!/usr/bin/env bash
# Re-export pieces after a colour change: recolour bake on the saved LOD0 -> maps -> LODs + export -> link -> winding.
# Usage: reexport.sh <id> [<id> ...]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender="$here/../../creatures/xeen_tiers_claude/bin/blender"
cd "$here"
for id in "$@"; do
    conf=$(python3 -c "import json; print('statues.json' if '$id' in json.load(open('scripts/statues.json')) else 'props.json')")
    name=$(python3 -c "import json; print(json.load(open('scripts/$conf'))['$id']['name'])")
    "$blender" --background --factory-startup --python scripts/lowbake.py -- "$conf" "$id" recolour 2>&1 \
        | grep -E "LOWBAKE_DONE|Traceback|Error" || true
    python3 scripts/finish_maps.py "$id" | grep -E "COLOUR|MR|NORMAL"
    "$blender" --background --factory-startup --python scripts/export_model.py -- "$conf" "$id" 2>&1 \
        | grep -E "LOD_TRI|Error|Traceback"
    if [[ $(python3 -c "import json; print(len(json.load(open('scripts/$conf'))['$id'].get('lod_ratios', [1])))") == 0 ]]; then
        cp "work/$id/${name}_raw.glb" "export/$name.glb"
    else
        python3 ../../../tools/link_static_model_lods.py "work/$id/${name}_raw.glb" "export/$name.glb" > /dev/null
    fi
    python3 ../mm8_3d/animated/scripts/check_winding.py "export/$name.glb" | tail -1
done
