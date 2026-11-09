#!/usr/bin/env bash
# Picked ladder step -> export/mm7_m286.glb (+ the reduced axe -> export/mm7_m286_axe.glb). TOKEN=<lease>.
# Body: cand_glb.sh <label> Cand_<NN> kn (kept normals) -> spike_points.py, floor_points.py -> build_lods.py ->
# ../shrink_shadow_lods.py -> carry_variants.py -> ../clamp_lod_uv.py -> check_winding.py.
# Axe: axe_dump.py -> axe_rings.py -> decimate_tex.py (blades) -> LOD1 from the pick -> axe_build.py -> check_winding.py.
# Usage: build_pick.sh <ladder label> <NN> <axe blade ratio in %>   (pick: j 80 40)
set -euo pipefail
cd "$(dirname "$0")/../.."; label=$1; NN=$2; AX=$3; ROOT=$(cd ../../.. && pwd)
PY="/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/e3647c91-e3a6-4261-8d10-ee038ee9090c/scratchpad/rd_venv/bin/python -I"
REA_KEPT_NORMALS=1 scripts/reduce/cand_glb.sh $label Cand_$NN kn
cp work/glb_${label}_${NN}kn.glb work/pick_lod0.glb
python3 scripts/reduce/spike_points.py ${label}_r$NN
REA_FLOOR_MM=45 REA_FLOOR_N=32 BL_GREP='FLOOR' scripts/reduce/bl.sh floor_points.py "$PWD/work/pick_lod0.glb"
BL_GREP='PROTECTED|LOD triangles' scripts/reduce/bl.sh build_lods.py "$PWD/work/pick_lod0.glb" "$PWD/work/pick_lods.glb"
python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_shadowfix.glb
python3 scripts/reduce/carry_variants.py work/pick_shadowfix.glb
python3 scripts/clamp_lod_uv.py work/pick_shadowfix.glb
cp work/pick_shadowfix.glb export/mm7_m286.glb
# axe
python3 scripts/reduce/axe_dump.py && python3 scripts/reduce/axe_rings.py
R=$(python3 -c "import numpy as np; h=np.load('work/axe_dec2/haft.npy'); n=len(h); k=int(h.sum()); print(f'{(k + (n - k) * $AX / 100) / n:.4f}')")
REA_KEEP_FACES=work/axe_dec2/haft.npy $PY scripts/reduce/decimate_tex.py work/axe_dec2 $R
T=$(python3 -c "print(int($R * 100))")
mkdir -p work/axe_lod1
python3 -c "import numpy as np; d=np.load('work/axe_dec2/mesh_r$T.npz'); np.savez('work/axe_lod1/mesh_in.npz', verts=d['verts'], faces=d['faces'], wuv=d['wuv'], protect=np.zeros(len(d['faces'])))"
$PY scripts/reduce/decimate_tex.py work/axe_lod1 0.5
AXE_DIR=work/axe_dec2 python3 scripts/reduce/axe_error.py $T
python3 scripts/reduce/axe_build.py export/mm7_m286_axe.glb work/axe_dec2:$T work/axe_lod1:50
for g in export/mm7_m286.glb export/mm7_m286_axe.glb; do
  python3 "$ROOT/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "$g" | tail -2
done
sha256sum export/mm7_m286.glb export/mm7_m286_axe.glb
