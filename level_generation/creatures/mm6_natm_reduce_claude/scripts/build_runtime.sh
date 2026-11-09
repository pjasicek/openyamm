#!/usr/bin/env bash
# natm runtime GLBs from the gated master (rebuild.sh -> rig_v5; texture chain export_uploads -> transfer_uv -> rig_v6):
# clips synced into rig_v6 -> export -> prepare -> LODs -> shadow fix -> colour variants (one region: cloth) -> spear
# and buckler split into attachments -> head merged into the body.
# --install: tools/install_model.py for body, spear and buckler (sources in assets_source, runtime copies in assets_dev).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
blender=/snap/bin/blender
cd "$here"
B() { "$blender" --background --factory-startup --threads 4 --python-exit-code 1 --python "$@"; }
B scripts/sync_actions.py -- work/rig_v5.blend work/rig_v6.blend 2>&1 | grep -E "SYNC|Error|Traceback" || true
B scripts/export_runtime.py 2>&1 | grep -E "PROP|EXPORTED|Error|Traceback" | cut -c1-200
python3 "$repo/tools/prepare_actor_glb.py" export/mm6_natm_lod0.glb export/mm6_natm_runtime_lod0.glb
"$blender" --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_natm_runtime_lod0.glb" \
  "$here/export/mm6_natm_lods.glb" --mesh-node Natm 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm6_natm_lods.glb export/mm6_natm_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm6_natm_lods_shadowfix.glb export/mm6_natm.glb textures/natm_ramps.json \
  --extra Natm openyamm_specular=1 --extra Natm openyamm_specular_mask=true --extra Natm pbr.metallicFactor=0 \
  --extra Spear openyamm_specular=1 --extra Spear openyamm_specular_mask=true --extra Spear pbr.metallicFactor=0 \
  --extra Buckler openyamm_specular=0.5 --extra Buckler openyamm_specular_mask=true --extra Buckler pbr.metallicFactor=0
python3 "$repo/tools/split_attachment.py" export/mm6_natm.glb --joint Spear --body export/mm6_natm.glb \
  --attachment export/mm6_natm_spear.glb
python3 "$repo/tools/split_attachment.py" export/mm6_natm.glb --joint Buckler --body export/mm6_natm.glb \
  --attachment export/mm6_natm_buckler.glb
python3 "$repo/tools/merge_head_material.py" export/mm6_natm.glb export/mm6_natm.glb
rm -f export/mm6_natm_lods.geometry.glb
if [[ "${1:-}" == "--install" ]]; then
  for name in mm6_natm mm6_natm_spear mm6_natm_buckler; do
    python3 "$repo/tools/install_model.py" "export/$name.glb" --world mm6
  done
fi
ls -la export/mm6_natm.glb export/mm6_natm_spear.glb export/mm6_natm_buckler.glb
