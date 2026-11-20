#!/usr/bin/env bash
# Head-intersection gate of one ladder candidate without the LOD build: export_cand -> swap_lod0 -> check_heads_glb
# on the swapped LOD0 (work/gate_<cand>.glb). Usage: scripts/gate_cand.sh <ladder label> <Cand_NN> [frame step]
set -euo pipefail
cd "$(dirname "$0")/.."
cp work/ladder_$1.blend work/ladder.blend
REA_CAND=$2 REA_NODE=M266 scripts/b.sh export_cand.py > /dev/null
python3 scripts/swap_lod0.py work/mm7_m266_source_pre_reduce.glb work/cand_export.glb work/gate_$1_$2.glb M266 > /dev/null
REA_GREP="^GATE" scripts/b.sh check_heads_glb.py "$PWD/work/gate_$1_$2.glb" ${3:-1}
