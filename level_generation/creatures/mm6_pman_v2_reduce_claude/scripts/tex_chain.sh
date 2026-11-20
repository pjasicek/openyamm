#!/usr/bin/env bash
# After both Meshy downloads: UV parity, rasters, AO, compose, export, swap into the accepted pre-runtime GLB, images,
# runtime chain (prepare -> LODs -> shadow LODs -> region variants -> head merge -> KHR_materials_specular stripped).
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"; ROOT="$(cd "$P/../../.." && pwd)"; A="$P/../mm6_pman_claude_20261013"; E="$P/export"; cd "$ROOT"
# FROM=<step> resumes at that step (e.g. FROM=compose after a compose-only change)
started=$([ -z "${FROM:-}" ] && echo 1 || echo 0)
t(){ [ "$1" = "${FROM:-}" ] && started=1; [ "$started" = 1 ] || return 0; local s=$(date +%s); local log="$P/work/log_$1.txt"; shift; "$@" > "$log" 2>&1 || { echo "FAILED $*"; tail -20 "$log"; exit 1; }; echo "$(basename "$log" .txt) $(( $(date +%s) - s ))s"; }
t verify blender -b --python-exit-code 1 -P "$P/scripts/tex_verify_uv.py"
t relayout blender -b --python-exit-code 1 -P "$P/scripts/tex_relayout.py"
t raster blender -b --python-exit-code 1 -P "$P/scripts/tex_raster.py"
t resample blender -b --python-exit-code 1 -P "$P/scripts/tex_resample.py"
t sample python3 "$P/scripts/tex_sample.py"
t hairmask blender -b --python-exit-code 1 -P "$P/scripts/tex_hairmask.py"
t ao blender -b --python-exit-code 1 -P "$P/scripts/tex_bake_ao.py"
t compose python3 "$P/scripts/tex_compose.py"
t export blender -b --python-exit-code 1 -P "$P/scripts/tex_export.py"
t swap python3 "$P/scripts/swap_lod0.py" "$A/export/mm6_pman_v2_lod0.glb" "$P/work/cand_export.glb" "$E/mm6_pman_v2_lod0.glb" Peasant
t images python3 "$P/scripts/tex_images.py" "$E/mm6_pman_v2_lod0.glb"
t prepare python3 tools/prepare_actor_glb.py "$E/mm6_pman_v2_lod0.glb" "$E/mm6_pman_v2_runtime_lod0.glb"
t lods blender -b --python-exit-code 1 -P tools/build_actor_lods.py -- "$E/mm6_pman_v2_runtime_lod0.glb" "$E/mm6_pman_v2_lods.glb" --mesh-node Peasant
t shadow python3 "$A/scripts/shrink_shadow_lods.py" "$E/mm6_pman_v2_lods.glb" "$E/mm6_pman_v2_lods_shadow.glb"
t regions python3 "$P/../claude_shared/region_variants.py" "$E/mm6_pman_v2_lods_shadow.glb" "$E/mm6_pman_v2_regions.glb" "$P/textures/pman_ramps.json" --extra Peasant openyamm_specular=1 --extra Peasant openyamm_specular_mask=true --extra Peasant pbr.metallicFactor=1
t merge python3 tools/merge_head_material.py "$E/mm6_pman_v2_regions.glb" "$E/mm6_pman_v2.glb"
t strip python3 "$P/scripts/strip_specular.py" "$E/mm6_pman_v2_runtime_lod0.glb" "$E/mm6_pman_v2.glb"
grep "LOD tri" "$P/work/log_lods.txt"
