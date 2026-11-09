#!/usr/bin/env bash
# Rebuild the runtime GLB chain from the authoring master: export -> prepare -> LODs -> skins -> install.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
blender=/snap/bin/blender
# Shared-skin tiers, 1K body base colour and the head texture set (inputs of the export below).
python3 "$here/scripts/tier_ramps.py" > /dev/null
python3 "$here/scripts/compose_head.py" > /dev/null
"$blender" --background "$here/work/final_v1.blend" --python "$here/scripts/export_glb.py" 2>&1 | grep EXPORTED
python3 "$repo/tools/prepare_actor_glb.py" "$here/export/mm6_gob_lod0.glb" "$here/export/mm6_gob_runtime_lod0.glb"
"$blender" --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_gob_runtime_lod0.glb" \
  "$here/export/mm6_gob_lods.glb" --mesh-node Peasant 2>&1 | grep "LOD triangles"
python3 "$here/scripts/shrink_shadow_lods.py" "$here/export/mm6_gob_lods.glb" "$here/export/mm6_gob_lods_shadowfix.glb"
# Tiers: one shared skin + region mask + ramps (rerun scripts/tier_ramps.py after compose/grade).
python3 "$here/../claude_shared/region_variants.py" "$here/export/mm6_gob_lods_shadowfix.glb" \
  "$here/export/mm6_gob.glb" "$here/textures/gob_ramps.json" --extra GoblinHead openyamm_specular=0 --extra GoblinHead pbr.metallicFactor=0
# The sword becomes an attachment on its Sword bone (actors.yml `attachments`), so variants can carry other weapons.
python3 "$repo/tools/split_attachment.py" "$here/export/mm6_gob.glb" --joint Sword \
  --body "$here/export/mm6_gob.glb" --attachment "$here/export/mm6_gob_sword.glb"
# One material per creature: the head texture set joins the body in a body|head atlas (one draw instead of two).
python3 "$repo/tools/merge_head_material.py" "$here/export/mm6_gob.glb" "$here/export/mm6_gob.glb"
rm -f "$here/export/mm6_gob_lods.geometry.glb"
if [[ "${1:-}" == "--install" ]]; then
  for name in mm6_gob mm6_gob_sword; do
    install -m 0664 "$here/export/$name.glb" "$repo/assets_dev/worlds/mm6/models/$name.glb"
    echo "installed $repo/assets_dev/worlds/mm6/models/$name.glb"
  done
fi
