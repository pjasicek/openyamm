#!/usr/bin/env bash
# Pose-aware ladder: mpqem.py (half-edge collapse scored over every clip) -> reduce_ladder.py (exact source weights,
# error over every clip, renders) -> compare_ladder.py. Usage: run_mp.sh <label> <ratios> [scales]
set -euo pipefail
label=$1; R=$2; SC=${3:-}; cd "$(dirname "$0")/.."
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
scripts/cap.sh python3 -W ignore scripts/mpqem.py ../mm9_banshee_claude/export/mm9_banshee_runtime_lod0.glb $R $SC > work/mp_$label.log; grep -v "^POSES\|OFFSET" work/mp_$label.log
REA_INFLUENCES=4 REA_METHOD=texture REA_RATIOS=$R $BL -P scripts/reduce_ladder.py > work/ladder_$label.log 2>&1
REA_HEIGHT_M=${REA_HEIGHT_M:-1.843} scripts/cap.sh python3 scripts/compare_ladder.py > work/compare_$label.log
cp work/ladder.blend work/ladder_$label.blend; cp work/selection.json work/selection_$label.json
cp review/ladder_sheet.png review/ladder_sheet_$label.png
python3 - "$label" <<'PY'
import json, sys; d = json.load(open(f'work/selection_{sys.argv[1]}.json'))
for t, c in d['ladder'].items(): print(' ', t, c['tris'], 'open', c['open_edges'], 'p99', c['p99_mm'], 'max', c['max_mm'], c.get('worst_at'), 'IoU', c['iou_min'], 'SSIM', c['ssim_mean'], 'PASS' if c['pass'] else 'fail')
PY
