#!/usr/bin/env bash
# m238 runtime GLB from the gated master (rebuild.sh STAGE=anim -> rig_v5; texture chain export_uploads -> Meshy ->
# transfer_uv -> rig_v6): clips synced into rig_v6 -> (TEXTURES=1: UV rasters, AO, compose) -> export (body + lamp mesh
# nodes) -> prepare -> LODs -> shadow fix -> colour variants (one region: the green cloth) -> head merged into the body
# -> collapsed mesh nodes hidden (lamp while alive, body when gone). NOTHING is installed (batch G).
# Every step runs in a memory-capped scope (cap.sh).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
: "${TOKEN:?set TOKEN to the workspace lease token}"
C="$here/scripts/cap.sh"
B() { local s=$1; shift; local out log; out=$(cd "$repo" && "$C" "$repo/tools/run_creature_blender.sh" --token "$TOKEN" "level_generation/creatures/mm7_m238_claude/scripts/$s" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if [ -z "$log" ] || grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $s"; exit 1; fi
      grep -E "SYNC|PROP|EXPORTED|^AO|UVR" "$log" | cut -c1-200 || true; }
cd "$here"
B sync_actions.py "$here/work/rig_v5.blend" "$here/work/rig_v6.blend"
if [[ "${TEXTURES:-1}" == 1 ]]; then
  B uv_raster.py "$here/work/rig_v6.blend" UVMap 1024
  B uv_raster.py "$here/work/rig_v6.blend" HeadUV 1024
  B bake_ao_natm.py "$here/work/rig_v6.blend" 1024
  "$C" python3 scripts/compose_m238.py | grep -E "REGION|NATIVE|CLASSES|RAMP|PROPS"
fi
B export_runtime.py
"$C" python3 "$repo/tools/prepare_actor_glb.py" export/mm7_m238_lod0.glb export/mm7_m238_runtime_lod0.glb
"$C" /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm7_m238_runtime_lod0.glb" \
  "$here/export/mm7_m238_lods.glb" --mesh-node M238 2>&1 | grep "LOD triangles"
"$C" python3 scripts/shrink_shadow_lods.py export/mm7_m238_lods.glb export/mm7_m238_lods_shadowfix.glb
"$C" python3 ../claude_shared/region_variants.py export/mm7_m238_lods_shadowfix.glb export/mm7_m238.glb textures/m238_ramps.json \
  --extra M238 openyamm_specular=1 --extra M238 openyamm_specular_mask=true --extra M238 pbr.metallicFactor=0 \
  --extra M238Head openyamm_specular=1 --extra M238Head openyamm_specular_mask=true --extra M238Head pbr.metallicFactor=0 \
  --extra Lamp openyamm_specular=1 --extra Lamp openyamm_specular_mask=true --extra Lamp pbr.metallicFactor=0
"$C" python3 "$repo/tools/merge_head_material.py" export/mm7_m238.glb export/mm7_m238.glb
"$C" python3 "$repo/tools/model_hide_collapsed_meshes.py" export/mm7_m238.glb --write export/mm7_m238.glb
rm -f export/mm7_m238_lods.geometry.glb
ls -la export/mm7_m238.glb
