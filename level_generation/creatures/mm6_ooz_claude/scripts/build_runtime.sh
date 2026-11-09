#!/usr/bin/env bash
# Ooze runtime GLB: compose -> export -> prepare -> LODs -> shadow fix -> A/B/C skins -> (install).
# Inputs: work/anim_v1.blend (rig_ooz.py -> uv_export.py -> anim_ooz.py), work/ao_body.png
# (blob_only.py + claude_shared/bake_creature_ao.py), meshy/retexture_v1.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
blender=/snap/bin/blender
cd "$here"
python3 scripts/compose_ooz.py | grep -E "SHADED|RAMPS|COMPOSED"
"$blender" --background --python scripts/export_glb.py 2>&1 | grep -E "POD|EXPORTED|Error|Traceback"
python3 "$repo/tools/prepare_actor_glb.py" export/mm6_ooz_lod0.glb export/mm6_ooz_runtime_lod0.glb
"$blender" --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_ooz_runtime_lod0.glb" \
  "$here/export/mm6_ooz_lods.glb" --mesh-node Ooze 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm6_ooz_lods.glb export/mm6_ooz_lods_shadowfix.glb
# Wet slime: the one creature that keeps engine specular, reduced to 0.7 (user: less glossy); metallic stays 0.
python3 ../claude_shared/region_variants.py export/mm6_ooz_lods_shadowfix.glb export/mm6_ooz.glb textures/ooz_ramps.json \
  --extra Ooze pbr.metallicFactor=0 --extra Ooze openyamm_specular=0.7 \
  --extra Ooze openyamm_specular_mask=true
rm -f export/mm6_ooz_lods.geometry.glb
if [[ "${1:-}" == "--install" ]]; then
  install -m 0664 export/mm6_ooz.glb "$repo/assets_dev/worlds/mm6/models/mm6_ooz.glb"
  echo "installed $repo/assets_dev/worlds/mm6/models/mm6_ooz.glb"
fi
