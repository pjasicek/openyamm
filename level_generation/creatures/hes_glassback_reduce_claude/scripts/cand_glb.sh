#!/usr/bin/env bash
# One ladder candidate as a runtime-like LOD0 GLB (no LODs): export_cand.py -> swap_lod0.py into the rollback source.
# Usage: scripts/cand_glb.sh <ladder label> <Cand_NN> -> work/cand_<label>_<NN>.glb
set -euo pipefail
cd "$(dirname "$0")/.."
export CAP=${CAP:-8G}
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
cp work/ladder_$1.blend work/ladder.blend
REA_CAND=$2 REA_NODE=Glassback $BL -P scripts/export_cand.py 2>&1 | grep -E "FLOOR|EXPORTED|Error"
python3 scripts/swap_lod0.py work/hes_glassback_source_pre_reduce.glb work/cand_export.glb work/cand_$1_${2#Cand_}.glb Glassback
