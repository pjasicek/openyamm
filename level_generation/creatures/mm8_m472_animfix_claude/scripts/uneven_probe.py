#!/usr/bin/env python3
"""Where a clip's once-per-loop head bob comes from: per-sample heights of pelvis, spine2, head (cm) and the
once-per-loop (k=1) and once-per-step (k=2) Fourier amplitudes of each.

    uneven_probe.py <glb> <clip>[,<clip>...]
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared/floor'))
import glb_pose  # noqa: E402

model = glb_pose.Model(glb_pose.Glb(sys.argv[1]))
idx = {n.get('name'): i for i, n in enumerate(model.glb.json['nodes'])}
for clip in sys.argv[2].split(','):
    T = max(float(model.glb.json['accessors'][s['input']]['max'][0])
            for a in model.glb.json['animations'] if a['name'] == clip for s in a['samplers'])
    n = 120
    ys = {k: [] for k in ('B_Pelvis', 'B_Spine2', 'B_Head')}
    for t in np.arange(n) / n * T:
        W = model.world(model.sample(clip, t))
        for k in ys:
            ys[k].append(W[idx[k]][1, 3])
    out = []
    for k, y in ys.items():
        f = np.fft.rfft(np.array(y) - np.mean(y)) / n * 2
        out.append(f'{k[2:]} k1 {abs(f[1]) * 100:4.1f} k2 {abs(f[2]) * 100:4.1f} cm')
    print(f'{clip:9} ' + '  '.join(out))
