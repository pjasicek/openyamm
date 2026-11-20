#!/usr/bin/env bash
# m150 runtime GLBs from the gated master (rebuild.sh STAGE=wings -> rig_v5x; texture chain export_uploads -> Meshy ->
# transfer_uv -> rig_v6): clips synced into rig_v6 -> (TEXTURES=1: UV rasters, AO, compose) -> export -> prepare ->
# LODs -> shadow fix -> colour variants (one region: the skirt) -> sword and shield split into attachments -> head
# merged into the body. NOTHING is installed (batch G: the user installs later; the commands are in the README).
# Every step runs in a memory-capped scope (cap.sh).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
: "${TOKEN:?set TOKEN to the workspace lease token}"
C="$here/scripts/cap.sh"
B() { local s=$1; shift; local out log; out=$(cd "$repo" && "$C" "$repo/tools/run_creature_blender.sh" --token "$TOKEN" "level_generation/creatures/mm7_m150_claude/scripts/$s" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if [ -z "$log" ] || grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $s"; exit 1; fi
      grep -E "SYNC|WINGSCALE|HELMETFIT|STRAPWEIGHTS|SKIRTINFLATE|PROP|EXPORTED|^AO|UVR|FEATHERS" "$log" | cut -c1-200 || true; }
cd "$here"
B sync_actions.py "$here/work/rig_v5x.blend" "$here/work/rig_v6.blend"
B wings_scale.py "$here/work/rig_v6.blend"        # once: native wing proportions (flag on the rig)
B helmet_fit.py "$here/work/rig_v6.blend"         # once: v2 helmet on the head, scalp pushed inside (flag on the rig)
B strap_weights.py "$here/work/rig_v6.blend"      # straps follow the clavicle (idempotent)
B skirt_inflate.py "$here/work/rig_v6.blend"      # once: skirt and tabs >= 2 cm off the thighs (flag on the rig)
if [[ "${TEXTURES:-1}" == 1 ]]; then
  B uv_raster.py "$here/work/rig_v6.blend" UVMap 1024
  B uv_raster.py "$here/work/rig_v6.blend" HeadUV 1024
  B bake_ao_natm.py "$here/work/rig_v6.blend" 1024
  RIM_PX=${RIM_PX:-3} "$C" python3 scripts/compose_m150.py | grep -E "REGION|NATIVE|CLASSES|RAMP|PROPS|STRAPS|AOCLEAN|FEATHERS"
fi
B export_runtime.py
"$C" python3 "$repo/tools/prepare_actor_glb.py" export/mm7_m150_lod0.glb export/mm7_m150_runtime_lod0.glb
"$C" /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm7_m150_runtime_lod0.glb" \
  "$here/export/mm7_m150_lods.glb" --mesh-node M150 2>&1 | grep "LOD triangles"
"$C" python3 scripts/shrink_shadow_lods.py export/mm7_m150_lods.glb export/mm7_m150_lods_shadowfix.glb
"$C" python3 ../claude_shared/region_variants.py export/mm7_m150_lods_shadowfix.glb export/mm7_m150.glb textures/m150_ramps.json \
  --extra M150 openyamm_specular=1 --extra M150 openyamm_specular_mask=true --extra M150 pbr.metallicFactor=0 \
  --extra M150Head openyamm_specular=1 --extra M150Head openyamm_specular_mask=true --extra M150Head pbr.metallicFactor=0 \
  --extra Sword openyamm_specular=1 --extra Sword openyamm_specular_mask=true --extra Sword pbr.metallicFactor=0 \
  --extra Shield openyamm_specular=1 --extra Shield openyamm_specular_mask=true --extra Shield pbr.metallicFactor=0 \
  --extra Helmet openyamm_specular=1 --extra Helmet openyamm_specular_mask=true --extra Helmet pbr.metallicFactor=0
"$C" python3 "$repo/tools/split_attachment.py" export/mm7_m150.glb --joint Sword --body export/mm7_m150.glb \
  --attachment export/mm7_m150_sword.glb
"$C" python3 "$repo/tools/split_attachment.py" export/mm7_m150.glb --joint Shield --body export/mm7_m150.glb \
  --attachment export/mm7_m150_shield.glb
"$C" python3 "$repo/tools/split_attachment.py" export/mm7_m150.glb --joint Helmet --body export/mm7_m150.glb \
  --attachment export/mm7_m150_helmet.glb
"$C" python3 "$repo/tools/merge_head_material.py" export/mm7_m150.glb export/mm7_m150.glb
rm -f export/mm7_m150_lods.geometry.glb
ls -la export/mm7_m150.glb export/mm7_m150_sword.glb export/mm7_m150_shield.glb export/mm7_m150_helmet.glb
