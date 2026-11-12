#!/usr/bin/env python3
"""Half-joint helpers (`<joint>_H`, finish_guard.py): each helper shares its joint's parent and rest, and takes half the joint's local rotation, on the joint's own keys. Idempotent: replaces the
helper channels. Run after every clip edit of the arms and legs. Args: <in glb> <out glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb
g = Glb(Path(sys.argv[1])); d = g.json
names = [n.get('name') for n in d['nodes']]; idx = {n: i for i, n in enumerate(names)}
helpers = [(idx[n[:-2]], i) for i, n in enumerate(names) if n and n.endswith('_H')]
for an in d['animations']:
    hs = {h for _, h in helpers}
    an['channels'] = [c for c in an['channels'] if c['target']['node'] not in hs]
    new = []
    for j, h in helpers:
        r0 = np.array(d['nodes'][j].get('rotation', [0, 0, 0, 1]), float)
        ch = next((c for c in an['channels'] if c['target']['node'] == j and c['target']['path'] == 'rotation'), None)
        if ch is None: continue
        sm = an['samplers'][ch['sampler']]
        q = np.asarray(g.accessor(sm['output']), float)
        s = np.sign((q * r0).sum(1, keepdims=True)); s[s == 0] = 1
        m = q * s + r0                                         # half rotation: normalised sum (slerp 0.5)
        m /= np.linalg.norm(m, axis=1, keepdims=True)
        for k in range(1, len(m)):
            if m[k] @ m[k - 1] < 0: m[k] = -m[k]
        oa = g.append_accessor(m.astype(np.float32), 'VEC4')
        an['samplers'].append(dict(input=sm['input'], output=oa, interpolation=sm.get('interpolation', 'LINEAR')))
        new.append(dict(sampler=len(an['samplers']) - 1, target=dict(node=h, path='rotation')))
    an['channels'] += new
g.write(Path(sys.argv[2]))
print('HELPERS', len(helpers), 'keyed')
