#!/usr/bin/env bash
# Rebuild the runtime GLB from the authoring master: textures -> head set -> export -> prepare -> LODs -> shadow fix
# -> colour variants -> head merged into the body material -> install. Inputs: work/rig_v3.blend (build_clips_wfigt1.py,
# then claude_shared/head_texture_split.py), work/ao_body.png (claude_shared/bake_creature_ao.py on rig_v2),
# work/uv3d.npz (dump_uv3d.py on rig_v2), meshy/retexture_v1 and meshy/head_retexture_v1. Head seam gain 0.8 from
# the fur medians (head 42, darkened body 35): the measured seam (32 edges under the AO-dark throat) asked for 0.30.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
blender=/snap/bin/blender
cd "$here"
python3 scripts/native_pixels.py | head -1
python3 scripts/prepare_textures.py | grep MAPS
python3 ../claude_shared/compose_head_set.py "$here" wwf work/rig_v3.blend Werewolf "$here/textures/wwf_a_basecolor.png" --seam-gain 0.8 \
  --local 0.4 --contrast 1.05 | tail -1
"$blender" --background --python scripts/export_runtime.py 2>&1 | grep -E "JOINED|EXPORTED|Error|Traceback" | cut -c1-300
python3 "$repo/tools/prepare_actor_glb.py" export/mm6_wwf_lod0.glb export/mm6_wwf_runtime_lod0.glb
"$blender" --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_wwf_runtime_lod0.glb" \
  "$here/export/mm6_wwf_lods.glb" --mesh-node Werewolf 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm6_wwf_lods.glb export/mm6_wwf_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm6_wwf_lods_shadowfix.glb export/mm6_wwf.glb textures/wwf_ramps.json \
  --extra Werewolf openyamm_specular=0 --extra Werewolf pbr.metallicFactor=0 \
  --extra WerewolfHead openyamm_specular=0 --extra WerewolfHead pbr.metallicFactor=0
# one draw per werewolf: head primitive merged into the body (body | gutter | head atlas), one material per tier
python3 "$repo/tools/merge_head_material.py" export/mm6_wwf.glb export/mm6_wwf.glb
rm -f export/mm6_wwf_lods.geometry.glb
if [[ "${1:-}" == "--install" ]]; then
  install -m 0664 export/mm6_wwf.glb "$repo/assets_dev/worlds/mm6/models/mm6_wwf.glb"
  echo "installed $repo/assets_dev/worlds/mm6/models/mm6_wwf.glb"
fi
python3 scripts/viewer_tiers.py
python3 scripts/update_viewer_manifest.py
