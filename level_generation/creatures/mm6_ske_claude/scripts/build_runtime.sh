#!/usr/bin/env bash
# Runtime GLBs from the authoring master (run scripts/rebuild.sh first): AO bakes + UV layout -> textures, masks,
# ramps -> export -> prepare -> LODs -> shadow fix -> colour variants -> cutlass split into an attachment -> head
# merged into the body material -> [install] -> viewer.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
blender=/snap/bin/blender
cd "$here"
"$blender" --background --python scripts/bake_ao.py -- work/rig_v1.blend Bone work/ao_body.png 0.03 1024 2>&1 | grep BAKED
"$blender" --background --python scripts/bake_ao.py -- work/rig_v1.blend Head work/ao_head.png 0.02 1024 2>&1 | grep BAKED
python3 scripts/compose_ske.py
"$blender" --background --python scripts/export_runtime.py 2>&1 | grep -E "SWORD|JOINED|SIGNS|EXPORTED|Error|Traceback" | cut -c1-300
python3 "$repo/tools/prepare_actor_glb.py" export/mm6_ske_lod0.glb export/mm6_ske_runtime_lod0.glb
"$blender" --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_ske_runtime_lod0.glb" \
  "$here/export/mm6_ske_lods.glb" --mesh-node Skeleton 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm6_ske_lods.glb export/mm6_ske_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm6_ske_lods_shadowfix.glb export/mm6_ske.glb textures/ske_ramps.json \
  --extra Skeleton openyamm_specular=0 --extra Skeleton pbr.metallicFactor=0
python3 "$repo/tools/split_attachment.py" export/mm6_ske.glb --joint Sword --body export/mm6_ske.glb \
  --attachment export/mm6_ske_sword.glb
python3 "$repo/tools/merge_head_material.py" export/mm6_ske.glb export/mm6_ske.glb
rm -f export/mm6_ske_lods.geometry.glb
if [[ "${1:-}" == "--install" ]]; then
  for name in mm6_ske mm6_ske_sword; do
    install -m 0664 "export/$name.glb" "$repo/assets_dev/worlds/mm6/models/$name.glb"
    echo "installed $repo/assets_dev/worlds/mm6/models/$name.glb"
  done
fi
