#!/usr/bin/env bash
# Rebuild the runtime GLB from the authoring master: textures -> head set -> export -> prepare -> LODs -> shadow fix
# -> colour variants -> head merged into the body material -> install. Inputs: work/rig_v3.blend (build_clips_thf.py,
# then claude_shared/head_texture_split.py), work/ao_body.png (claude_shared/bake_creature_ao.py on rig_v2),
# meshy/retexture_v1 and meshy/head_retexture_v1.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
blender=/snap/bin/blender
cd "$here"
python3 scripts/native_pixels.py | head -1
"$blender" --background work/rig_v2.blend --python scripts/dump_uv3d.py | grep DUMPED
python3 scripts/prepare_textures.py | grep MAPS
python3 ../claude_shared/compose_head_set.py "$here" thf work/rig_v3.blend Thief "$here/textures/thf_a_basecolor.png" --seam-gain 1.0 \
  --local 0.4 --contrast 1.05 | tail -1
"$blender" --background work/rig_v3.blend --python scripts/dump_head_uv.py | grep HEADUV
python3 scripts/head_tiers.py
"$blender" --background --python scripts/export_runtime.py 2>&1 | grep -E "DAGGER|JOINED|EXPORTED|Error|Traceback" | cut -c1-300
python3 "$repo/tools/prepare_actor_glb.py" export/mm6_thf_lod0.glb export/mm6_thf_runtime_lod0.glb
"$blender" --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_thf_runtime_lod0.glb" \
  "$here/export/mm6_thf_lods.glb" --mesh-node Thief 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm6_thf_lods.glb export/mm6_thf_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm6_thf_lods_shadowfix.glb export/mm6_thf.glb textures/thf_ramps.json \
  --extra Thief openyamm_specular=0 --extra Thief pbr.metallicFactor=0 \
  --extra ThiefHead openyamm_specular=0 --extra ThiefHead pbr.metallicFactor=0
# one draw per thief: head primitive merged into the body (body | gutter | head atlas), one material per tier
python3 "$repo/tools/merge_head_material.py" export/mm6_thf.glb export/mm6_thf.glb
rm -f export/mm6_thf_lods.geometry.glb
if [[ "${1:-}" == "--install" ]]; then
  install -m 0664 export/mm6_thf.glb "$repo/assets_dev/worlds/mm6/models/mm6_thf.glb"
  echo "installed $repo/assets_dev/worlds/mm6/models/mm6_thf.glb"
fi
python3 scripts/viewer_tiers.py
python3 scripts/update_viewer_manifest.py
