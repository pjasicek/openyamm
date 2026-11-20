#!/usr/bin/env python3
"""Jitter gate: the floor pass's correction per clip (height of XCENTER ours vs before the floor pass): range and largest
frame-to-frame change of the correction and its second difference. Usage: root_jitter.py <final glb> <glb before floor pass>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
a, b = Model(Glb(sys.argv[1])), Model(Glb(sys.argv[2]))
n = [x.get('name') for x in a.glb.json['nodes']].index('XCENTER')
for c in a.clips:
    ts = np.arange(0, a.clip_times(c)[-1] + 1e-6, 1 / 30)
    d = np.array([a.world(a.sample(c, t))[n][1, 3] - b.world(b.sample(c, t))[n][1, 3] for t in ts])
    print(f'{c:12s} correction {d.min():+.4f}..{d.max():+.4f} step max {np.abs(np.diff(d)).max():.4f} second diff max {np.abs(np.diff(d, 2)).max() if len(d) > 2 else 0:.4f}')
