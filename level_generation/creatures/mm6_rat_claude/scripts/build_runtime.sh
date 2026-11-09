#!/usr/bin/env bash
# Rat runtime GLB: export -> prepare -> LODs -> shadow fix -> A/B/C skins -> (install).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
blender=/snap/bin/blender
"$blender" --background "$here/work/anim_v1.blend" --python "$here/scripts/export_glb.py" 2>&1 | grep EXPORTED
python3 "$repo/tools/prepare_actor_glb.py" "$here/export/mm6_rat_lod0.glb" "$here/export/mm6_rat_runtime_lod0.glb"
"$blender" --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_rat_runtime_lod0.glb" \
  "$here/export/mm6_rat_lods.glb" --mesh-node Rat 2>&1 | grep "LOD triangles"
python3 "$here/scripts/shrink_shadow_lods.py" "$here/export/mm6_rat_lods.glb" "$here/export/mm6_rat_lods_shadowfix.glb"
# Tiers: one shared skin + region mask + ramps fitted from compose_rat.py's region weights and graded A/B/C.
python3 "$here/../claude_shared/fit_tier_regions.py" "$here/textures" rat Rat_A Rat
python3 "$here/../claude_shared/region_variants.py" "$here/export/mm6_rat_lods_shadowfix.glb" \
  "$here/export/mm6_rat.glb" "$here/textures/rat_ramps.json" --extra Rat openyamm_specular=0 --extra Rat pbr.metallicFactor=0
rm -f "$here/export/mm6_rat_lods.geometry.glb"
if [[ "${1:-}" == "--install" ]]; then
  install -m 0664 "$here/export/mm6_rat.glb" "$repo/assets_dev/worlds/mm6/models/mm6_rat.glb"
  echo "installed $repo/assets_dev/worlds/mm6/models/mm6_rat.glb"
fi
