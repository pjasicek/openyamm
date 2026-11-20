#!/usr/bin/env bash
# One ladder configuration on the dumped mesh (work/mesh_in.npz): texture-aware MeshLab decimation with the robot
# face labels (robot_groups.py), ladder (weights by transfer + piece weights, error over every clip, renders), compare;
# kept as work/ladder_<label>.blend and work/selection_<label>.json. Thresholds scaled to the robot's 0.96 m length.
# Usage: REA_PROTECT_RATIO=.. REA_GROUP_RATIOS=1:..,2:.. run_ladder.sh <label> <ratios> LEASE_TOKEN
set -euo pipefail
label=$1; R=$2; token=$3; cd "$(dirname "$0")/.."
VENV="/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/a2981f4f-bdca-4d0a-bfc6-14c520ffd94b/scratchpad/im_venv/bin/python -I"
REA_PROTECT_FACES=work/protect_head.npy REA_KEEP_FACES=${KEEP:-work/keep_spikes.npy} REA_GROUPS=work/groups.npy $VENV scripts/decimate_tex.py work $R > work/decimate_$label.log
cat work/decimate_$label.log
(cd ../../.. && REA_INFLUENCES=4 REA_METHOD=texture REA_RATIOS=$R tools/run_creature_blender.sh --token $token \
  level_generation/creatures/mm7_m386_v2_claude/scripts/reduce_ladder.py) > work/ladder_$label.log 2>&1
grep -h "^LADDER" $(grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' work/ladder_$label.log | head -1)
REA_HEIGHT_M=0.96 python3 scripts/compare_ladder.py > work/compare_$label.log
cp work/ladder.blend work/ladder_$label.blend; cp work/selection.json work/selection_$label.json
cp review/ladder_sheet.png review/ladder_sheet_$label.png 2>/dev/null || true
python3 - "$label" <<'PY'
import json, sys; d = json.load(open(f'work/selection_{sys.argv[1]}.json'))
for t, c in d['ladder'].items(): print(' ', t, c['tris'], 'p99', c['p99_mm'], 'max', c['max_mm'], c.get('worst_at'), 'IoU', c['iou_min'], 'SSIM', c['ssim_mean'], 'PASS' if c['pass'] else 'fail')
print('picked', d['picked'])
PY
