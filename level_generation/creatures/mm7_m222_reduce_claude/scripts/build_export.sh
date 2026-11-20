#!/usr/bin/env bash
# Reduced Chain Fighter runtime GLB from the picked ladder candidate: export_cand.py -> swap_lod0.py (into the rollback
# source: materials, variants, region ramps, sockets and clips unchanged) -> build_lods.py -> shrink_shadow_lods.py
# (as the source export) -> carry_variants.py -> export/mm7_m222.glb. The scimitar attachment is copied unchanged.
# Usage: TOKEN=<lease> scripts/build_export.sh [ladder label] [Cand_NN]
set -euo pipefail
cd "$(dirname "$0")/.."; label=${1:-j}; cand=${2:-Cand_83}
cp work/ladder_$label.blend work/ladder.blend
REA_CAND=$cand REA_NODE=M222 scripts/blend.sh export_cand.py | grep -E "EXPORTED|Error"
python3 scripts/swap_lod0.py work/mm7_m222_source_pre_reduce.glb work/cand_export.glb work/pick_lod0.glb M222
scripts/blend.sh build_lods.py | grep -E "PROTECTED|RATIOS|LOD tri|Error"
python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb | tail -2
cp work/pick_lods_shadowfix.glb export/mm7_m222.glb
python3 scripts/carry_variants.py export/mm7_m222.glb
cp work/mm7_m222_sword_source_pre_reduce.glb export/mm7_m222_sword.glb
ls -la export/
