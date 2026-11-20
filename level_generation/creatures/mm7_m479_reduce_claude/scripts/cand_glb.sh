#!/usr/bin/env bash
# Ladder candidate -> textured GLB with the source materials, variants and clips (LOD0 only) for glb_close.py.
# REA_KEPT_NORMALS=1 first restores the source GLB's normals on unchanged faces and kept vertices (kept_normals.py).
# Usage: TOKEN=<lease> cand_glb.sh <ladder label> <Cand_NN> [out suffix] -> work/glb_<label>_<NN><suffix>.glb
set -euo pipefail
cd "$(dirname "$0")/.."; label=$1; cand=$2; suf=${3:-}; ROOT=$(cd ../../.. && pwd); NN=${cand#Cand_}
B() { local out; out=$("$ROOT/tools/run_creature_blender.sh" --token "$TOKEN" "level_generation/creatures/mm7_m479_reduce_claude/scripts/$@" 2>&1)
      local log; log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      grep -E "EXPORTED|KEPTNORMALS|Traceback|Error:" "$log" || true; }
cp work/ladder_$label.blend work/ladder.blend
# the npz of this ladder's decimation (mesh_rNN.npz is overwritten by later ladders: keep a copy per label)
npz=work/mesh_${label}_r$NN.npz; [ -f "$npz" ] || npz=work/mesh_r$NN.npz
[ "${REA_KEPT_NORMALS:-0}" = 1 ] && B kept_normals.py $cand "$PWD/$npz" "$PWD/work/mm7_m479_source_pre_reduce.glb" M479
REA_CAND=$cand REA_NODE=M479 B export_cand.py
python3 scripts/swap_lod0.py work/mm7_m479_source_pre_reduce.glb work/cand_export.glb work/glb_${label}_${NN}${suf}.glb M479 | tail -1
