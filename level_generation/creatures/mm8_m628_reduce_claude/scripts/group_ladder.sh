#!/usr/bin/env bash
# Per-region ladder (work/regions.npy: 1 skull/hood, 2 jaw, 3 spine/ribs/clavicles, 4 pelvis, 5 thighs, 6 calves,
# 7 feet, 8 arms; 0 rest): one step per head ratio, the body groups fixed by REA_BODY ("3:0.85,4:0.85,...").
# Usage: group_ladder.sh <label> <head ratio,...>   (REA_KEEP_FACES required; label 0 at 0.6)
set -euo pipefail
label=$1; cd "$(dirname "$0")/.."
VENV="/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/da4542c9-2ca5-4473-bf19-87d753441380/scratchpad/im_venv/bin/python -I"
BODY=${REA_BODY:-2:0.6,3:0.85,4:0.85,5:0.85,6:0.85,7:0.7,8:0.7}
R=""; : > work/decimate_$label.log
for h in ${2//,/ }; do
  r=$(python3 - "$h" "$BODY" <<'PY'
import sys, numpy as np
g = np.load('work/regions.npy'); k = np.load('work/keep_a.npy') if False else None
import os; k = np.load(os.environ['REA_KEEP_FACES'])
rat = {1: float(sys.argv[1]), **{int(a): float(b) for a, b in (x.split(':') for x in sys.argv[2].split(','))}}
tot = k.sum() + sum(int(((g == x) & ~k).sum() * q) for x, q in rat.items()) + int(((g == 0) & ~k).sum() * .6)
print(f'{tot / len(g):.4f}')
PY
)
  # ratio label = head ratio (mesh_r<NN>.npz keyed by it): decimate one step at a time and rename
  REA_GROUPS=work/regions.npy REA_GROUP_RATIOS="1:$h,$BODY" $VENV scripts/decimate_tex.py work $r >> work/decimate_$label.log
  hn=$(python3 -c "print(int(round($h*100)))"); rn=$(python3 -c "print(int($r*100))")
  [ "$rn" = "$hn" ] || mv work/mesh_r$rn.npz work/mesh_r$hn.npz
  R="$R,$h"
done
R=${R#,}; cat work/decimate_$label.log
REA_SHARP=work/sharp.npy REA_INFLUENCES=3 REA_METHOD=texture REA_RATIOS=$R blender -b -P scripts/reduce_ladder.py > work/ladder_$label.log 2>&1
REA_HEIGHT_M=1.772 python3 scripts/compare_ladder.py > work/compare_$label.log
cp work/ladder.blend work/ladder_$label.blend; cp work/selection.json work/selection_$label.json
python3 - "$label" <<'PY'
import json, sys; d = json.load(open(f'work/selection_{sys.argv[1]}.json'))
for t, c in d['ladder'].items(): print(' ', t, c['tris'], 'p99', c['p99_mm'], 'max', c['max_mm'], c.get('worst_at'), 'IoU', c['iou_min'], 'SSIM', c['ssim_mean'], 'PASS' if c['pass'] else 'fail')
PY
