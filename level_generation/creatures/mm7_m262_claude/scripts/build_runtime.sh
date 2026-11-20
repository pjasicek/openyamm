#!/usr/bin/env bash
# m262 runtime GLBs from the gated master (rebuild.sh STAGE=wings -> rig_v5x; texture chain export_uploads -> Meshy ->
# transfer_uv -> rig_v6): clips synced into rig_v6 -> (TEXTURES=1: UV rasters, AO, compose) -> export -> prepare ->
# LODs -> shadow fix -> colour variants (two regions: flight feathers, metal inserts) -> knife split into an attachment -> head
# merged into the body. NOTHING is installed (batch G: the user installs later; the commands are in the README).
# Every step runs in a memory-capped scope (cap.sh).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
: "${TOKEN:?set TOKEN to the workspace lease token}"
C="$here/scripts/cap.sh"
B() { local s=$1; shift; local out log; out=$(cd "$repo" && "$C" "$repo/tools/run_creature_blender.sh" --token "$TOKEN" "level_generation/creatures/mm7_m262_claude/scripts/$s" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if [ -z "$log" ] || grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $s"; exit 1; fi
      grep -E "SYNC|PROP|EXPORTED|^AO|UVR" "$log" | cut -c1-200 || true; }
cd "$here"
B sync_actions.py "$here/work/rig_v5x.blend" "$here/work/rig_v6.blend"
if [[ "${TEXTURES:-1}" == 1 ]]; then
  B uv_raster.py "$here/work/rig_v6.blend" UVMap 1024
  B uv_raster.py "$here/work/rig_v6.blend" HeadUV 1024
  B bake_ao_natm.py "$here/work/rig_v6.blend" 1024
  "$C" python3 scripts/compose_m262.py | grep -E "REGION|NATIVE|CLASSES|RAMP|PROPS"
fi
B export_runtime.py
"$C" python3 "$repo/tools/prepare_actor_glb.py" export/mm7_m262_lod0.glb export/mm7_m262_runtime_lod0.glb
"$C" /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm7_m262_runtime_lod0.glb" \
  "$here/export/mm7_m262_lods.glb" --mesh-node M262 2>&1 | grep "LOD triangles"
"$C" python3 scripts/shrink_shadow_lods.py export/mm7_m262_lods.glb export/mm7_m262_lods_shadowfix.glb
"$C" python3 ../claude_shared/region_variants.py export/mm7_m262_lods_shadowfix.glb export/mm7_m262.glb textures/m262_ramps.json \
  --extra M262 openyamm_specular=1 --extra M262 openyamm_specular_mask=true --extra M262 pbr.metallicFactor=0 \
  --extra M262Head openyamm_specular=1 --extra M262Head openyamm_specular_mask=true --extra M262Head pbr.metallicFactor=0 \
  --extra Sword openyamm_specular=1 --extra Sword openyamm_specular_mask=true --extra Sword pbr.metallicFactor=0
"$C" python3 "$repo/tools/split_attachment.py" export/mm7_m262.glb --joint Sword --body export/mm7_m262.glb \
  --attachment export/mm7_m262_sword.glb
"$C" python3 "$repo/tools/merge_head_material.py" export/mm7_m262.glb export/mm7_m262.glb
rm -f export/mm7_m262_lods.geometry.glb
ls -la export/mm7_m262.glb export/mm7_m262_sword.glb
