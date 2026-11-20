#!/usr/bin/env python3
"""Viewer close-up shot specs around joints. Usage: close_specs.py <glb> <prefix> <clip:seconds> <joint:ox,oy,oz:dist> ..."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb, pre, cs = sys.argv[1:4]; m = Model(Glb(glb)); names = [n.get('name') for n in m.glb.json['nodes']]
clip, sec = cs.split(':'); w = m.world(m.sample(clip, float(sec)))
for k, it in enumerate(sys.argv[4:]):
    j, o, d = it.split(':'); p = w[names.index(j)][:3, 3]
    o = np.array([float(x) for x in o.split(',')]); o = o / np.linalg.norm(o) * float(d)
    print(f'{pre}{k}:{clip}:{sec}:front:body:' + ','.join(f'{x:.3f}' for x in p + o) + ':' + ','.join(f'{x:.3f}' for x in p))
