#!/usr/bin/env bash
# Retextured 55 % goblin, after the two Meshy downloads: UV parity, rasters, compose, export, assemble into the
# installed GLB, prepare, LODs, variants to LOD/shadow meshes, shadow tuck, head merged into the body atlas,
# viewer variants. -> export/mm6_gob2.glb (not installed).
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"; ROOT="$(cd "$P/../../.." && pwd)"; cd "$P"
t(){ local s=$(date +%s); "$@" > "work/log_$(basename "${@: -1}" | tr -c 'a-zA-Z0-9_.\n' _).txt" 2>&1 || { echo "FAILED $*"; tail -20 "work/log_$(basename "${@: -1}" | tr -c 'a-zA-Z0-9_.\n' _).txt"; exit 1; }; echo "$(basename "$2" 2>/dev/null) $(( $(date +%s) - s ))s"; }
blender -b --python-exit-code 1 -P scripts/uv_parity.py > work/log_parity.txt 2>&1 || { tail work/log_parity.txt; exit 1; }; grep PARITY work/log_parity.txt
blender -b --python-exit-code 1 -P scripts/raster_gob.py -- 1024 > work/log_raster.txt 2>&1 || { tail work/log_raster.txt; exit 1; }; grep RASTER work/log_raster.txt
python3 scripts/compose_gob.py | grep -E "CLASSES|HEAD|GRADE|DETAIL|SKIN"
blender -b --python-exit-code 1 -P scripts/export_master.py 2>&1 | grep EXPORTED
python3 scripts/assemble_gob.py "$ROOT/assets_source/worlds/mm6/models/mm6_gob2.glb" work/master_export.glb export/mm6_gob2_assembled.glb
python3 "$ROOT/tools/prepare_actor_glb.py" export/mm6_gob2_assembled.glb export/mm6_gob2_runtime_lod0.glb
blender -b --factory-startup --python-exit-code 1 --python "$ROOT/tools/build_actor_lods.py" -- \
  export/mm6_gob2_runtime_lod0.glb export/mm6_gob2_lods.glb --mesh-node Goblin 2>&1 | grep "LOD triangles"
python3 scripts/carry_variants.py export/mm6_gob2_lods.glb
python3 ../mm6_gob2_claude/scripts/shrink_shadow_lods.py export/mm6_gob2_lods.glb export/mm6_gob2_shadowfix.glb | tail -1
python3 scripts/clamp_lod_uvs.py export/mm6_gob2_shadowfix.glb
python3 "$ROOT/tools/merge_head_material.py" export/mm6_gob2_shadowfix.glb export/mm6_gob2.glb | tail -2
python3 scripts/viewer_variants.py export/mm6_gob2.glb r55t > /dev/null && echo "viewer variants r55t"
