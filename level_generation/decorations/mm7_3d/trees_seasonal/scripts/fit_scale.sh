#!/usr/bin/env bash
# Fit a species' Sapling scale so its skeleton top is <fraction> of height_m (default 0.96): a bare winter state must
# stay under its summer model's top. Usage: fit_scale.sh <id> [fraction]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"; cd "$here"
id="$1"; frac="${2:-0.96}"
for i in 1 2 3; do
  /snap/bin/blender --background --python skeleton_preview.py -- "$id" 2>&1 | grep -E "SKELETON" || true
  python3 - "$id" "$frac" <<'PY'
import json, sys, common
sid, frac = sys.argv[1], float(sys.argv[2])
spec = common.load(sid); k = json.load(open(spec['work'] + '/skel.json'))
target = frac * spec['height_m']
path = f'{common.TREES}/species/{sid}.json'; s = json.load(open(path))
if abs(k['top'] - target) > 0.02 * spec['height_m']:
    s['sapling']['scale'] = round(k['scale'] * target / k['top'], 2); json.dump(s, open(path, 'w'), indent=1)
    print('FIT', sid, 'scale ->', s['sapling']['scale'])
PY
done
