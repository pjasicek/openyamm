#!/usr/bin/env bash
# m214 runtime GLBs from the gated, textured master (adapted from mm6_natm_claude): clips synced from rig_v5 into
# rig_v6 -> export -> prepare -> LODs -> shadow fix -> colour variants (cloth + hair) -> bow and arrow split into
# attachments -> head merged into the body. No install (batch C keeps everything in the project); the install commands
# are in the README. Token: CREATURE_3D_TOKEN.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
P=level_generation/creatures/mm7_m214_claude
B() { (cd "$repo" && tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" "$P/scripts/$1" "${@:2}") | sed -n 's/^Blender log: //p' | xargs grep -hE "SYNC|PROP|EXPORTED|Error|Traceback" | cut -c1-200 || true; }
cd "$here"
[ "${SKIP_SYNC:-}" ] || B sync_actions.py "$here/work/rig_v5.blend" "$here/work/rig_v6.blend"
B export_runtime.py
python3 "$repo/tools/prepare_actor_glb.py" export/mm7_m214_lod0.glb export/mm7_m214_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm7_m214_runtime_lod0.glb" \
  "$here/export/mm7_m214_lods.glb" --mesh-node Elf 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm7_m214_lods.glb export/mm7_m214_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm7_m214_lods_shadowfix.glb export/mm7_m214.glb textures/m214_ramps.json \
  --extra Elf openyamm_specular=1 --extra Elf openyamm_specular_mask=true --extra Elf pbr.metallicFactor=0 \
  --extra Bow openyamm_specular=0.5 --extra Bow openyamm_specular_mask=true --extra Bow pbr.metallicFactor=0 \
  --extra Arrow openyamm_specular=0.5 --extra Arrow openyamm_specular_mask=true --extra Arrow pbr.metallicFactor=0
python3 "$repo/tools/split_attachment.py" export/mm7_m214.glb --joint Bow --body export/mm7_m214.glb \
  --attachment export/mm7_m214_bow.glb
python3 "$repo/tools/split_attachment.py" export/mm7_m214.glb --joint Arrow --body export/mm7_m214.glb \
  --attachment export/mm7_m214_arrow.glb
python3 scripts/clamp_lod_uv.py export/mm7_m214.glb
python3 "$repo/tools/merge_head_material.py" export/mm7_m214.glb export/mm7_m214.glb
rm -f export/mm7_m214_lods.geometry.glb
ls -la export/mm7_m214.glb export/mm7_m214_bow.glb export/mm7_m214_arrow.glb
