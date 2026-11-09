#!/usr/bin/env bash
# m430 runtime GLBs from the gated master (rebuild.sh -> rig_v5; texture chain export_uploads -> Meshy -> transfer_uv
# -> rig_v6): clips synced into rig_v6 -> UV rasters, AO, compose -> export -> prepare -> LODs -> shadow fix -> colour
# variants (one region: robe) -> dagger split into an attachment -> head merged into the body.
# NOT installed (batch D rule): install later with the commands in README.md.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
blender=/snap/bin/blender
cd "$here"
B() { "$blender" --background --factory-startup --threads 4 --python-exit-code 1 --python "$@"; }
B scripts/sync_actions.py -- work/rig_v5.blend work/rig_v6.blend 2>&1 | grep -E "SYNC|Error|Traceback" || true
B scripts/reduce_textured.py -- work/rig_v6.blend work/rig_v6.blend 2>&1 | grep -E "REDUCE2|Error|Traceback" || true
B scripts/rebake_uv.py -- work/rig_v6_full.blend work/rig_v6.blend meshy/retexture_v1 meshy/head_retexture_v1 texturing/rebake_v2 2>&1 | grep -E "REBAKE|Error|Traceback" || true
if [[ "${TEXTURES:-1}" == 1 ]]; then
  B scripts/uv_raster.py -- work/rig_v6.blend UVMap 1024 2>&1 | grep -E "Error|Traceback" || true
  B scripts/uv_raster.py -- work/rig_v6.blend HeadUV 1024 2>&1 | grep -E "Error|Traceback" || true
  B scripts/bake_ao_natm.py -- work/rig_v6.blend 1024 2>&1 | grep -E "^AO|Error|Traceback" || true
  python3 scripts/compose_m430.py | grep -E "NATIVE|CLASSES|MEDIANS|RAMP"
fi
B scripts/export_runtime.py 2>&1 | grep -E "PROP|EXPORTED|Error|Traceback" | cut -c1-200
python3 "$repo/tools/prepare_actor_glb.py" export/mm7_m430_lod0.glb export/mm7_m430_runtime_lod0.glb
"$blender" --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm7_m430_runtime_lod0.glb" \
  "$here/export/mm7_m430_lods.glb" --mesh-node Wight 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm7_m430_lods.glb export/mm7_m430_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm7_m430_lods_shadowfix.glb export/mm7_m430.glb textures/m430_ramps.json \
  --extra Wight openyamm_specular=1 --extra Wight openyamm_specular_mask=true --extra Wight pbr.metallicFactor=0 \
  --extra Dagger openyamm_specular=1 --extra Dagger openyamm_specular_mask=true --extra Dagger pbr.metallicFactor=0
python3 "$repo/tools/split_attachment.py" export/mm7_m430.glb --joint Dagger --body export/mm7_m430.glb \
  --attachment export/mm7_m430_dagger.glb
python3 "$repo/tools/merge_head_material.py" export/mm7_m430.glb export/mm7_m430.glb
rm -f export/mm7_m430_lods.geometry.glb
ls -la export/mm7_m430.glb export/mm7_m430_dagger.glb
