#!/usr/bin/env python3
"""Cow gait: per paw joint over Walking and Running, the body travel per cycle a planted paw implies (its mean
backward speed while it is low and moving back, times the cycle length). Usage: gait_measure.py <glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1]))
names = [n.get('name') for n in m.glb.json['nodes']]
for clip in ('Walking', 'Running'):
    T = m.clip_times(clip)[-1]
    ts = np.linspace(0, T, 121)
    out = []
    for paw in ('Xffoot01', 'Xffoot', 'Xbfoot01', 'Xbfoot'):
        P = np.array([np.asarray(m.world(m.sample(clip, t))[names.index(paw)])[:3, 3] for t in ts])
        z, y = P[:, 2], P[:, 1]   # glTF: +Z forward (Blender -Y), +Y up
        vz = np.gradient(z, ts)
        stance = (y < y.min() + 0.25 * (y.max() - y.min())) & (vz < 0)
        speed = -vz[stance].mean() if stance.any() else 0.0
        out.append((paw, round(float(z.max() - z.min()), 3), round(float(stance.mean()), 2), round(float(speed * T), 3)))
    print(clip, 'T', round(T, 3), out, 'stride (median)', np.median([o[3] for o in out]))
