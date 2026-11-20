#!/usr/bin/env bash
# Eye runtime GLB: export -> prepare -> LODs -> shadow fix -> A/B/C skins -> (install).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
blender=/snap/bin/blender
"$blender" --background "$here/work/anim_v1.blend" --python "$here/scripts/export_glb.py" 2>&1 | grep EXPORTED
python3 "$repo/tools/prepare_actor_glb.py" "$here/export/mm6_bh_lod0.glb" "$here/export/mm6_bh_runtime_lod0.glb"
"$blender" --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_bh_runtime_lod0.glb" \
  "$here/export/mm6_bh_lods.glb" --mesh-node Eye 2>&1 | grep "LOD triangles"
python3 "$here/scripts/shrink_shadow_lods.py" "$here/export/mm6_bh_lods.glb" "$here/export/mm6_bh_lods_shadowfix.glb"
# Tiers: one shared skin + region mask (compose_bh.py) + ramps from the native palette sprites.
python3 "$here/scripts/tier_ramps.py" > /dev/null
python3 "$here/../claude_shared/region_variants.py" "$here/export/mm6_bh_lods_shadowfix.glb" \
  "$here/export/mm6_bh.glb" "$here/textures/bh_ramps.json" --extra Eye openyamm_specular=0 --extra Eye pbr.metallicFactor=0
rm -f "$here/export/mm6_bh_lods.geometry.glb"
if [[ "${1:-}" == "--install" ]]; then
  install -m 0664 "$here/export/mm6_bh.glb" "$repo/assets_dev/worlds/mm6/models/mm6_bh.glb"
  echo "installed $repo/assets_dev/worlds/mm6/models/mm6_bh.glb"
fi
