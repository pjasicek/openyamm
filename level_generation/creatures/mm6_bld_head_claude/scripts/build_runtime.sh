#!/usr/bin/env bash
# Bloodsucker with a head texture set: export -> prepare -> LODs -> shadow LODs tucked in -> A/B/C region variants
# (body and head share ramps) -> head merged into the body material (one draw) -> collapsed-mesh keys -> export/mm6_bld.glb.
# Install separately with tools/install_model.py after review.
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"; ROOT="$(cd "$P/../../.." && pwd)"; E="$P/export"; S="$P/../claude_shared"
cd "$ROOT"
t(){ local log="$P/work/log_$1.txt"; shift; "$@" > "$log" 2>&1 || { echo "FAILED $*"; tail -20 "$log"; exit 1; }; }
t export blender -b --python-exit-code 1 -P "$P/scripts/export_glb.py"
t prepare python3 tools/prepare_actor_glb.py "$E/mm6_bld_lod0.glb" "$E/mm6_bld_runtime_lod0.glb"
t lods blender -b --python-exit-code 1 -P tools/build_actor_lods.py -- "$E/mm6_bld_runtime_lod0.glb" "$E/mm6_bld_lods.glb" --mesh-node Bld
t shadow python3 "$P/../mm6_bld_claude/scripts/shrink_shadow_lods.py" "$E/mm6_bld_lods.glb" "$E/mm6_bld_lods_shadow.glb"
t regions python3 "$S/region_variants.py" "$E/mm6_bld_lods_shadow.glb" "$E/mm6_bld_regions.glb" "$P/textures/bld_ramps.json" \
  --extra Bld openyamm_specular=0 --extra Bld pbr.metallicFactor=0 \
  --extra BldHead openyamm_specular=0 --extra BldHead pbr.metallicFactor=0
t merge python3 tools/merge_head_material.py "$E/mm6_bld_regions.glb" "$E/mm6_bld_merged.glb"
t keys python3 tools/model_hide_collapsed_meshes.py "$E/mm6_bld_merged.glb" --write "$E/mm6_bld.glb"
grep "LOD tri" "$P/work/log_lods.txt"
tail -3 "$P/work/log_keys.txt"
