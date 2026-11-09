#!/usr/bin/env bash
# One ladder candidate -> LOD0-only GLB for close-ups: cand_glb.sh <ladder label> <ratio e.g. 60> -> work/<label>_r<ratio>_lod0.glb
set -euo pipefail
cd "$(dirname "$0")/.."; lab=$1; r=$2
cp work/ladder_$lab.blend work/ladder.blend
REA_CAND=Cand_$r REA_NODE=Triton blender -b -P scripts/export_cand.py 2>&1 | grep EXPORTED
python3 scripts/swap_lod0.py work/mm8_m576_source_pre_reduce.glb work/cand_export.glb work/${lab}_r${r}_lod0.glb Triton | tail -1
