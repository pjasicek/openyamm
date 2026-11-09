#!/usr/bin/env bash
# Behemoth runtime GLB from the gated master (rebuild.sh -> rig_v3; texture chain export_uploads -> transfer_uv ->
# garments -> rig_v4u): clips synced into rig_v4 -> export -> prepare -> LODs -> shadow fix -> colour variants (one
# region: mane + beard) -> head merged into the body. NO install (batch E keeps everything in the project): the
# command that would install it is printed at the end.
# Usage: scripts/build_runtime.sh <creature lease token>
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
T=${1:?token}
cd "$repo"
P=level_generation/creatures/mm7_m162_claude
B() { local out log; out=$(tools/run_creature_blender.sh --token "$T" "$@" 2>&1) || { echo "$out"; exit 1; }
      log=$(echo "$out" | sed -n 's/^Blender log: //p'); grep -E "SYNC|EXPORTED|Error|Traceback" "$log" | cut -c1-240 || true; }
B $P/scripts/sync_actions.py $P/work/rig_v3.blend $P/work/rig_v4u.blend
cp $P/work/rig_v4u.blend $P/work/rig_v4.blend
B $P/scripts/export_runtime.py
cd "$here"
python3 "$repo/tools/prepare_actor_glb.py" export/mm7_m162_lod0.glb export/mm7_m162_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm7_m162_runtime_lod0.glb" \
  "$here/export/mm7_m162_lods.glb" --mesh-node M162 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm7_m162_lods.glb export/mm7_m162_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm7_m162_lods_shadowfix.glb export/mm7_m162.glb textures/m162_ramps.json \
  --extra M162 openyamm_specular=1 --extra M162 openyamm_specular_mask=true --extra M162 pbr.metallicFactor=0
python3 "$repo/tools/merge_head_material.py" export/mm7_m162.glb export/mm7_m162.glb
rm -f export/mm7_m162_lods.geometry.glb
ls -la export/mm7_m162.glb
echo "install later with: python3 tools/install_model.py $P/export/mm7_m162.glb --world mm7"
