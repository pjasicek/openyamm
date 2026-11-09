#!/usr/bin/env bash
# m242 runtime GLB from the master (rebuild.sh -> rig_v3 clips; reduce_ghost -> rig_v4; texture chain export_uploads ->
# Meshy -> transfer_uv -> rig_v6): clips synced into rig_v6 -> (TEXTURES=1: UV rasters, AO, compose) -> export ->
# prepare -> LODs -> shadow fix -> colour variants (one region: the robe) -> head merged into the body.
# NOTHING is installed (batch G: the user installs later; the commands are in the README). Memory-capped steps.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
: "${TOKEN:?set TOKEN to the workspace lease token}"
export CAP=${CAP:-8G}
C="$here/scripts/cap.sh"; B="$here/scripts/b.sh"
cd "$here"
PAT=SYNC $B sync_actions.py "$here/work/rig_v3.blend" "$here/work/rig_v6.blend"
if [[ "${TEXTURES:-1}" == 1 ]]; then
  PAT=XX $B uv_raster.py "$here/work/rig_v6.blend" UVMap 1024 || true
  PAT=XX $B uv_raster.py "$here/work/rig_v6.blend" HeadUV 1024 || true
  PAT="^AO" $B bake_ao_natm.py "$here/work/rig_v6.blend" 1024
  "$C" python3 scripts/compose_m242.py | grep -E "REGION|CLASSES|RAMP|SOCKET"
fi
PAT="EXPORTED" $B export_runtime.py | cut -c1-200
"$C" python3 "$repo/tools/prepare_actor_glb.py" export/mm7_m242_lod0.glb export/mm7_m242_runtime_lod0.glb
"$C" /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm7_m242_runtime_lod0.glb" \
  "$here/export/mm7_m242_lods.glb" --mesh-node M242 2>&1 | grep "LOD triangles"
"$C" python3 scripts/shrink_shadow_lods.py export/mm7_m242_lods.glb export/mm7_m242_lods_shadowfix.glb
"$C" python3 ../claude_shared/region_variants.py export/mm7_m242_lods_shadowfix.glb export/mm7_m242.glb textures/m242_ramps.json \
  --extra M242 openyamm_specular=1 --extra M242 openyamm_specular_mask=true --extra M242 pbr.metallicFactor=0 \
  --extra M242Head openyamm_specular=1 --extra M242Head openyamm_specular_mask=true --extra M242Head pbr.metallicFactor=0
"$C" python3 "$repo/tools/merge_head_material.py" export/mm7_m242.glb export/mm7_m242.glb
rm -f export/mm7_m242_lods.geometry.glb
ls -la export/mm7_m242.glb
