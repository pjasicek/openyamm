#!/usr/bin/env bash
# One ladder configuration on the dumped mesh (work/mesh_in.npz): decimate, ladder, compare; results kept as
# work/ladder_<label>.blend and work/selection_<label>.json. Usage: [REA_* env] run_ladder.sh <label> <ratios>
set -euo pipefail
label=$1; R=$2; cd "$(dirname "$0")/.."
../claude_shared/meshlab_venv/bin/python -I scripts/decimate_tex.py work $R 2>&1 | grep -v Warn > work/decimate_$label.log; cat work/decimate_$label.log
tags=$(python3 -c "print(','.join('r%d' % int(float(r) * 100) for r in '$R'.split(',')))")
[ -n "${REA_DROP_FACES:-}" ] && ../claude_shared/meshlab_venv/bin/python -I scripts/hair_backs_regen.py $tags 2>&1 | grep -v Warn
../claude_shared/meshlab_venv/bin/python -I scripts/interp_weights.py $tags 2>&1 | grep -v Warn
REA_WEIGHTS=${REA_WEIGHTS:-interp} REA_INFLUENCES=4 REA_METHOD=texture REA_RATIOS=$R scripts/bl.sh scripts/reduce_ladder.py > work/ladder_$label.log 2>&1
REA_HEIGHT_M=${REA_HEIGHT_M:-1.92} python3 scripts/compare_ladder.py > work/compare_$label.log
cp work/ladder.blend work/ladder_$label.blend; cp work/selection.json work/selection_$label.json; cp work/ladder.json work/ladder_$label.json
cp review/ladder_sheet.png review/ladder_sheet_$label.png
python3 - "$label" <<'PY'
import json, sys; d = json.load(open(f'work/selection_{sys.argv[1]}.json'))
print('source', d['source_tris'], 'limits', d['thresholds_mm'], 'picked', d['picked'])
for t, c in d['ladder'].items(): print(' ', t, c['tris'], 'open', c['open_edges'], 'p99', c['p99_mm'], 'max', c['max_mm'], c.get('worst_at'), 'IoU', c['iou_min'], 'SSIM', c['ssim_mean'], 'PASS' if c['pass'] else 'fail')
PY
