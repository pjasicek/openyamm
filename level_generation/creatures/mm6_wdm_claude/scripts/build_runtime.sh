#!/usr/bin/env bash
# Flying demon runtime GLB: export -> prepare -> LODs -> shadow fix -> tinted colour variants -> (install).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
blender=/snap/bin/blender
"$blender" --background "$here/work/anim_v1.blend" --python "$here/scripts/export_glb.py" 2>&1 | grep -E "EXPORTED|Error"
python3 "$repo/tools/prepare_actor_glb.py" "$here/export/mm6_wdm_lod0.glb" "$here/export/mm6_wdm_runtime_lod0.glb"
"$blender" --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_wdm_runtime_lod0.glb" \
  "$here/export/mm6_wdm_lods.glb" --mesh-node Demon 2>&1 | grep "LOD triangles"
python3 "$here/scripts/shrink_shadow_lods.py" "$here/export/mm6_wdm_lods.glb" "$here/export/mm6_wdm_lods_shadowfix.glb"
python3 "$here/scripts/add_variants.py" "$here/export/mm6_wdm_lods_shadowfix.glb" "$here/export/mm6_wdm.glb"
rm -f "$here/export/mm6_wdm_lods.geometry.glb"
if [[ "${1:-}" == "--install" ]]; then
  install -m 0664 "$here/export/mm6_wdm.glb" "$repo/assets_dev/worlds/mm6/models/mm6_wdm.glb"
  echo "installed $repo/assets_dev/worlds/mm6/models/mm6_wdm.glb"
fi
