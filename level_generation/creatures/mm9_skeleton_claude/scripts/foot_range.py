#!/usr/bin/env python3
"""Fore-aft range of the feet and stance share per gait clip. Args: <glb> <clip>..."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); names = [n.get('name') for n in m.glb.json['nodes']]
for c in sys.argv[2:]:
    T = m.clip_times(c)[-1]; ts = np.arange(0, T, 1 / 60)
    for f in ('Bip01 L Foot', 'Bip01 R Foot'):
        p = np.array([m.world(m.sample(c, float(t)))[names.index(f)][:3, 3] for t in ts])
        R = np.ptp(p[:, 2]); h = p[:, 1]; st = (h < h.min() + 0.04).mean()
        v = -np.gradient(p[:, 2], ts); print(c, f, 'range', round(float(R), 3), 'stance', round(float(st), 2), 'p90 backward speed', round(float(np.percentile(v, 90)), 2), 'cycle stride R/stance', round(float(R / max(st, .1)), 2), 'dur', round(float(T), 3))
