#!/usr/bin/env bash
# m218 runtime GLBs from the gated, textured master (adapted from mm6_natm_claude): clips synced from rig_v5 into
# rig_v6 -> export -> prepare -> LODs -> shadow fix -> colour variants (loincloth) -> spear split into
# an attachment -> head merged into the body. No install (batch C keeps everything in the project); the install commands
# are in the README. Token: CREATURE_3D_TOKEN.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
P=level_generation/creatures/mm7_m218_claude
B() { (cd "$repo" && tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" "$P/scripts/$1" "${@:2}") | sed -n 's/^Blender log: //p' | xargs grep -hE "SYNC|PROP|EXPORTED|Error|Traceback" | cut -c1-200 || true; }
cd "$here"
[ "${SKIP_SYNC:-}" ] || B sync_actions.py "$here/work/rig_v5.blend" "$here/work/rig_v6.blend"
B export_runtime.py
python3 "$repo/tools/prepare_actor_glb.py" export/mm7_m218_lod0.glb export/mm7_m218_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm7_m218_runtime_lod0.glb" \
  "$here/export/mm7_m218_lods.glb" --mesh-node Elf 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm7_m218_lods.glb export/mm7_m218_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm7_m218_lods_shadowfix.glb export/mm7_m218.glb textures/m218_ramps.json \
  --extra Elf openyamm_specular=1 --extra Elf openyamm_specular_mask=true --extra Elf pbr.metallicFactor=0 \
  --extra SpearProp openyamm_specular=0.5 --extra SpearProp openyamm_specular_mask=true --extra SpearProp pbr.metallicFactor=0
python3 "$repo/tools/split_attachment.py" export/mm7_m218.glb --joint Spear --body export/mm7_m218.glb \
  --attachment export/mm7_m218_spear.glb
python3 scripts/clamp_lod_uv.py export/mm7_m218.glb
python3 "$repo/tools/merge_head_material.py" export/mm7_m218.glb export/mm7_m218.glb
rm -f export/mm7_m218_lods.geometry.glb
ls -la export/mm7_m218.glb export/mm7_m218_spear.glb
