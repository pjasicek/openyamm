#!/usr/bin/env bash
# Retextured reduced thief: UVs -> compose -> export -> prepare -> LODs -> shadow LODs tucked in -> region variants
# (body, cloak and head share the cloth ramps) -> collapsed-mesh check -> export/mm6_thf_tex.glb. Install separately.
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"; ROOT="$(cd "$P/../../.." && pwd)"; E="$P/export"
cd "$ROOT"
t(){ local log="$P/work/log_tex_$1.txt"; shift; "$@" > "$log" 2>&1 || { echo "FAILED $*"; tail -20 "$log"; exit 1; }; }
t uv blender -b --python-exit-code 1 -P "$P/scripts/dump_tex_uv.py"
t srcuv blender -b --python-exit-code 1 -P "$P/scripts/dump_source_uv.py"
# t bake blender -b --python-exit-code 1 -P "$P/scripts/bake_body.py"   (BODY_UVS = baked only)
t compose python3 "$P/scripts/compose_tex.py"
t export blender -b --python-exit-code 1 -P "$P/scripts/export_tex.py"
t prepare python3 tools/prepare_actor_glb.py "$E/mm6_thf_tex_lod0.glb" "$E/mm6_thf_tex_runtime_lod0.glb"
t lods blender -b --python-exit-code 1 -P tools/build_actor_lods.py -- "$E/mm6_thf_tex_runtime_lod0.glb" "$E/mm6_thf_tex_lods.glb" --mesh-node Thief
t shadow python3 "$P/../mm6_thf_claude/scripts/shrink_shadow_lods.py" "$E/mm6_thf_tex_lods.glb" "$E/mm6_thf_tex_shadow.glb"
t regions python3 "$P/../claude_shared/region_variants.py" "$E/mm6_thf_tex_shadow.glb" "$E/mm6_thf_tex_regions.glb" "$P/textures/thf_ramps.json" \
  --extra Thief openyamm_specular=0 --extra Thief pbr.metallicFactor=0 \
  --extra ThiefCloak openyamm_specular=0 --extra ThiefCloak pbr.metallicFactor=0 \
  --extra ThiefHead openyamm_specular=0 --extra ThiefHead pbr.metallicFactor=0
t keys python3 tools/model_hide_collapsed_meshes.py "$E/mm6_thf_tex_regions.glb" --write "$E/mm6_thf_tex.glb"
grep -E "COMPOSED" "$P/work/log_tex_compose.txt"
grep -E "DAGGER|EXPORTED" "$P/work/log_tex_export.txt" | cut -c1-200
grep "LOD tri" "$P/work/log_tex_lods.txt"
