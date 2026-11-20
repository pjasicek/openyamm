#!/usr/bin/env bash
# MM7 Sea Monster (shark) runtime GLB from the textured master work/anim_v2u.blend (rig_shark -> anim_shark -> transfer_uv):
# export -> prepare -> LODs -> shadow fix -> colour variants (blue skin). NO install (batch L keeps everything in the project): the
# command that would install it is printed at the end.
# Usage: scripts/build_runtime.sh <creature lease token>
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
T=${1:?token}
cd "$repo"
P=level_generation/creatures/mm7_m394_claude
B() { local out log; out=$(tools/run_creature_blender.sh --token "$T" "$@" 2>&1) || { echo "$out"; exit 1; }
      log=$(echo "$out" | sed -n 's/^Blender log: //p'); grep -E "SYNC|EXPORTED|Error|Traceback" "$log" | cut -c1-240 || true; }
B $P/scripts/sync_actions.py $P/work/anim_v1.blend $P/work/anim_v2u.blend
PROTECT=Head,Jaw B $P/scripts/halve_lod0.py $P/work/anim_v2u.blend $P/work/anim_v2h.blend   # LOD0 halved (user, 2026-10-20)
B $P/scripts/export_runtime.py
cd "$here"
python3 "$repo/tools/prepare_actor_glb.py" export/mm7_m394_lod0.glb export/mm7_m394_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm7_m394_runtime_lod0.glb" \
  "$here/export/mm7_m394_lods.glb" --mesh-node M394 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm7_m394_lods.glb export/mm7_m394_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm7_m394_lods_shadowfix.glb export/mm7_m394.glb textures/m394_ramps.json \
  --extra M394 openyamm_specular=1 --extra M394 openyamm_specular_mask=true --extra M394 pbr.metallicFactor=0
rm -f export/mm7_m394_lods.geometry.glb export/mm7_m394_lods.glb export/mm7_m394_lods_shadowfix.glb export/mm7_m394_runtime_lod0.glb
ls -la export/mm7_m394.glb
echo "install later with: python3 tools/install_model.py $P/export/mm7_m394.glb --world mm7"
