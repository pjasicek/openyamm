#!/usr/bin/env bash
# m322 runtime GLBs from the gated, textured master (adapted from mm7_m218_claude / mm7_m222_claude): clips synced from rig_v5 into
# rig_v6 -> export -> prepare -> LODs -> shadow fix -> colour variants (cloth + hair, nine palettes) -> staff split into
# an attachment -> head merged into the body. No install (batch C keeps everything in the project); the install commands
# are in the README. Token: CREATURE_3D_TOKEN.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
P=level_generation/creatures/mm7_m322_claude
B() { (cd "$repo" && tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" "$P/scripts/$1" "${@:2}") | sed -n 's/^Blender log: //p' | xargs grep -hE "SYNC|PROP|EXPORTED|Error|Traceback" | cut -c1-200 || true; }
cd "$here"
[ "${SKIP_SYNC:-}" ] || B sync_actions.py "$here/work/rig_v5.blend" "$here/work/rig_v6.blend"
B export_runtime.py
python3 "$repo/tools/prepare_actor_glb.py" export/mm7_m322_lod0.glb export/mm7_m322_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm7_m322_runtime_lod0.glb" \
  "$here/export/mm7_m322_lods.glb" --mesh-node Elf 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm7_m322_lods.glb export/mm7_m322_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm7_m322_lods_shadowfix.glb export/mm7_m322.glb textures/m322_ramps.json \
  --extra Elf openyamm_specular=1 --extra Elf openyamm_specular_mask=true --extra Elf pbr.metallicFactor=0 \
  --extra Staff openyamm_specular=1 --extra Staff openyamm_specular_mask=true --extra Staff pbr.metallicFactor=0
python3 "$repo/tools/split_attachment.py" export/mm7_m322.glb --joint Sword --body export/mm7_m322.glb \
  --attachment export/mm7_m322_staff.glb
python3 scripts/clamp_lod_uv.py export/mm7_m322.glb
python3 "$repo/tools/merge_head_material.py" export/mm7_m322.glb export/mm7_m322.glb
rm -f export/mm7_m322_lods.geometry.glb
ls -la export/mm7_m322.glb export/mm7_m322_staff.glb
