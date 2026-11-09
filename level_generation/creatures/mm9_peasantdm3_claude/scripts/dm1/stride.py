#!/usr/bin/env python3
"""Stride of an in-place walk/run: planted-foot speed along the facing axis (glTF +Z) x cycle length.
Usage: stride.py <glb> <clip> <foot joint> [<foot joint>...]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model

glb = Glb(Path(sys.argv[1])); m = Model(glb); clip = sys.argv[2]
names = [n.get('name') for n in glb.json['nodes']]
dur = max(m.clip_times(clip)); ts = np.arange(0, dur, 1 / 60)
for foot in sys.argv[3:]:
    i = names.index(foot)
    p = np.array([m.world(m.sample(clip, float(t)))[i][:3, 3] for t in ts])
    low = p[:, 1] < p[:, 1].min() + 0.02
    v = np.gradient(p[:, 2], ts)
    speed = -np.median(v[low])
    print(f'{foot}: planted speed {speed:.3f} m/s, stride {speed * dur:.3f} m over {dur:.3f} s, '
          f'planted {low.mean() * 100:.0f}% of the cycle')
