#!/usr/bin/env bash
# Rebuild the runtime GLB chain from the authoring master: export -> prepare -> LODs -> skins -> install.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
blender=/snap/bin/blender
# Shared-skin tiers, 1K body base colour and the head texture set (inputs of the export below).
python3 "$here/scripts/tier_ramps.py" > /dev/null
python3 "$here/../claude_shared/compose_head_set.py" "$here" pman work/final_v1.blend Peasant "$here/textures/pman_a_basecolor.png" \
  --local 0 --contrast 1.0 --saturation 1.0 --fine 1.0  # the body is not graded either
"$blender" --background "$here/work/final_v1.blend" --python "$here/scripts/export_glb.py" 2>&1 | grep EXPORTED
python3 "$repo/tools/prepare_actor_glb.py" "$here/export/mm6_pman_lod0.glb" "$here/export/mm6_pman_runtime_lod0.glb"
"$blender" --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_pman_runtime_lod0.glb" \
  "$here/export/mm6_pman_lods.glb" --mesh-node Peasant 2>&1 | grep "LOD triangles"
python3 "$here/scripts/shrink_shadow_lods.py" "$here/export/mm6_pman_lods.glb" "$here/export/mm6_pman_lods_shadowfix.glb"
# Tiers: one shared skin + region mask + ramps (rerun scripts/tier_ramps.py after compose).
python3 "$here/../claude_shared/region_variants.py" "$here/export/mm6_pman_lods_shadowfix.glb" \
  "$here/export/mm6_pman.glb" "$here/textures/pman_ramps.json" --extra Peasant openyamm_specular=0 --extra Peasant pbr.metallicFactor=0
# One material per creature: the head texture set joins the body in a body|head atlas (one draw instead of two).
python3 "$repo/tools/merge_head_material.py" "$here/export/mm6_pman.glb" "$here/export/mm6_pman.glb"
rm -f "$here/export/mm6_pman_lods.geometry.glb"
if [[ "${1:-}" == "--install" ]]; then
  install -m 0664 "$here/export/mm6_pman.glb" "$repo/assets_dev/worlds/mm6/models/mm6_pman.glb"
  echo "installed $repo/assets_dev/worlds/mm6/models/mm6_pman.glb"
fi
