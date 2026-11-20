#!/usr/bin/env bash
# Winged Mutant: decimate_sym.py (mirror-symmetric; REA_GROUP_RATIOS for hair 1, wing 2, feet 3), UV weights always.
# One ladder configuration on the already dumped mesh (work/mesh_in.npz): decimate, ladder, compare; results kept as
# work/ladder_<label>.blend and work/selection_<label>.json. Usage: [REA_PROTECT_* env] run_ladder.sh <label> <ratios>
set -euo pipefail
label=$1; R=$2; cd "$(dirname "$0")/.."
VENV="scripts/cap.sh /home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/meshlab_venv/bin/python -I"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
$VENV scripts/decimate_sym.py work $R > work/decimate_$label.log; cat work/decimate_$label.log
scripts/cap.sh python3 scripts/uv_weights.py $R
REA_INFLUENCES=4 REA_METHOD=texture REA_RATIOS=$R $BL -P scripts/reduce_ladder.py > work/ladder_$label.log 2>&1
REA_HEIGHT_M=${REA_HEIGHT_M:-1.67} scripts/cap.sh python3 scripts/compare_ladder.py > work/compare_$label.log
cp work/ladder.blend work/ladder_$label.blend; cp work/selection.json work/selection_$label.json
python3 - "$label" <<'PY'
import json, sys; d = json.load(open(f'work/selection_{sys.argv[1]}.json'))
for t, c in d['ladder'].items(): print(' ', t, c['tris'], 'p99', c['p99_mm'], 'max', c['max_mm'], c.get('worst_at'), 'IoU', c['iou_min'], 'SSIM', c['ssim_mean'], 'PASS' if c['pass'] else 'fail')
PY
mkdir -p work/cfg_$label; for t in ${R//,/ }; do n=$(python3 -c "print(int(round($t*100)))"); cp work/mesh_r$n.npz work/weights_r$n.npz work/cfg_$label/; done; cp work/sets.npz work/cfg_$label/
