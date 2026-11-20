#!/usr/bin/env bash
# Runtime GLB from the gated master (rebuild.sh -> export_uploads -> transfer_uv [-> head UVs] -> work/rig_v6.blend):
# UV rasters -> textures/tier ramps -> export -> prepare -> LODs -> shadow fix -> colour variants -> head merged into
# the body (when the head set exists) -> [--install: copies mm6_dru1.glb into the MM6 models; actors.yml is separate]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
blender=/snap/bin/blender
cd "$here"
"$blender" --background --python scripts/uv_raster.py -- work/rig_v6.blend UVMap 1024 2>&1 | grep RASTER
if [[ -f meshy/head_retexture_v1/texture_urls_0_base_color.png ]]; then
  "$blender" --background --python scripts/uv_raster.py -- work/rig_v6.blend HeadUV 1024 2>&1 | grep RASTER
fi
python3 scripts/compose_dru1.py | grep -E "CLASSES|GRADE|HEAD|RAMPS"
"$blender" --background --python-exit-code 1 --python scripts/export_runtime.py 2>&1 | grep -E "SOCKETS|EXPORTED|Error|Traceback" | cut -c1-200
python3 "$repo/tools/prepare_actor_glb.py" export/mm6_dru1_lod0.glb export/mm6_dru1_runtime_lod0.glb
"$blender" --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_dru1_runtime_lod0.glb" \
  "$here/export/mm6_dru1_lods.glb" --mesh-node Druidess 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm6_dru1_lods.glb export/mm6_dru1_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm6_dru1_lods_shadowfix.glb export/mm6_dru1.glb textures/dru1_ramps.json \
  --extra Druidess openyamm_specular=1 --extra Druidess openyamm_specular_mask=true \
  --extra Druidess pbr.metallicFactor=0
if [[ -f textures/dru1_head_basecolor_1k.png ]]; then
  python3 "$repo/tools/merge_head_material.py" export/mm6_dru1.glb export/mm6_dru1.glb
fi
rm -f export/mm6_dru1_lods.geometry.glb
if [[ "${1:-}" == "--install" ]]; then
  install -m 0664 export/mm6_dru1.glb "$repo/assets_dev/worlds/mm6/models/mm6_dru1.glb"
  echo "installed $repo/assets_dev/worlds/mm6/models/mm6_dru1.glb"
fi
