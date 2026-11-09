#!/usr/bin/env python3
"""Viewer specs framing the whole head: front, quarter, side, below. Args: <glb> <prefix>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); names = [n.get('name') for n in m.glb.json['nodes']]
p = m.world(m.sample('Standing', 0.5))[names.index('Bip01 Head')][:3, 3] + [0, 0.09, 0.05]
for k, o in enumerate(((0, 0.04, 1), (-0.75, 0.05, 0.75), (-1, 0.03, 0), (0.45, -0.75, 0.75))):
    o = np.array(o, float); o = o / np.linalg.norm(o) * 0.62
    print(f'{sys.argv[2]}{k}:Standing:0.5:front:body:' + ','.join(f'{x:.3f}' for x in p + o) + ':' + ','.join(f'{x:.3f}' for x in p))
