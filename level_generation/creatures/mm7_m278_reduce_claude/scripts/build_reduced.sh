#!/usr/bin/env bash
# Reduced runtime GLB from the picked ladder step: export_cand -> swap_lod0 (onto the batch E export) -> LODs
# (protected extremes and Death floor contact) -> shadow LODs -> colour variants carried to every LOD/shadow primitive.
# Usage: [REA_FLAT=1] scripts/build_reduced.sh <out.glb>   (default smooth shading; REA_FLAT=1 = flat, as batch E)
set -euo pipefail
cd "$(dirname "$0")/.."; out=${1:-export/mm7_m278.glb}
cp work/ladder_c1.blend work/ladder.blend
REA_CAND=Cand_66 REA_NODE=M278 blender -b -P scripts/export_cand.py 2>&1 | grep EXPORTED
python3 scripts/swap_lod0.py work/mm7_m278_source_pre_reduce.glb work/cand_export.glb work/pick_lod0.glb M278
REA_LOD_RATIOS=0.5,0.25,0.1 REA_FLOOR_M=0.006 blender -b -P scripts/build_lods.py 2>&1 | grep -E "PROTECTED|LOD triangles"
python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb
cp work/pick_lods_shadowfix.glb "$out"; python3 scripts/carry_variants.py "$out"; ls -la "$out"
