#!/usr/bin/env bash
# Reduced m226 runtime body GLB from the picked candidate in work/ladder.blend (+ its work/mesh_rNN.npz):
# kept_normals.py (source normals on unchanged faces) -> export_cand.py -> swap_lod0.py (into the rollback source:
# materials, variants, region ramps, clips and the Sword socket unchanged) -> build_lods.py -> shrink_shadow_lods.py
# (as the source project) -> carry_variants.py -> export/mm7_m226.glb. Usage: TOKEN=<lease> scripts/build_export.sh Cand_76 r76
set -euo pipefail
cd "$(dirname "$0")/.."
cand=${1:-Cand_76}; tag=${2:-r76}
scripts/bl.sh scripts/kept_normals.py -- $cand work/mesh_$tag.npz work/mm7_m226_source_pre_reduce.glb M226 2>&1 | grep -E "KEPTNORMALS|Error|Traceback" || true
REA_CAND=$cand REA_NODE=M226 scripts/bl.sh scripts/export_cand.py 2>&1 | grep -E "EXPORTED|Error|Traceback"
python3 scripts/swap_lod0.py work/mm7_m226_source_pre_reduce.glb work/cand_export.glb work/pick_lod0.glb M226
scripts/bl.sh scripts/build_lods.py 2>&1 | grep -E "PROTECTED|RATIOS|LOD tri|Error|Traceback"
python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb > /dev/null
cp work/pick_lods_shadowfix.glb export/mm7_m226.glb
python3 scripts/carry_variants.py export/mm7_m226.glb
ls -la export/mm7_m226.glb
