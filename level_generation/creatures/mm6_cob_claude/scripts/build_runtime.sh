#!/usr/bin/env bash
# Cobra runtime GLB: export -> prepare -> LODs -> shadow fix -> region tiers (mask + ramps) -> (install).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
blender=/snap/bin/blender
"$blender" --background "$here/work/anim_v1.blend" --python "$here/scripts/export_glb.py" 2>&1 | grep -E "EXPORTED|Error"
python3 "$repo/tools/prepare_actor_glb.py" "$here/export/mm6_cob_lod0.glb" "$here/export/mm6_cob_runtime_lod0.glb"
"$blender" --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_cob_runtime_lod0.glb" \
  "$here/export/mm6_cob_lods.glb" --mesh-node Cobra 2>&1 | grep "LOD triangles"
python3 "$here/scripts/shrink_shadow_lods.py" "$here/export/mm6_cob_lods.glb" "$here/export/mm6_cob_lods_shadowfix.glb"
python3 "$here/../claude_shared/region_variants.py" "$here/export/mm6_cob_lods_shadowfix.glb" \
  "$here/export/mm6_cob.glb" "$here/textures/cob_ramps.json" \
  --extra Cobra openyamm_specular=0 --extra Cobra pbr.metallicFactor=0
rm -f "$here/export/mm6_cob_lods.geometry.glb"
if [[ "${1:-}" == "--install" ]]; then
  install -m 0664 "$here/export/mm6_cob.glb" "$repo/assets_dev/worlds/mm6/models/mm6_cob.glb"
  echo "installed $repo/assets_dev/worlds/mm6/models/mm6_cob.glb"
fi
