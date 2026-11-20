#!/usr/bin/env bash
# Candidate of a kept ladder blend -> work/glb_<label>.glb (installed GLB with the candidate as LOD0, no LODs) for
# glb_close.py. Usage: quick_glb.sh <ladder label> <step, e.g. 66> <out label>
set -euo pipefail; cd "$(dirname "$0")/.."
cp work/ladder_$1.blend work/ladder.blend
REA_CAND=Cand_$2 REA_NODE=Minotaur blender -b -P scripts/export_cand.py > work/export_$3.log 2>&1
python3 scripts/swap_lod0.py work/mm8_m488_source_pre_reduce.glb work/cand_export.glb work/glb_$3.glb Minotaur | tail -1
