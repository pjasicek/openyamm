#!/usr/bin/env bash
# One ladder configuration on the already dumped mesh (work/mesh_in.npz): decimate, ladder, compare; results kept as
# work/ladder_<label>.blend and work/selection_<label>.json. Blender runs through scripts/b.sh (creature wrapper,
# lease token in REA_TOKEN). Usage: [REA_* env] run_ladder.sh <label> <ratios>
set -euo pipefail
label=$1; R=$2; cd "$(dirname "$0")/.."
VENV="${REA_VENV:-/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/6ff9ed88-7a28-43ed-af0c-54fedb78da17/scratchpad/reduce_hydra/venv/bin/python} -I"
$VENV scripts/decimate_tex.py work $R > work/decimate_$label.log; cat work/decimate_$label.log
if [ "${REA_WEIGHTS:-}" = component ]; then python3 scripts/uv_weights.py $R; fi
REA_INFLUENCES=4 REA_METHOD=texture REA_RATIOS=$R scripts/b.sh reduce_ladder.py > work/ladder_$label.log 2>&1 || { cat work/ladder_$label.log; exit 1; }
REA_HEIGHT_M=${REA_HEIGHT_M:-2.0} python3 scripts/compare_ladder.py > work/compare_$label.log
cp work/ladder.blend work/ladder_$label.blend; cp work/selection.json work/selection_$label.json
cp review/ladder_sheet.png review/ladder_sheet_$label.png
python3 - "$label" <<'PY'
import json, sys; d = json.load(open(f'work/selection_{sys.argv[1]}.json'))
for t, c in d['ladder'].items(): print(' ', t, c['tris'], 'open', c['open_edges'], 'p99', c['p99_mm'], 'max', c['max_mm'], c.get('worst_at'), 'IoU', c['iou_min'], 'SSIM', c['ssim_mean'], 'PASS' if c['pass'] else 'fail')
PY
