#!/usr/bin/env python3
"""Viewer cameras on the left hand and its skull per clip: front, 3/4 (from the figure's left-front), low (from below-front), DIST m from
the point OFF below the Hand joint (the clip pose). Args: <glb> <prefix> <dist> <clip:sec,...>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb, pre, dist = sys.argv[1], sys.argv[2], float(sys.argv[3])
m = Model(Glb(glb)); names = [n.get('name') for n in m.glb.json['nodes']]
for cs in sys.argv[4].split(','):
    clip, sec = cs.split(':'); w = m.world(m.sample(clip, float(sec)))
    h = w[names.index('FHP L Hand')][:3, 3]; t = h + np.array([0, -0.10, 0.02])
    for k, d in (('front', (0, 0.15, 1)), ('q34', (0.8, 0.2, 0.7)), ('low', (0.3, -0.6, 0.8))):
        d = np.array(d, float); d /= np.linalg.norm(d); c = t + d * dist
        print(f'{pre}_{clip}_{k}:{clip}:{sec}:front:body:' + ','.join(f'{x:.3f}' for x in c) + ':' + ','.join(f'{x:.3f}' for x in t))
