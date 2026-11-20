#!/usr/bin/env bash
# Ladder candidate -> textured GLB with the installed materials/clips (LOD0 only) for glb_close.py.
# Usage: cand_glb.sh <ladder label> <Cand_NN> -> work/glb_<label>_<NN>.glb
set -euo pipefail
cd "$(dirname "$0")/.."; label=$1; cand=$2
cp work/ladder_$label.blend work/ladder.blend
REA_CAND=$cand REA_NODE=M432 blender -b -P scripts/export_cand.py 2>&1 | grep EXPORTED
python3 scripts/swap_lod0.py work/mm8_m432_source_pre_reduce.glb work/cand_export.glb work/glb_${label}_${cand#Cand_}.glb M432 | tail -1
