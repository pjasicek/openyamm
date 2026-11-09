#!/usr/bin/env bash
# Rebuild the runtime GLBs from the authoring master: textures -> head set (+ hands) -> export -> prepare -> LODs
# -> shadow fix -> colour variants -> staff split into an attachment -> head merged into the body material -> install.
# Inputs: work/rig_v4.blend (scripts/rebuild_clips.sh), work/ao_body.png (claude_shared/bake_creature_ao.py on rig_v2),
# work/uv3d.npz (dump_uv3d.py on rig_v2), meshy/retexture_v1 and meshy/head_retexture_v1.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
blender=/snap/bin/blender
cd "$here"
python3 scripts/native_pixels.py | head -1
python3 scripts/prepare_textures.py | grep MAPS | cut -c1-200
python3 ../claude_shared/compose_head_set.py "$here" cle work/rig_v4.blend Cleric "$here/textures/cle_a_basecolor.png" \
  --local 0.4 --contrast 1.05 | tail -1
python3 scripts/hand_texture_set.py
"$blender" --background --python scripts/export_runtime.py 2>&1 | grep -E "STAFF|HANDS|LINING|SOCKETS|JOINED|EXPORTED|Error|Traceback" \
  | cut -c1-300
python3 "$repo/tools/prepare_actor_glb.py" export/mm6_cle_lod0.glb export/mm6_cle_runtime_lod0.glb
"$blender" --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_cle_runtime_lod0.glb" \
  "$here/export/mm6_cle_lods.glb" --mesh-node Cleric 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm6_cle_lods.glb export/mm6_cle_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm6_cle_lods_shadowfix.glb export/mm6_cle.glb textures/cle_ramps.json \
  --extra Cleric openyamm_specular=0 --extra Cleric pbr.metallicFactor=0 \
  --extra ClericHead openyamm_specular=0 --extra ClericHead pbr.metallicFactor=0
# the staff becomes an attachment on its Staff bone (actors.yml `attachments`), then one material per tier: the head
# texture set joins the body in a body|head atlas (one draw instead of two)
python3 "$repo/tools/split_attachment.py" export/mm6_cle.glb --joint Staff --body export/mm6_cle.glb \
  --attachment export/mm6_cle_staff.glb
python3 "$repo/tools/merge_head_material.py" export/mm6_cle.glb export/mm6_cle.glb
rm -f export/mm6_cle_lods.geometry.glb
if [[ "${1:-}" == "--install" ]]; then
  for name in mm6_cle mm6_cle_staff; do
    install -m 0664 "export/$name.glb" "$repo/assets_dev/worlds/mm6/models/$name.glb"
    echo "installed $repo/assets_dev/worlds/mm6/models/$name.glb"
  done
fi
python3 scripts/viewer_tiers.py
python3 scripts/update_viewer_manifest.py
