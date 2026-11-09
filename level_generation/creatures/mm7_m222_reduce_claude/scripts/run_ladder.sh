#!/usr/bin/env bash
# One ladder configuration on the already dumped mesh (work/mesh_in.npz): decimate, ladder, compare; results kept as
# work/ladder_<label>.blend, work/selection_<label>.json, review/ladder_sheet_<label>.png.
# Usage: TOKEN=<lease> [REA_KEEP_FACES/REA_GROUPS/REA_GROUP_RATIOS env] run_ladder.sh <label> <ratios>
set -euo pipefail
label=$1; R=$2; cd "$(dirname "$0")/.."
VENV="/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/22c4fb2e-4378-42a4-b0c9-4c4891dcee85/scratchpad/im_venv/bin/python -I"
$VENV scripts/decimate_tex.py work $R > work/decimate_$label.log; cat work/decimate_$label.log
REA_INFLUENCES=4 REA_METHOD=texture REA_RATIOS=$R scripts/blend.sh reduce_ladder.py > work/ladder_$label.log 2>&1 || { tail -30 work/ladder_$label.log; exit 1; }
REA_HEIGHT_M=${REA_HEIGHT_M:-1.706} python3 scripts/compare_ladder.py > work/compare_$label.log
cp work/ladder.blend work/ladder_$label.blend; cp work/selection.json work/selection_$label.json
cp review/ladder_sheet.png review/ladder_sheet_$label.png
for r in ${R//,/ }; do cp work/mesh_r$(python3 -c "print(int($r*100))").npz work/mesh_${label}_r$(python3 -c "print(int($r*100))").npz; done
python3 - "$label" <<'PY'
import json, sys; d = json.load(open(f'work/selection_{sys.argv[1]}.json'))
print('limits', d['thresholds_mm'])
for t, c in d['ladder'].items(): print(' ', t, c['tris'], 'p99', c['p99_mm'], 'max', c['max_mm'], c.get('worst_at'), 'IoU', c['iou_min'], 'SSIM', c['ssim_mean'], 'PASS' if c['pass'] else 'fail')
PY
