#!/usr/bin/env bash
# Iteration helper: rebuild the crown blend and render the front view, print the crown's mean colour.
# Usage: quick.sh <id> [views]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
blender=/home/pjasicek/github/OpenYAMM/level_generation/creatures/xeen_tiers_claude/bin/blender
id="$1"; views="${2:-eye}"
cd "$here"
python3 make_envelope.py "$id" >/dev/null
python3 prepare.py "$id" >/dev/null
"$blender" --background --python build_tree.py -- "$id" 2>&1 | grep -E "SKELETON|BARK lod 0|CLUMPS|CARDS|VIEW|OCCLUSION|^LOD|Error|Traceback"
"$blender" --background --python render_review.py -- "$id" "../work/$id/q" "../work/$id/tree.blend" "$views" lit 540 >/dev/null 2>&1
python3 - "$id" <<'PY'
import sys, numpy as np
from PIL import Image
sys.path.insert(0, '.')
import common
spec = common.load(sys.argv[1])
x = np.asarray(Image.open(f"{spec['work']}/q_Tree_eye.png").convert('RGBA')).astype(float)
m = x[..., 3] > 128; m[int(m.shape[0] * 0.78):] = False
print('QUICK crown mean', x[m][:, :3].mean(0).round(1).tolist(), 'target', spec['leaves']['target_srgb'])
PY
