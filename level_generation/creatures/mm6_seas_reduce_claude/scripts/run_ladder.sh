#!/usr/bin/env bash
# One ladder configuration on the already dumped mesh (work/mesh_in.npz): decimate, ladder, compare; results kept as
# work/ladder_<label>.blend and work/selection_<label>.json. Usage: [REA_PROTECT_* env] run_ladder.sh <label> <ratios>
set -euo pipefail
label=$1; R=$2; cd "$(dirname "$0")/.."
VENV="/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/da4542c9-2ca5-4473-bf19-87d753441380/scratchpad/im_venv/bin/python -I"
$VENV scripts/decimate_tex.py work $R > work/decimate_$label.log; cat work/decimate_$label.log
[ "${REA_WEIGHTS:-}" != component ] || python3 scripts/component_weights.py $R
REA_METHOD=texture REA_RATIOS=$R blender -b -P scripts/reduce_ladder.py > work/ladder_$label.log 2>&1
REA_HEIGHT_M=1.039 python3 scripts/compare_ladder.py > work/compare_$label.log
cp work/ladder.blend work/ladder_$label.blend; cp work/selection.json work/selection_$label.json
python3 - "$label" <<'PY'
import json, sys; d = json.load(open(f'work/selection_{sys.argv[1]}.json'))
for t, c in d['ladder'].items(): print(' ', t, c['tris'], 'p99', c['p99_mm'], 'max', c['max_mm'], c.get('worst_at'), 'IoU', c['iou_min'], 'SSIM', c['ssim_mean'], 'PASS' if c['pass'] else 'fail')
PY
