#!/usr/bin/env bash
# mpqem.py alone (no Blender): [SETS=a MP_GROUPS=...] mp_only.sh <label> <ratios> -> work/mp_<label>.log, work/mp_<label>_r<NN>.npz
set -euo pipefail
label=$1; R=$2; cd "$(dirname "$0")/.."
export MP_CHART=${MP_CHART:-1} MP_AUDIT=${MP_AUDIT:-1} MP_W5=${MP_W5:-4} MP_TEX_MAX=${MP_TEX_MAX:-100} MP_TEX_MEAN=${MP_TEX_MEAN:-45}
scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore scripts/mpqem.py before/mm9_skraelos.glb $R > work/mp_$label.log 2>&1
for r in ${R//,/ }; do t=$(python3 -c "print(int(round($r*100)))"); cp work/mp_r$t.npz work/mp_${label}_r$t.npz; cp work/mesh_r$t.npz work/mesh_${label}_r$t.npz; done
grep -v "^POSES\|OFFSET\|Unexpected" work/mp_$label.log
