#!/usr/bin/env bash
# Ladder candidate -> textured GLB with the source materials/variants/clips (LOD0 only) for glb_close.py.
# Usage: TOKEN=<lease> cand_glb.sh <ladder label> <Cand_NN> -> work/glb_<label>_<NN>.glb
set -euo pipefail
cd "$(dirname "$0")/.."; label=$1; cand=$2
cp work/ladder_$label.blend work/ladder.blend
REA_CAND=$cand REA_NODE=M222 scripts/blend.sh export_cand.py | grep -E "EXPORTED|Error"
python3 scripts/swap_lod0.py work/mm7_m222_source_pre_reduce.glb work/cand_export.glb work/glb_${label}_${cand#Cand_}.glb M222 | tail -1
