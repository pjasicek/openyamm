#!/usr/bin/env bash
# Candidate <Cand_NN> of work/ladder_<label>.blend -> work/glb_<label>_<NN>.glb (installed GLB with LOD0 swapped, old LODs
# dropped) for GLB-only review (glb_close.py). Usage: cand_glb.sh <label> <Cand_NN>
set -euo pipefail; cd "$(dirname "$0")/.."
n=${2#Cand_}
REA_LADDER=ladder_$1.blend REA_CAND=$2 REA_NODE=Cyclops REA_INFLUENCES=8 REA_OUT=cand_$1_$n.glb blender -b -P scripts/export_cand.py 2>&1 | grep EXPORTED
python3 scripts/swap_lod0.py work/mm8_m520_source_pre_reduce.glb work/cand_$1_$n.glb work/glb_$1_$n.glb Cyclops
rm work/cand_$1_$n.glb
