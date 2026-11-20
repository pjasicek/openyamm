#!/usr/bin/env bash
# One ladder configuration on work/mesh_in.npz (copied from mm8_m492_reduce_claude/scripts/run_ladder.sh): decimate
# with the m182 keep/groups (scripts/m182_regions.py), ladder over every clip, compare; results kept as
# work/ladder_<label>.blend and work/selection_<label>.json. Usage: run_ladder.sh <label> <ratios> [group ratios]
set -euo pipefail
label=$1; R=$2; G=${3:-1:0.7,2:0.7}; cd "$(dirname "$0")/.."
VENV="${REA_VENV:-/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/22c4fb2e-4378-42a4-b0c9-4c4891dcee85/scratchpad/im_venv/bin/python} -I"
REA_KEEP_FACES=${KEEP:-work/keep.npy} REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=$G $VENV scripts/decimate_tex.py work $R > work/decimate_$label.log; cat work/decimate_$label.log
REA_INFLUENCES=4 REA_METHOD=texture REA_RATIOS=$R blender -b --factory-startup -P scripts/reduce_ladder.py > work/ladder_$label.log 2>&1
REA_HEIGHT_M=${REA_HEIGHT_M:-1.5} python3 scripts/compare_ladder.py > work/compare_$label.log
cp work/ladder.blend work/ladder_$label.blend; cp work/selection.json work/selection_$label.json; cp review/ladder_sheet.png review/ladder_sheet_$label.png
python3 - "$label" <<'PY'
import json, sys; d = json.load(open(f'work/selection_{sys.argv[1]}.json'))
for t, c in d['ladder'].items(): print(' ', t, c['tris'], 'open', c['open_edges'], 'p99', c['p99_mm'], 'max', c['max_mm'], c.get('worst_at'), 'IoU', c['iou_min'], 'SSIM', c['ssim_mean'], 'PASS' if c['pass'] else 'fail')
PY
