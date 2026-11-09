#!/usr/bin/env bash
# One ladder configuration on the dumped mesh (work/mesh_in.npz): per-region groups at fixed ratios, the free faces
# (groups not listed: torso, arms, legs) at each of <free ratios>; decimate, ladder (all clips), compare.
# Results: work/ladder_<label>.blend, work/selection_<label>.json, review/ladder_sheet_<label>.png.
# Usage: TOKEN=<lease> run_ladder.sh <label> <set name> "<g:ratio,...>" <free ratio,...>
set -euo pipefail
label=$1; set=$2; gr=$3; fr=$4; cd "$(dirname "$0")/.."; P=$PWD; ROOT=$(cd ../../.. && pwd)
VENV="/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/1067a3a2-746f-4666-9e20-0b1a5a102eb9/scratchpad/rd_venv/bin/python -I"
R=$(python3 - "$set" "$gr" "$fr" <<'PY'
import sys, numpy as np
keep = np.load(f'work/keep_{sys.argv[1]}.npy'); g = np.load(f'work/groups_{sys.argv[1]}.npy')
gr = {int(k): float(x) for k, x in (kv.split(':') for kv in sys.argv[2].split(',') if kv)}
fixed = keep.sum() + sum(int(((g == k) & ~keep).sum() * q) for k, q in gr.items())
free = (~keep & ~np.isin(g, list(gr))).sum()
print(','.join(f'{(fixed + rb * free) / len(g):.4f}' for rb in map(float, sys.argv[3].split(','))))
PY
)
echo "overall ratios $R"
REA_KEEP_FACES=work/keep_$set.npy REA_GROUPS=work/groups_$set.npy REA_GROUP_RATIOS=$gr $VENV scripts/decimate_tex.py work $R > work/decimate_$label.log; cat work/decimate_$label.log
for r in ${R//,/ }; do t=$(python3 -c "print(int($r * 100))"); cp work/mesh_r$t.npz work/mesh_${label}_r$t.npz; done
for t in 1 2; do
  out=$(REA_INFLUENCES=4 REA_METHOD=texture REA_RATIOS=$R "$ROOT/tools/run_creature_blender.sh" --token "$TOKEN" "level_generation/creatures/mm7_m322_reduce_claude/scripts/reduce_ladder.py" 2>&1 || true)
  log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1); cp "$log" work/ladder_$label.log
  grep -q "^DONE" work/ladder_$label.log && break; echo "blender retry $t"; grep -A8 Traceback work/ladder_$label.log | tail -8
done
REA_HEIGHT_M=${REA_HEIGHT_M:-1.80} python3 scripts/compare_ladder.py > work/compare_$label.log
cp work/ladder.blend work/ladder_$label.blend; cp work/selection.json work/selection_$label.json; cp review/ladder_sheet.png review/ladder_sheet_$label.png
python3 - "$label" <<'PY'
import json, sys; d = json.load(open(f'work/selection_{sys.argv[1]}.json'))
print('limits', d['thresholds_mm'], 'source', d['source_tris'])
for t, c in d['ladder'].items(): print(' ', t, c['tris'], 'p99', c['p99_mm'], 'max', c['max_mm'], c.get('worst_at'), 'open', c['open_edges'], 'IoU', c['iou_min'], 'SSIM', c['ssim_mean'], 'PASS' if c['pass'] else 'fail')
PY
