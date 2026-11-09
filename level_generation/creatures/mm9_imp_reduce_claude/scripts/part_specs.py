#!/usr/bin/env python3
"""Viewer specs framed on the posed centroid of the vertices a bone group dominates (imp-reduce-20261104; the bone origins sit at
the wrists and ankles of this small body). Usage: part_specs.py <glb> <prefix> <clip:seconds> <bone substring,...> <dx,dy,dz:dist> ..."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb, pre, cs, bones = sys.argv[1:5]; m = Model(Glb(glb)); names = [n.get('name') for n in m.glb.json['nodes']]
jn = [names[j] for j in m.joints]; sel = np.array([any(b in n for b in bones.split(',')) for n in jn])
clip, sec = cs.split(':'); sp = m.skinned_positions(m.world(m.sample(clip, float(sec))))
node = m.primitives[0]['node']; P = [k for k, p in enumerate(m.primitives) if p['node'] == node]
X = np.vstack([sp[k][0] for k in P]); J = np.vstack([m.primitives[k]['joints'] for k in P]); W = np.vstack([m.primitives[k]['weights'] for k in P])
dom = J[np.arange(len(J)), W.argmax(1)]; p = X[sel[dom]].mean(0)
for k, it in enumerate(sys.argv[5:]):
    o, d = it.split(':'); o = np.array([float(x) for x in o.split(',')]); o = o / np.linalg.norm(o) * float(d)
    print(f'{pre}{k}:{clip}:{sec}:front:body:' + ','.join(f'{x:.3f}' for x in p + o) + ':' + ','.join(f'{x:.3f}' for x in p))
