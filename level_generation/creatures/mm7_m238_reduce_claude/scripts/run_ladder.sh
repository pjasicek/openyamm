#!/usr/bin/env bash
# One ladder configuration on the already dumped mesh (work/mesh_in.npz): decimate (MeshLab venv), UV weights, ladder
# (Blender through b.sh, memory-capped), compare; results kept as work/ladder_<label>.blend and work/selection_<label>.json.
# Usage: TOKEN=<lease> [REA_* env] run_ladder.sh <label> <ratios>
set -euo pipefail
label=$1; R=$2; cd "$(dirname "$0")/.."
VENV="/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/31d543c7-aae8-4f96-a0fb-ccb802dd87be/scratchpad/im_venv/bin/python -I"
export CAP=${CAP:-8G}
scripts/cap.sh $VENV scripts/decimate_tex.py work $R > work/decimate_$label.log; cat work/decimate_$label.log
if [ "${REA_WEIGHTS:-}" = component ]; then scripts/cap.sh python3 scripts/uv_weights.py $R; fi
REA_INFLUENCES=4 REA_METHOD=texture REA_RATIOS=$R PAT='^LADDER|^DONE' scripts/b.sh reduce_ladder.py > work/ladder_$label.log 2>&1 || { tail -20 work/ladder_$label.log; exit 1; }
REA_HEIGHT_M=${REA_HEIGHT_M:-1.79} scripts/cap.sh python3 scripts/compare_ladder.py > work/compare_$label.log
cp work/ladder.blend work/ladder_$label.blend; cp work/selection.json work/selection_$label.json
python3 - "$label" <<'PY'
import json, sys; d = json.load(open(f'work/selection_{sys.argv[1]}.json'))
for t, c in d['ladder'].items(): print(' ', t, c['tris'], 'p99', c['p99_mm'], 'max', c['max_mm'], c.get('worst_at'), 'IoU', c['iou_min'], 'SSIM', c['ssim_mean'], 'PASS' if c['pass'] else 'fail')
PY
