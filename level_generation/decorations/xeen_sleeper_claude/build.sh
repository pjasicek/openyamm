#!/usr/bin/env bash
# Build the four sleepers: body (pose, LODs, laid) -> body textures (skin ramps, closed eyes) -> couch textures ->
# per element couch + export -> linked GLB in export/ -> winding. Blender goes through lane S's serialising wrapper.
# Usage: build.sh [fire] [air] [earth] [water] [--review]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender="$here/../../creatures/xeen_tiers_claude/bin/blender"
cd "$here"
els=(); review=0
for a in "$@"; do [[ $a == --review ]] && review=1 || els+=("$a"); done
[[ ${#els[@]} -gt 0 ]] || els=(earth fire air water)
python3 scripts/expose_lods.py ../../../assets_source/worlds/mm6/models/mm6_ttn.glb work/ttn_lods.glb
"$blender" --background --factory-startup --python scripts/build_body.py 2>&1 | grep -E "BODY LOD|BODY bounds|Traceback|Error" || true
python3 scripts/body_textures.py | grep -E "^SET . T"
python3 scripts/couch_textures.py | grep -E "TRIM|GLOW"
for el in "${els[@]}"; do
    name=xeen_deco_sleeper_$el
    "$blender" --background --factory-startup --python scripts/build_export.py -- "$el" 2>&1 | grep -E "LOD_TRI|BOUNDS|Error|Traceback"
    python3 ../../../tools/link_static_model_lods.py "work/${name}_raw.glb" "export/$name.glb"
    python3 ../mm8_3d/animated/scripts/check_winding.py "export/$name.glb" | tail -1
done
if [[ $review == 1 ]]; then
    files=(); for el in "${els[@]}"; do files+=("export/xeen_deco_sleeper_$el.glb"); done
    "$blender" --background --factory-startup --python scripts/review_render.py -- review/final "${files[@]}" 2>&1 | grep -E "DONE|Error|Traceback"
    for el in "${els[@]}"; do python3 scripts/sheet.py "review/final/${el}_sheet.png" 3 review/final/${el}_{front,q,head,back,face,far}.png; done
fi
