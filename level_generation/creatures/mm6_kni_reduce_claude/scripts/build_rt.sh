#!/usr/bin/env bash
# Retextured knight runtime GLB from work/uv.blend and textures/ (compose.py): geometry export -> swap into the
# installed GLB (clips, skin, nodes kept; helmet primitive added) -> maps -> tier materials (region ramps) -> LODs ->
# variant mappings on every primitive -> unused materials/images dropped -> viewer GLBs. Usage: build_rt.sh <tag>
set -euo pipefail
tag=$1; P="$(cd "$(dirname "$0")/.." && pwd)"; ROOT="$(cd "$P/../../.." && pwd)"; cd "$P"
blender -b -P scripts/export_geom.py > work/log_export_geom.txt 2>&1; grep EXPORTED work/log_export_geom.txt
python3 scripts/swap_multi.py work/mm6_kni_source_pre_reduce.glb work/geom_export.glb work/rt_swap.glb KnightPlate
python3 scripts/apply_textures.py work/rt_swap.glb work/rt_maps.glb textures/maps.json | cut -c1-60
python3 ../claude_shared/region_variants.py work/rt_maps.glb work/rt_var.glb textures/kni_ramps.json \
  --extra KnightPlate openyamm_specular=1 --extra KnightHelm openyamm_specular=1 \
  --extra KnightPlate openyamm_specular_mask=true --extra KnightHelm openyamm_specular_mask=true \
  --extra KnightPlate pbr.metallicFactor=0 --extra KnightHelm pbr.metallicFactor=0 | tail -2
blender -b -P "$ROOT/tools/build_actor_lods.py" -- work/rt_var.glb export/mm6_kni_$tag.glb --mesh-node KnightPlate 2>&1 | grep "LOD tri"
python3 scripts/carry_variants.py export/mm6_kni_$tag.glb
python3 scripts/prune_materials.py export/mm6_kni_$tag.glb | cut -c1-200
python3 scripts/viewer_variants.py export/mm6_kni_$tag.glb $tag > /dev/null
