#!/usr/bin/env python3
"""Viewer specs framed on the mouth and on the throat in any pose: the camera rides the head's skin rotation. Args: <glb> <prefix> <clip:seconds> ..."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); pre = sys.argv[2]; doc = m.glb.json; names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
h = names.index('Bip01 Head')
for k, cs in enumerate(sys.argv[3:]):
    c, t = cs.split(':'); w = m.world(m.sample(c, float(t))); S = w[m.joints[h]] @ m.inverse_binds[h]
    def P(p): return (S @ np.array([*p, 1.0]))[:3]
    mouth = P((0, 2.09, 0.33)); cam = P((0.12, 2.12, 1.05))
    throat = P((0, 1.93, 0.14)); cam2 = P((0.25, 1.55, 0.95))
    print(f'{pre}m{k}:{c}:{t}:front:body:' + ','.join(f'{x:.3f}' for x in cam) + ':' + ','.join(f'{x:.3f}' for x in mouth))
    print(f'{pre}t{k}:{c}:{t}:front:body:' + ','.join(f'{x:.3f}' for x in cam2) + ':' + ','.join(f'{x:.3f}' for x in throat))
