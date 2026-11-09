#!/usr/bin/env bash
# Manticore runtime GLB from the textured master work/anim_v2u.blend (rig_manticore -> anim_manticore -> uv_export):
# export -> prepare -> LODs -> shadow fix -> colour variants (mane, fur). NO install (batch E keeps everything in the project): the
# command that would install it is printed at the end.
# Usage: scripts/build_runtime.sh <creature lease token>
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
T=${1:?token}
cd "$repo"
P=level_generation/creatures/mm7_m266_claude
B() { local out log; out=$(tools/run_creature_blender.sh --token "$T" "$@" 2>&1) || { echo "$out"; exit 1; }
      log=$(echo "$out" | sed -n 's/^Blender log: //p'); grep -E "SYNC|EXPORTED|Error|Traceback" "$log" | cut -c1-240 || true; }
B $P/scripts/export_runtime.py
cd "$here"
python3 "$repo/tools/prepare_actor_glb.py" export/mm7_m266_lod0.glb export/mm7_m266_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm7_m266_runtime_lod0.glb" \
  "$here/export/mm7_m266_lods.glb" --mesh-node M266 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm7_m266_lods.glb export/mm7_m266_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm7_m266_lods_shadowfix.glb export/mm7_m266.glb textures/m266_ramps.json \
  --extra Hydra openyamm_specular=1 --extra Hydra openyamm_specular_mask=true --extra Hydra pbr.metallicFactor=0
rm -f export/mm7_m266_lods.geometry.glb export/mm7_m266_lods.glb export/mm7_m266_lods_shadowfix.glb export/mm7_m266_runtime_lod0.glb
ls -la export/mm7_m266.glb
echo "install later with: python3 tools/install_model.py $P/export/mm7_m266.glb --world mm7"
