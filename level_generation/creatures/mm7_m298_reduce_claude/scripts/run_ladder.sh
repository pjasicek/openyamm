#!/usr/bin/env bash
# One ladder configuration on the already dumped mesh (work/mesh_in.npz): decimate, ladder, compare; results kept as
# work/ladder_<label>.blend and work/selection_<label>.json. Blender through tools/run_creature_blender.sh (lease token
# in CREATURE_3D_TOKEN). Usage: [REA_* env] run_ladder.sh <label> <ratios>
set -euo pipefail
label=$1; R=$2; cd "$(dirname "$0")/.."; P=$(pwd); REPO=$(cd ../../.. && pwd)
VENV="${REA_VENV:-/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/6ff9ed88-7a28-43ed-af0c-54fedb78da17/scratchpad/reduce_ooze/im_venv/bin/python} -I"
$VENV scripts/decimate_tex.py work $R > work/decimate_$label.log; cat work/decimate_$label.log
if [ "${REA_WEIGHTS:-}" = component ]; then $VENV scripts/uv_weights.py $R; fi
out=$(cd "$REPO" && REA_INFLUENCES=4 REA_METHOD=texture REA_RATIOS=$R tools/run_creature_blender.sh "${P#$REPO/}/scripts/reduce_ladder.py" 2>&1) || { echo "$out"; exit 1; }
cp "$(echo "$out" | sed -n 's/^Blender log: //p')" work/ladder_$label.log
REA_HEIGHT_M=${REA_HEIGHT_M:-1.0} $VENV scripts/compare_ladder.py > work/compare_$label.log
cp work/ladder.blend work/ladder_$label.blend; cp work/selection.json work/selection_$label.json
$VENV - "$label" <<'PY'
import json, sys; d = json.load(open(f'work/selection_{sys.argv[1]}.json'))
for t, c in d['ladder'].items(): print(' ', t, c['tris'], 'open', c['open_edges'], 'p99', c['p99_mm'], 'max', c['max_mm'], c.get('worst_at'), 'IoU', c['iou_min'], 'SSIM', c['ssim_mean'], 'PASS' if c['pass'] else 'fail')
PY
