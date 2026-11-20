#!/usr/bin/env bash
# Pose-aware ladder (PeasantF8's run_mp.sh, per model M=1|2 in work/hof$M, review/hof$M): mpqem.py (half-edge collapse scored
# over every clip, linings re-emitted from their twins) -> reduce_ladder.py (exact source weights, error over every clip,
# renders) -> compare_ladder.py.
# Usage: M=1 [SETS=a MP_GROUPS=1:0.7,...] run_mp.sh <label> <ratios>
set -euo pipefail
label=$1; R=$2; cd "$(dirname "$0")/.."; : "${M:?M=1|2}"; export M
W=work/hof$M; V=review/hof$M
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
export MP_GROUPS=${MP_GROUPS:-} MP_TEX_MAX=${MP_TEX_MAX:-100} MP_TEX_MEAN=${MP_TEX_MEAN:-45}
if [[ -z "${SKIP_MP:-}" ]]; then scripts/cap.sh ../claude_shared/gltf_venv/bin/python -W ignore scripts/mpqem.py before/mm9_peasanthof$M.glb $R > $W/mp_$label.log; fi; grep -v "^POSES\|OFFSET" $W/mp_$label.log
if [[ -n "${SKIP_LADDER:-}" ]]; then for r in ${R//,/ }; do t=$(python3 -c "print(int(round($r*100)))"); cp $W/mp_r$t.npz $W/mp_${label}_r$t.npz; done; exit 0; fi
flock work/blender.lock env REA_INFLUENCES=4 REA_METHOD=texture REA_RATIOS=$R $BL -P scripts/reduce_ladder.py > $W/ladder_$label.log 2>&1
REA_HEIGHT_M=${REA_HEIGHT_M:-1.97} scripts/cap.sh python3 scripts/compare_ladder.py > $W/compare_$label.log
cp $W/ladder.blend $W/ladder_$label.blend; cp $W/selection.json $W/selection_$label.json
cp $V/ladder_sheet.png $V/ladder_sheet_$label.png
for r in ${R//,/ }; do t=$(python3 -c "print(int(round($r*100)))"); cp $W/mp_r$t.npz $W/mp_${label}_r$t.npz; done
python3 - "$W/selection_$label.json" <<'PY'
import json, sys; d = json.load(open(sys.argv[1]))
for t, c in d['ladder'].items(): print(' ', t, c['tris'], 'open', c['open_edges'], 'p99', c['p99_mm'], 'max', c['max_mm'], c.get('worst_at'), 'IoU', c['iou_min'], 'SSIM', c['ssim_mean'], 'PASS' if c['pass'] else 'fail')
PY
