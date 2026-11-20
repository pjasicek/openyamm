#!/usr/bin/env bash
# Rerun the ladder with the current REA_* environment (decimate -> ladder -> compare). Usage: run_ladder.sh <ratios>
set -euo pipefail; cd "$(dirname "$0")/.."
VENV="/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/da4542c9-2ca5-4473-bf19-87d753441380/scratchpad/im_venv/bin/python -I"
rm -f work/mesh_r*.npz
$VENV scripts/decimate_tex.py work $1 > work/decimate.log; grep DECIMATED work/decimate.log
REA_METHOD=texture REA_RATIOS=$1 blender -b -P scripts/reduce_ladder.py > work/ladder.log 2>&1
REA_HEIGHT_M=${REA_HEIGHT_M:-1.0} python3 scripts/compare_ladder.py > work/compare.log
python3 -c "
import json;d=json.load(open('work/selection.json'));print('picked',d['picked'])
for t,c in d['ladder'].items(): print(' ',t,c['tris'],'p99',c['p99_mm'],'max',c['max_mm'],'worst',c['worst_at'],'IoU',c['iou_min'],'SSIM',c['ssim_mean'],'PASS' if c['pass'] else 'fail')"
