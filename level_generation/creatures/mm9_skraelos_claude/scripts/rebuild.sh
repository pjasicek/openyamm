#!/usr/bin/env bash
# Everything after the paid UV layout (work/uv.npz, never re-laid): grip and held props -> skull copies -> clean-up -> reduction -> linings ->
# paint fixes and grade -> rig, weights, clips -> runtime GLB -> viewer. Project folder: scripts/rebuild.sh <viewer revision> [--install]
# (geometry before the UVs: step1_clean.py, skull_prep.py, assemble_sk.py -> work/asm1.npz, rig on it, staff_place.py -> work/asm2.npz, uv_sk.py)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages; BL="$here/scripts/bl.sh"; P=level_generation/creatures/mm9_skraelos_claude
STAFF_OUT=${STAFF_OUT:-0} STAFF_DIST=${STAFF_DIST:-0.02} SKULL_MODE=hold SKULL_GAP=0.03 SKULL_ALONG=0.13 CONTACT=0.003 $G -W ignore scripts/grip_sk.py work/asm2.npz work/rig_asm2.json source/mm9/skraelos.glb work/clips_asm1.glb work/skull.npz work/asm3.npz 2>&1 | grep -E "GRIP|HOLD|STAFF|SKULL"
$G -W ignore - <<'PY'
import numpy as np
A = np.load('work/asm3.npz'); U = dict(np.load('work/uv_tex.npz')); U['co'] = A['co'][U['orig']]; np.savez('work/uv_g.npz', **U)
PY
(cd "$repo" && "$BL" scripts/copies_sk.py $P/work/asm3.npz $P/work/uv_g.npz $P/work/asm4.npz $P/work/uv4.npz | grep -E "COPY|SAVED|rc=")
python3 scripts/drop_degenerate.py work/uv4.npz work/uv5.npz
python3 scripts/orient_parts.py work/asm4.npz work/asm5.npz; python3 scripts/orient_parts.py work/uv5.npz work/uv6.npz
python3 scripts/orient_comps.py work/asm5.npz work/asm5.npz necklace; python3 scripts/orient_comps.py work/uv6.npz work/uv6.npz necklace
(cd "$repo" && "$BL" scripts/reduce_parts.py $P/work/uv6.npz $P/work/uv7.npz hands=2300 heldskull=750 pendant=180 | grep -E "REDUCE|SAVED|rc=")
python3 scripts/drop_degenerate.py work/uv7.npz work/uv7.npz
# no linings: the cloth material is doubleSided (double_body.py in build_runtime_sk.sh); work/uv_ln.npz = the reduced mesh
cp work/uv7.npz work/uv_ln.npz
$G -W ignore scripts/paint_fix_sk.py textures/sk_body_raw.png textures/sk_head_raw.png 2>&1 | grep -E "FIX|COLLAR|TABARD"
$G -W ignore scripts/finish_sk.py work/uv_ln.npz 2>&1 | grep FINISH | cut -c1-30
ASM=work/asm5.npz scripts/rig_sk.sh work/uv_ln_tex.npz 2>&1 | grep -E "GLB|WEIGHTS|CLIPS" | cut -c1-120
scripts/build_runtime_sk.sh ${2:-} 2>&1 | grep -E "LOD tri|WINDING|corpse|installed|Error" || true
scripts/viewer_update.sh "$1" | tail -1
