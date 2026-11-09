#!/usr/bin/env bash
# Body-only retexture of the new cut as it is (compose.py with HELMET=0): the cut's LOD0 GLB (clips, skin, original
# UVs) -> maps -> tier materials (region ramps) -> LODs -> variant mappings -> unused materials/images dropped -> viewer
# GLBs. Usage: build_orig.sh <tag> [lod0 glb, default export/mm6_kni_u7r65_lod0.glb]
set -euo pipefail
tag=$1; P="$(cd "$(dirname "$0")/.." && pwd)"; ROOT="$(cd "$P/../../.." && pwd)"; cd "$P"
src=${2:-export/mm6_kni_u7r65_lod0.glb}
python3 scripts/apply_textures.py "$src" work/ro_maps.glb textures/maps.json | cut -c1-60
python3 ../claude_shared/region_variants.py work/ro_maps.glb work/ro_var.glb textures/kni_ramps.json \
  --extra KnightPlate openyamm_specular=1 --extra KnightPlate openyamm_specular_mask=true \
  --extra KnightPlate pbr.metallicFactor=0 | tail -2
blender -b -P "$ROOT/tools/build_actor_lods.py" -- work/ro_var.glb export/mm6_kni_$tag.glb --mesh-node KnightPlate 2>&1 | grep "LOD tri"
python3 scripts/carry_variants.py export/mm6_kni_$tag.glb
python3 scripts/prune_materials.py export/mm6_kni_$tag.glb | cut -c1-200
python3 scripts/viewer_variants.py export/mm6_kni_$tag.glb $tag > /dev/null
