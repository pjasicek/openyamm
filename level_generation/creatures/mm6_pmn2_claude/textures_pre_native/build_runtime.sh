#!/usr/bin/env bash
# Rebuild the runtime GLB from the authoring master: textures -> export -> prepare -> LODs -> shadow fix -> colour
# variants -> install. Run scripts/bake_ao.py first when the mesh changes.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
blender=/snap/bin/blender
python3 "$here/scripts/prepare_textures.py"
# Shared-skin tiers, 1K body base colour and the head texture set (inputs of the export below).
python3 "$here/scripts/tier_ramps.py" > /dev/null
python3 "$here/../claude_shared/compose_head_set.py" "$here" pmn2 work/rig_v8.blend Mage "$here/textures/pmn2_a_basecolor.png" \
  --local 0 --contrast 1.0 --saturation 1.0 --fine 1.0  # the body is not graded either
"$blender" --background --python "$here/scripts/export_runtime.py" 2>&1 | grep -E "MAPS|PACKED|JOINED|EXPORTED|Error|Traceback"
python3 "$repo/tools/prepare_actor_glb.py" "$here/export/mm6_pmn2_lod0.glb" "$here/export/mm6_pmn2_runtime_lod0.glb"
"$blender" --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_pmn2_runtime_lod0.glb" \
  "$here/export/mm6_pmn2_lods.glb" --mesh-node Mage 2>&1 | grep "LOD triangles"
python3 "$here/scripts/shrink_shadow_lods.py" "$here/export/mm6_pmn2_lods.glb" "$here/export/mm6_pmn2_lods_shadowfix.glb"
# Tiers: one shared skin + region mask + ramps (robe mask and tints from prepare_textures.py; tier_ramps.py above).
python3 "$here/../claude_shared/region_variants.py" "$here/export/mm6_pmn2_lods_shadowfix.glb" \
  "$here/export/mm6_pmn2.glb" "$here/textures/pmn2_ramps.json" --extra Mage openyamm_specular=0 --extra Mage pbr.metallicFactor=0
rm -f "$here/export/mm6_pmn2_lods.geometry.glb"
if [[ "${1:-}" == "--install" ]]; then
  install -m 0664 "$here/export/mm6_pmn2.glb" "$repo/assets_dev/worlds/mm6/models/mm6_pmn2.glb"
  echo "installed $repo/assets_dev/worlds/mm6/models/mm6_pmn2.glb"
fi
