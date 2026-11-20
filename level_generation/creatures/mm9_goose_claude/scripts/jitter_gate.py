#!/usr/bin/env python3
"""Jitter gate: the floor pass moves the root per key. Per clip the root joint's height at 30 fps before (<a>) and after
(<b>) the pass: the applied offset's range and its largest frame-to-frame second difference (jitter), against the same
measure of the head joint in the source. Usage: jitter_gate.py <before glb> <after glb> <joint>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
A, B = Model(Glb(sys.argv[1])), Model(Glb(sys.argv[2]))
names = [n.get('name') for n in A.glb.json['nodes']]
j = names.index(sys.argv[3])
for an in A.glb.json['animations']:
    c = an['name']
    t0, t1 = A.clip_times(c)[0], A.clip_times(c)[-1]
    ts = np.arange(t0, t1 + 1e-6, 1 / 30)
    ha = np.array([A.world(A.sample(c, t))[j][1, 3] for t in ts])
    hb = np.array([B.world(B.sample(c, t))[j][1, 3] for t in ts])
    off = hb - ha
    sd = np.abs(np.diff(off, 2)).max() if len(off) > 2 else 0
    sa = np.abs(np.diff(ha, 2)).max() if len(ha) > 2 else 0
    print(c, 'offset %.4f..%.4f' % (off.min(), off.max()), 'offset 2nd diff %.5f' % sd, 'source 2nd diff %.5f' % sa)
