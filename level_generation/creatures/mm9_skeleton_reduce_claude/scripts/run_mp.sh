#!/usr/bin/env bash
# Fix-pass ladder: mp_plan.py per step (budgets given as TAG:MAX:MEAN, the chart-guarded per-piece sweep of mp_pieces.py, SFX
# selects it) -> reduce_ladder.py (every vertex a source vertex: exact weights; error over every clip, renders) -> compare.
# Usage: SFX=_c run_mp.sh <label> <tag:max:mean,...>
set -euo pipefail
label=$1; cd "$(dirname "$0")/.."
G="scripts/cap.sh ../claude_shared/gltf_venv/bin/python -I -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
R=""
for s in ${2//,/ }; do IFS=: read t mx mn <<< "$s"; $G scripts/mp_plan.py $t $mx $mn 2>&1 | grep -v prefix; cp work/mp_r$t.npz work/mp_${label}_r$t.npz; R="$R${R:+,}0.$t"; done
REA_INFLUENCES=4 REA_METHOD=texture REA_RATIOS=$R $BL -P scripts/reduce_ladder.py > work/ladder_$label.log 2>&1
REA_HEIGHT_M=${REA_HEIGHT_M:-1.729} scripts/cap.sh python3 scripts/compare_ladder.py > work/compare_$label.log
cp work/ladder.blend work/ladder_$label.blend; cp work/selection.json work/selection_$label.json
cp review/ladder_sheet.png review/ladder_sheet_$label.png
python3 - "$label" <<'PY'
import json, sys; d = json.load(open(f'work/selection_{sys.argv[1]}.json'))
for t, c in d['ladder'].items(): print(' ', t, c['tris'], 'p99', c['p99_mm'], 'max', c['max_mm'], c.get('worst_at'), 'IoU', c['iou_min'], 'PASS' if c['pass'] else 'fail')
PY
