#!/usr/bin/env bash
# Cockatrice runtime GLB: export -> prepare -> LODs -> shadow fix -> A/B/C skins -> (install).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
blender=/snap/bin/blender
# Head texture set (1K, shared by all tiers) and the 1K body base colour.
python3 "$here/../claude_shared/compose_head_set.py" "$here" ckt work/anim_v1.blend Cockatrice \
  "$here/textures/ckt_a_basecolor_graded.png" --seam-gain 1.0 > /dev/null  # seam hidden by the ruff; see README
python3 -c "from PIL import Image; Image.open('$here/textures/ckt_a_basecolor_graded.png').resize((1024, 1024), Image.LANCZOS).save('$here/textures/ckt_a_basecolor_graded_1k.png', optimize=True)"
"$blender" --background "$here/work/anim_v1.blend" --python "$here/scripts/export_glb.py" 2>&1 | grep EXPORTED
python3 "$repo/tools/prepare_actor_glb.py" "$here/export/mm6_ckt_lod0.glb" "$here/export/mm6_ckt_runtime_lod0.glb"
"$blender" --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm6_ckt_runtime_lod0.glb" \
  "$here/export/mm6_ckt_lods.glb" --mesh-node Cockatrice 2>&1 | grep "LOD triangles"
python3 "$here/scripts/shrink_shadow_lods.py" "$here/export/mm6_ckt_lods.glb" "$here/export/mm6_ckt_lods_shadowfix.glb"
# Tiers: one shared skin + membrane region mask (compose_ckt.py) + palette-transfer ramps (tier_ramps.py).
python3 "$here/scripts/tier_ramps.py" > /dev/null
python3 "$here/../claude_shared/region_variants.py" "$here/export/mm6_ckt_lods_shadowfix.glb" \
  "$here/export/mm6_ckt.glb" "$here/textures/ckt_ramps.json" \
  --extra Cockatrice openyamm_specular=0 --extra Cockatrice pbr.metallicFactor=0
rm -f "$here/export/mm6_ckt_lods.geometry.glb"
if [[ "${1:-}" == "--install" ]]; then
  install -m 0664 "$here/export/mm6_ckt.glb" "$repo/assets_dev/worlds/mm6/models/mm6_ckt.glb"
  echo "installed $repo/assets_dev/worlds/mm6/models/mm6_ckt.glb"
fi
