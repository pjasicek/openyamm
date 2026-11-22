#!/usr/bin/env bash
# Build the sphinxes: SDF high/low sources -> meshes (+ face graft) -> LOD0, UVs, bakes -> maps -> LODs + export ->
# linked GLB in export/ -> winding check. Blender goes through lane S's serialising wrapper (one Blender at a time).
# Usage: build.sh [north] [south] [--review]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender="$here/../../creatures/xeen_tiers_claude/bin/blender"
cd "$here"
ids=(); review=0
for a in "$@"; do [[ $a == --review ]] && review=1 || ids+=("$a"); done
[[ ${#ids[@]} -gt 0 ]] || ids=(north south)
for id in "${ids[@]}"; do
    name=xeen_deco_sphinx_$id
    mkdir -p "work/$id"
    python3 scripts/sphinx_sdf.py "$id" --cell 6 | grep -E "MESH"
    python3 scripts/sphinx_sdf.py "$id" --cell 14 --flat --preview | grep -E "MESH"
    "$blender" --background --factory-startup --python scripts/build_mesh.py -- "$id" > "work/$id/mesh.log" 2>&1
    grep -E "FACE|triangles|top face|Traceback|Error" "work/$id/mesh.log" || true
    "$blender" --background --factory-startup --python scripts/lowbake.py -- "$id" > "work/$id/lowbake.log" 2>&1
    grep -E "LOD0|REGIONS|PARTUV|UV_ATLAS FALLBACK|UV charts|LOWBAKE_DONE|Traceback|Error" "work/$id/lowbake.log" || true
    python3 scripts/finish_maps.py "$id"
    "$blender" --background --factory-startup --python scripts/export_sphinx.py -- "$id" 2>&1 | grep -E "LOD_TRI|EXPORTED|Error|Traceback"
    python3 ../../../tools/link_static_model_lods.py "work/$id/${name}_raw.glb" "export/$name.glb"
    python3 ../mm8_3d/animated/scripts/check_winding.py "export/$name.glb" | tail -1
    if [[ $review == 1 ]]; then
        "$blender" --background --factory-startup --python scripts/review_render.py -- "$id" "work/$id/${name}_raw.glb" \
            review/final 2>&1 | grep -E "DONE|Error|Traceback"
    fi
done
