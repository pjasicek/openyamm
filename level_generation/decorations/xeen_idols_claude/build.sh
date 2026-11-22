#!/usr/bin/env bash
# Build the idols: pose + plinth (high) -> LOD0, UVs, bakes -> finished maps -> LODs + export -> linked GLB in export/.
# Blender goes through lane S's serialising wrapper (one Blender at a time). Usage: build.sh [demon] [devil] [--review]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender="$here/../../creatures/xeen_tiers_claude/bin/blender"
cd "$here"
ids=(); review=0
for a in "$@"; do [[ $a == --review ]] && review=1 || ids+=("$a"); done
[[ ${#ids[@]} -gt 0 ]] || ids=(demon devil)
for id in "${ids[@]}"; do
    name=xeen_deco_idol_$id
    "$blender" --background --factory-startup --python scripts/build_high.py -- "$id" > "work/$id/high.log" 2>&1
    grep -E "FIGURE scale|Traceback|Error" "work/$id/high.log" || true
    "$blender" --background --factory-startup --python scripts/lowbake.py -- "$id" > "work/$id/lowbake.log" 2>&1
    grep -E "LOD0|SPARROW best|^UV charts|LOWBAKE_DONE|Traceback|Error" "work/$id/lowbake.log" || true
    python3 scripts/finish_maps.py "$id"
    "$blender" --background --factory-startup --python scripts/export_idol.py -- "$id" 2>&1 | grep -E "LOD_TRI|EXPORTED|Error|Traceback"
    python3 ../../../tools/link_static_model_lods.py "work/$id/${name}_raw.glb" "export/$name.glb"
    python3 ../mm8_3d/animated/scripts/check_winding.py "export/$name.glb" | tail -1
done
if [[ $review == 1 ]]; then
    "$blender" --background --factory-startup --python scripts/review_render.py -- review/final \
        export/xeen_deco_idol_demon.glb export/xeen_deco_idol_devil.glb 2>&1 | grep -E "DONE|Error|Traceback"
    for id in demon devil; do python3 scripts/sheet4.py "review/final/$id" "review/final/${id}_sheet.png" front q side back; done
fi
