#!/usr/bin/env bash
# m504 runtime GLB from the gated master (rebuild.sh -> rig_v5c; texture chain export_uploads -> Meshy -> transfer_uv
# -> rig_v6): clips synced into rig_v6 -> armpit weight fix (rig_v6w) -> LOD0 halved (rig_v6h) -> rubble death (rig_v7) -> UV rasters, AO, compose -> export -> prepare ->
# LODs of the body and of the rubble -> shadow fix -> colour variants (one region: all stone) -> head merged into the
# body -> collapsed-mesh hide keys (the rubble is not drawn while the body lives, the body not after the break).
# NOT installed (batch L rule): install later with the commands in README.md.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
blender=/snap/bin/blender
cd "$here"
B() { "$blender" --background --factory-startup --threads 4 --python-exit-code 1 --python "$@"; }
B scripts/sync_actions.py -- work/rig_v5c.blend work/rig_v6.blend 2>&1 | grep -E "SYNC|Error|Traceback" || true
# armpit fix (user review 2026-10-20: smeared stone under the raised arms): clavicle fade + torso weight smoothing
CL_IN=0.10 CL_OUT=0.25 ITER=40 TORSO=1 B scripts/armpit_smooth.py -- work/rig_v6.blend work/rig_v6w.blend 2>&1 | grep -E "^ARMPIT|Error|Traceback" || true
if [[ "${TEXTURES:-1}" == 1 ]]; then
  B scripts/uv_raster.py -- work/rig_v6.blend UVMap 1024 2>&1 | grep -E "Error|Traceback" || true
  B scripts/uv_raster.py -- work/rig_v6.blend HeadUV 1024 2>&1 | grep -E "Error|Traceback" || true
  B scripts/bake_ao_natm.py -- work/rig_v6.blend 1024 2>&1 | grep -E "^AO|Error|Traceback" || true
  python3 scripts/compose_m504.py | grep -E "NATIVE|CAPSQUARE|RAMP"
fi
# LOD0 halved (user, 2026-10-20), the face protected
PROTECT=B_Head B scripts/halve_lod0.py -- work/rig_v6w.blend work/rig_v6h.blend 2>&1 | grep -E "^HALVE|Error|Traceback" || true
B scripts/rubble.py -- work/rig_v6h.blend work/rig_v7.blend 2>&1 | grep -E "^RUBBLE|Error|Traceback" | cut -c1-200
B scripts/export_runtime.py 2>&1 | grep -E "EXPORTED|Error|Traceback" | cut -c1-300
python3 "$repo/tools/prepare_actor_glb.py" export/mm8_m504_lod0.glb export/mm8_m504_runtime_lod0.glb
for n in EarthElemental Rubble; do
  src=export/mm8_m504_runtime_lod0.glb; [[ $n == Rubble ]] && src=export/mm8_m504_lods_body.glb
  dst=export/mm8_m504_lods_body.glb; [[ $n == Rubble ]] && dst=export/mm8_m504_lods.glb
  "$blender" --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
    --python "$repo/tools/build_actor_lods.py" -- "$here/$src" "$here/$dst" --mesh-node $n 2>&1 | grep "LOD triangles"
done
python3 scripts/shrink_shadow_lods.py export/mm8_m504_lods.glb export/mm8_m504_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm8_m504_lods_shadowfix.glb export/mm8_m504.glb textures/m504_ramps.json \
  --extra EarthElemental openyamm_specular=1 --extra EarthElemental openyamm_specular_mask=true --extra EarthElemental pbr.metallicFactor=0
python3 "$repo/tools/merge_head_material.py" export/mm8_m504.glb export/mm8_m504.glb
python3 "$repo/tools/model_hide_collapsed_meshes.py" export/mm8_m504.glb --write export/mm8_m504.glb
rm -f export/mm8_m504_lods.geometry.glb export/mm8_m504_lods_body.geometry.glb
ls -la export/mm8_m504.glb
