#!/usr/bin/env python3
"""Clip jitter against MM9's untouched clip: per role at 30 fps, the XCENTER height in ours (after the floor pass) and in
MM9 (+lift), the largest frame-to-frame acceleration of each (mm per frame^2) and the largest height difference.
Usage: jitter.py <mm9 glb> <our glb> <lift>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
ROLE = {'Standing': 'Stand', 'Walking': 'Walk', 'Running': 'Run', 'Fidget': 'Fidget1', 'AttackMelee': 'HAttack1',
        'Hit': 'Wince1', 'Death': 'Die1'}
a, b, lift = Model(Glb(sys.argv[1])), Model(Glb(sys.argv[2])), float(sys.argv[3])
idx = lambda m: {m.glb.json['nodes'][j]['name']: j for j in m.joints}
ia, ib = idx(a), idx(b)
for role, src in ROLE.items():
    T = b.clip_times(role)[-1]; n = int(round(T * 30))
    ta = a.clip_times(src)[-1]
    ya, yb = [], []
    for k in range(n + 1):
        t = k / 30
        ya.append(a.world(a.sample(src, min(t, ta)))[ia['XCENTER']][1, 3] + lift)
        yb.append(b.world(b.sample(role, t))[ib['XCENTER']][1, 3])
    ya, yb = np.array(ya), np.array(yb)
    acc = lambda y: float(np.abs(np.diff(y, 2)).max()) * 1000 if len(y) > 2 else 0.0
    print(f'{role:12s} accel mm9 {acc(ya):6.1f} ours {acc(yb):6.1f}  height diff max {np.abs(ya - yb).max() * 1000:6.1f} mm')
