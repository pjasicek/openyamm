#!/usr/bin/env bash
# Medusa runtime GLBs from the textured master work/anim_v2.blend (rig_medusa -> attach_props -> rig_hair -> uv_medusa ->
# anim_medusa; textures compose_m282.py + compose_head.py): export -> prepare -> LODs -> shadow fix -> colour variants
# (scale-mail region) -> bow and arrow split into attachments -> head material merged into the body.
# NO install (batch I keeps everything in the project): the commands that would install it are printed at the end.
# Usage: scripts/build_runtime.sh <creature lease token>
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
T=${1:?token}
cd "$repo"
P=level_generation/creatures/mm7_m282_claude
B() { local out log; out=$(tools/run_creature_blender.sh --token "$T" "$@" 2>&1) || { echo "$out"; exit 1; }
      log=$(echo "$out" | sed -n 's/^Blender log: //p'); grep -E "EXPORTED|Error|Traceback" "$log" | cut -c1-300 || true; }
B $P/scripts/export_runtime.py
cd "$here"
python3 "$repo/tools/prepare_actor_glb.py" export/mm7_m282_lod0.glb export/mm7_m282_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm7_m282_runtime_lod0.glb" \
  "$here/export/mm7_m282_lods.glb" --mesh-node M282 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm7_m282_lods.glb export/mm7_m282_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm7_m282_lods_shadowfix.glb export/mm7_m282.glb textures/m282_ramps.json \
  --extra M282 openyamm_specular=1 --extra M282 openyamm_specular_mask=true --extra M282 pbr.metallicFactor=0 \
  --extra M282Head openyamm_specular=1 --extra M282Head openyamm_specular_mask=true --extra M282Head pbr.metallicFactor=0 \
  --extra Bow openyamm_specular=0.5 --extra Bow openyamm_specular_mask=true --extra Bow pbr.metallicFactor=0 \
  --extra Arrow openyamm_specular=0.5 --extra Arrow openyamm_specular_mask=true --extra Arrow pbr.metallicFactor=0
python3 "$repo/tools/split_attachment.py" export/mm7_m282.glb --joint Bow --body export/mm7_m282.glb \
  --attachment export/mm7_m282_bow.glb
python3 "$repo/tools/split_attachment.py" export/mm7_m282.glb --joint Arrow --body export/mm7_m282.glb \
  --attachment export/mm7_m282_arrow.glb
python3 "$repo/tools/merge_head_material.py" export/mm7_m282.glb export/mm7_m282.glb
rm -f export/mm7_m282_lods.geometry.glb export/mm7_m282_lods.glb export/mm7_m282_lods_shadowfix.glb export/mm7_m282_runtime_lod0.glb
ls -la export/mm7_m282.glb export/mm7_m282_bow.glb export/mm7_m282_arrow.glb
echo "install later with:"
for g in mm7_m282 mm7_m282_bow mm7_m282_arrow; do echo "  python3 tools/install_model.py $P/export/$g.glb --world mm7"; done
