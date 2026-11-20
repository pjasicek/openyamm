#!/usr/bin/env bash
# One ladder over scaled region budgets: each region's cut (1 - ratio) is scaled by m for every m in <scales>; the
# free label 0 takes the same scaled cut. Usage: group_ladder.sh <label> <keep.npy> "<g:ratio,...>" <scales>
set -euo pipefail
label=$1; keep=$2; base=$3; scales=$4; cd "$(dirname "$0")/.."
VENV="/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/da4542c9-2ca5-4473-bf19-87d753441380/scratchpad/im_venv/bin/python -I"
rs=(); i=0
for m in ${scales//,/ }; do
  read gr r < <(python3 - "$base" "$m" "$keep" <<'PY'
import sys, numpy as np
base, m, keep = sys.argv[1], float(sys.argv[2]), np.load(sys.argv[3]); g = np.load('work/groups.npy')
gr = {int(k): 1 - (1 - float(v)) * m for k, v in (kv.split(':') for kv in base.split(','))}
free0 = int(((g == 0) & ~keep).sum()); total = keep.sum() + sum(int(((g == k) & ~keep).sum() * v) for k, v in gr.items())
total += int(free0 * (1 - .2 * m))
print(','.join(f'{k}:{v:.3f}' for k, v in gr.items()), f'{total / len(g):.4f}')
PY
)
  echo "scale $m -> overall $r groups $gr"
  REA_KEEP_FACES=$keep REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=$gr $VENV scripts/decimate_tex.py work $r | tail -1
  rs+=($r)
done
R=$(IFS=,; echo "${rs[*]}")
for t in 1 2 3; do REA_INFLUENCES=8 REA_METHOD=texture REA_RATIOS=$R blender -b -P scripts/reduce_ladder.py > work/ladder_$label.log 2>&1 && break; echo "blender retry $t"; done
REA_HEIGHT_M=1.401 python3 scripts/compare_ladder.py > work/compare_$label.log
cp work/ladder.blend work/ladder_$label.blend; cp work/selection.json work/selection_$label.json
python3 - "$label" <<'PY'
import json, sys; d = json.load(open(f'work/selection_{sys.argv[1]}.json'))
for t, c in d['ladder'].items(): print(' ', t, c['tris'], 'p99', c['p99_mm'], 'max', c['max_mm'], c.get('worst_at'), 'IoU', c['iou_min'], 'SSIM', c['ssim_mean'], 'PASS' if c['pass'] else 'fail')
PY
