#!/usr/bin/env bash
# Ooze runtime GLB from the animated master work/anim_v1.blend (rig_ooze -> uv_export -> anim_ooze; textures from
# tex_prep + compose_ooze): export -> prepare -> LODs -> shadow fix -> colour variants (one slime region).
# NO install (batch I keeps everything in the project): the command that would install it is printed at the end.
# Usage: scripts/build_runtime.sh <creature lease token>
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
T=${1:?token}
cd "$repo"
P=level_generation/creatures/mm7_m298_claude
B() { local out log; out=$(tools/run_creature_blender.sh --token "$T" "$@" 2>&1) || { echo "$out"; exit 1; }
      log=$(echo "$out" | sed -n 's/^Blender log: //p'); grep -E "DISC|EXPORTED|Error|Traceback" "$log" | cut -c1-400 || true; }
B $P/scripts/export_runtime.py
cd "$here"
python3 "$repo/tools/prepare_actor_glb.py" export/mm7_m298_lod0.glb export/mm7_m298_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm7_m298_runtime_lod0.glb" \
  "$here/export/mm7_m298_lods.glb" --mesh-node Ooze 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm7_m298_lods.glb export/mm7_m298_lods_shadowfix.glb
# Wet slime keeps engine specular (mm6_ooz_claude: 0.7 after user review), masked per texel by the ORM red channel;
# metallic 0.
python3 ../claude_shared/region_variants.py export/mm7_m298_lods_shadowfix.glb export/mm7_m298.glb textures/ooze_ramps.json \
  --extra Ooze openyamm_specular=0.7 --extra Ooze openyamm_specular_mask=true --extra Ooze pbr.metallicFactor=0
rm -f export/mm7_m298_lods.geometry.glb export/mm7_m298_lods.glb export/mm7_m298_lods_shadowfix.glb export/mm7_m298_runtime_lod0.glb
ls -la export/mm7_m298.glb
echo "install later with: python3 tools/install_model.py $P/export/mm7_m298.glb --world mm7"
