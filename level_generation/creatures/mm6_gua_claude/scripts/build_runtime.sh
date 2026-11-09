#!/usr/bin/env bash
# Rebuild the runtime GLB from the authoring master: textures -> head set -> export -> prepare -> LODs -> shadow fix
# -> colour variants -> install. Inputs: work/rig_v7.blend (scripts/rebuild_anim.sh), work/ao_body.png
# (claude_shared/bake_creature_ao.py on rig_v6), meshy/retexture_v1 and meshy/head_retexture_v1.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
blender=/snap/bin/blender
cd "$here"
python3 scripts/prepare_textures.py | grep MAPS
python3 ../claude_shared/compose_head_set.py "$here" gua work/rig_v7.blend Guard "$here/textures/gua_a_basecolor.png" \
  --local 0.4 --contrast 1.06 --saturation 1.12 | tail -1
"$blender" --background work/rig_v7.blend --python scripts/dump_head_uv.py | grep HEADUV
python3 scripts/head_tiers.py
"$blender" --background --python scripts/export_runtime.py 2>&1 | grep -E "JOINED|EXPORTED|Error|Traceback"
python3 "$repo/tools/prepare_actor_glb.py" export/mm6_gua_lod0.glb export/mm6_gua_runtime_lod0.glb
"$blender" --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_gua_runtime_lod0.glb" \
  "$here/export/mm6_gua_lods.glb" --mesh-node Guard 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm6_gua_lods.glb export/mm6_gua_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm6_gua_lods_shadowfix.glb export/mm6_gua.glb textures/gua_ramps.json \
  --extra Guard openyamm_specular=0 --extra Guard pbr.metallicFactor=0 \
  --extra GuardHead openyamm_specular=0 --extra GuardHead pbr.metallicFactor=0
# the halberd becomes a static attachment on the Halberd joint (tier variants can carry different weapons)
python3 "$repo/tools/split_attachment.py" export/mm6_gua.glb --joint Halberd --body export/mm6_gua.glb \
  --attachment export/mm6_gua_halberd.glb
# one draw per guard: head primitive merged into the body (body | gutter | head atlas), one material per tier
python3 "$repo/tools/merge_head_material.py" export/mm6_gua.glb export/mm6_gua.glb
rm -f export/mm6_gua_lods.geometry.glb
if [[ "${1:-}" == "--install" ]]; then
  install -m 0664 export/mm6_gua.glb "$repo/assets_dev/worlds/mm6/models/mm6_gua.glb"
  install -m 0664 export/mm6_gua_halberd.glb "$repo/assets_dev/worlds/mm6/models/mm6_gua_halberd.glb"
  echo "installed $repo/assets_dev/worlds/mm6/models/mm6_gua.glb"
fi
