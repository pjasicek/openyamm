#!/usr/bin/env bash
# Treant runtime GLB from the textured master work/anim_v1.blend (rig_treant -> uv_export -> eyes_add -> reduce_roots ->
# anim_treant): export -> prepare -> LODs -> shadow fix -> material extras (one material, no tiers). NO install (batch I
# keeps everything in the project): the command that would install it is printed at the end.
# Usage: scripts/build_runtime.sh <creature lease token>
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
T=${1:?token}
cd "$repo"
P=level_generation/creatures/mm7_m479_claude
B() { local out log; out=$(tools/run_creature_blender.sh --token "$T" "$@" 2>&1) || { echo "$out"; exit 1; }
      log=$(echo "$out" | sed -n 's/^Blender log: //p'); grep -E "SYNC|EXPORTED|Error|Traceback" "$log" | cut -c1-240 || true; }
B $P/scripts/export_runtime.py
cd "$here"
python3 "$repo/tools/prepare_actor_glb.py" export/mm7_m479_lod0.glb export/mm7_m479_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm7_m479_runtime_lod0.glb" \
  "$here/export/mm7_m479_lods.glb" --mesh-node M479 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm7_m479_lods.glb export/mm7_m479_lods_shadowfix.glb
python3 scripts/set_extras.py export/mm7_m479_lods_shadowfix.glb export/mm7_m479.glb M479 \
  openyamm_specular=1 openyamm_specular_mask=true pbr.metallicFactor=0
rm -f export/mm7_m479_lods.geometry.glb export/mm7_m479_lods.glb export/mm7_m479_lods_shadowfix.glb export/mm7_m479_runtime_lod0.glb
ls -la export/mm7_m479.glb
echo "install later with: python3 tools/install_model.py $P/export/mm7_m479.glb --world mm7"
