#!/usr/bin/env bash
# m254 golem runtime GLBs from the gated, textured master (adapted from mm7_m414_claude): clips synced from rig_v5 into
# rig_v6 -> export -> prepare -> LODs -> shadow fix -> colour variants (dark and light stripes) -> head merged into the
# body. Unarmed: no attachment. No install (batch I keeps everything in the project); the install command is in the
# README. Token: CREATURE_3D_TOKEN.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
P=level_generation/creatures/mm7_m254_claude
B() { (cd "$repo" && tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" "$P/scripts/$1" "${@:2}") | sed -n 's/^Blender log: //p' | xargs grep -hE "SYNC|PROP|EXPORTED|Error|Traceback" | cut -c1-200 || true; }
cd "$here"
[ "${SKIP_SYNC:-}" ] || B sync_actions.py "$here/work/rig_v5.blend" "$here/work/rig_v6.blend"
B export_runtime.py
python3 "$repo/tools/prepare_actor_glb.py" export/mm7_m254_lod0.glb export/mm7_m254_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm7_m254_runtime_lod0.glb" \
  "$here/export/mm7_m254_lods.glb" --mesh-node Golem 2>&1 | grep "LOD triangles"
MESH_NODE=Golem python3 scripts/shrink_shadow_lods.py export/mm7_m254_lods.glb export/mm7_m254_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm7_m254_lods_shadowfix.glb export/mm7_m254.glb textures/m254_ramps.json \
  --extra Golem openyamm_specular=1 --extra Golem openyamm_specular_mask=true --extra Golem pbr.metallicFactor=0
python3 scripts/clamp_lod_uv.py export/mm7_m254.glb
python3 "$repo/tools/merge_head_material.py" export/mm7_m254.glb export/mm7_m254.glb
rm -f export/mm7_m254_lods.geometry.glb
ls -la export/mm7_m254.glb
