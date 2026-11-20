#!/usr/bin/env bash
# Runtime GLBs from the gated master (scripts/rebuild.sh, export_uploads, transfer_uv): textures -> export -> prepare
# -> LODs -> shadow fix -> colour variants -> sword split into an attachment -> head merged into the body -> [install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
blender=/snap/bin/blender
cd "$here"
"$blender" --background --python scripts/uv_raster.py -- work/rig_v6.blend UVMap 1024 2>&1 | grep RASTER
"$blender" --background --python scripts/uv_raster.py -- work/rig_v6.blend HeadUV 1024 2>&1 | grep RASTER
python3 scripts/compose_bar1.py | grep -E "CLASSES|HEAD gain"
"$blender" --background --python-exit-code 1 --python scripts/clip_timing.py 2>&1 | grep -E "^(ATTACK|BLENDS|LEGS|FEET|STEP)|Error|Traceback"
"$blender" --background --python-exit-code 1 --python scripts/export_runtime.py 2>&1 | grep -E "SWORD|EXPORTED|Error|Traceback" | cut -c1-200
python3 "$repo/tools/prepare_actor_glb.py" export/mm6_bar1_lod0.glb export/mm6_bar1_runtime_lod0.glb
"$blender" --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_bar1_runtime_lod0.glb" \
  "$here/export/mm6_bar1_lods.glb" --mesh-node Barbarian 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm6_bar1_lods.glb export/mm6_bar1_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm6_bar1_lods_shadowfix.glb export/mm6_bar1.glb textures/bar1_ramps.json \
  --extra Barbarian openyamm_specular=1 --extra Barbarian openyamm_specular_mask=true \
  --extra Barbarian pbr.metallicFactor=0
python3 "$repo/tools/split_attachment.py" export/mm6_bar1.glb --joint Sword --body export/mm6_bar1.glb \
  --attachment export/mm6_bar1_sword.glb
python3 "$repo/tools/merge_head_material.py" export/mm6_bar1.glb export/mm6_bar1.glb
rm -f export/mm6_bar1_lods.geometry.glb
if [[ "${1:-}" == "--install" ]]; then
  for name in mm6_bar1 mm6_bar1_sword; do
    install -m 0664 "export/$name.glb" "$repo/assets_dev/worlds/mm6/models/$name.glb"
    echo "installed $repo/assets_dev/worlds/mm6/models/$name.glb"
  done
fi
