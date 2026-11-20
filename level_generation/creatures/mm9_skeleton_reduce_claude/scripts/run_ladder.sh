#!/usr/bin/env bash
# One ladder configuration on the dumped mesh (work/mesh_in.npz) and plan (work/groups.npy, work/group_plan.json):
# per-piece decimation (decimate_pieces.py), Blender ladder (piece weights, exact source weights), compare.
# Results kept as work/ladder_<label>.blend and work/selection_<label>.json.
# Usage: run_ladder.sh <label> <tag,...>  (plans work/plan_<tag>.json; the ladder's ratio is tag / 100)
set -euo pipefail
label=$1; T=$2; R=$(python3 -c "import sys; print(','.join(str(int(t) / 100) for t in sys.argv[1].split(',')))" $T); P=$(python3 -c "import sys; print(','.join(f'{t}=work/plan_{t}.json' for t in sys.argv[1].split(',')))" $T); cd "$(dirname "$0")/.."
VENV="scripts/cap.sh /home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/meshlab_venv/bin/python -I"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
$VENV scripts/decimate_pieces.py work $P > work/decimate_$label.log; grep -E "DECIMATED|inflation" work/decimate_$label.log
REA_INFLUENCES=4 REA_METHOD=texture REA_RATIOS=$R $BL -P scripts/reduce_ladder.py > work/ladder_$label.log 2>&1
REA_HEIGHT_M=${REA_HEIGHT_M:-1.729} scripts/cap.sh python3 scripts/compare_ladder.py > work/compare_$label.log
cp work/ladder.blend work/ladder_$label.blend; cp work/selection.json work/selection_$label.json
cp review/ladder_sheet.png review/ladder_sheet_$label.png
python3 - "$label" <<'PY'
import json, sys; d = json.load(open(f'work/selection_{sys.argv[1]}.json'))
for t, c in d['ladder'].items(): print(' ', t, c['tris'], 'p99', c['p99_mm'], 'max', c['max_mm'], c.get('worst_at'), 'IoU', c['iou_min'], 'SSIM', c['ssim_mean'], 'PASS' if c['pass'] else 'fail')
PY
