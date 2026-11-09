#!/usr/bin/env bash
# New slivers / long faces of a ladder mesh (sliver_probe.py) with their visibility (visibility.py on the candidate:
# views out of 26 in which the face owns >= 2 pixels) and source group. Usage: sliver_vis.sh <tag, e.g. p_r78>
set -euo pipefail; cd "$(dirname "$0")/.."; t=$1
python3 scripts/sliver_probe.py work/mesh_in.npz work/mesh_$t.npz > work/slivers_$t.log
REA_MESH=work/mesh_$t.npz REA_OUT=work/visible_$t.npy python3 scripts/visibility.py -0.01 1.76 > /dev/null
python3 - "$t" <<'PY'
import re, sys, numpy as np
t = sys.argv[1]; s = np.load(f'work/visible_{t}.npy'); g = np.load(f'work/mesh_{t}.npz')['group']
for l in open(f'work/slivers_{t}.log'):
    m = re.match(r'\s+NEW (SLIVER|LONGFACE) (\d+)(.*)', l)
    if m:
        i = int(m.group(2)); print(m.group(1), i, 'views', int(s[i]), 'group', g[i], m.group(3).strip())
    elif not l.startswith(' '):
        print(l.rstrip())
PY
