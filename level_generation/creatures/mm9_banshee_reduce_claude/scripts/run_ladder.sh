#!/usr/bin/env bash
# One ladder configuration on the dumped mesh (work/mesh_in.npz): decimate, ladder, compare; results kept as
# work/ladder_<label>.blend and work/selection_<label>.json. Usage: [REA_* env] run_ladder.sh <label> <ratios>
set -euo pipefail
label=$1; R=$2; cd "$(dirname "$0")/.."
VENV="scripts/cap.sh /home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/meshlab_venv/bin/python -I"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
$VENV scripts/decimate_tex.py work $R > work/decimate_$label.log; cat work/decimate_$label.log
REA_INFLUENCES=4 REA_METHOD=texture REA_RATIOS=$R $BL -P scripts/reduce_ladder.py > work/ladder_$label.log 2>&1
REA_HEIGHT_M=${REA_HEIGHT_M:-1.843} scripts/cap.sh python3 scripts/compare_ladder.py > work/compare_$label.log
cp work/ladder.blend work/ladder_$label.blend; cp work/selection.json work/selection_$label.json
mkdir -p review/ladder_$label; cp review/ladder_sheet.png review/ladder_sheet_$label.png
python3 - "$label" <<'PY'
import json, sys; d = json.load(open(f'work/selection_{sys.argv[1]}.json'))
for t, c in d['ladder'].items(): print(' ', t, c['tris'], 'open', c['open_edges'], 'p99', c['p99_mm'], 'max', c['max_mm'], c.get('worst_at'), 'IoU', c['iou_min'], 'SSIM', c['ssim_mean'], 'PASS' if c['pass'] else 'fail')
PY
