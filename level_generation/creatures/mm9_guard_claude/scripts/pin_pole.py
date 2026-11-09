#!/usr/bin/env python3
"""MM9 keys the weapon bone inside the hand in `sleep`: the pole slides through our closed fist. Pins Xbase to its Standing local pose in the named clips. Args: <in glb> <out glb> CLIP..."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb
g = Glb(Path(sys.argv[1])); d = g.json; names = [n.get('name') for n in d['nodes']]; X = names.index('Xbase')
A = {a['name']: a for a in d['animations']}
ref = {c['target']['path']: np.asarray(g.accessor(A['Standing']['samplers'][c['sampler']]['output']))[0] for c in A['Standing']['channels'] if c['target']['node'] == X}
for clip in sys.argv[3:]:
    a = A[clip]
    for c in a['channels']:
        if c['target']['node'] != X: continue
        s = a['samplers'][c['sampler']]; v = np.asarray(g.accessor(s['output'])); move = float(np.abs(v - v[0]).max())
        s['output'] = g.append_accessor(np.tile(ref[c['target']['path']], (len(v), 1)), 'VEC4' if v.shape[1] == 4 else 'VEC3')
        print('PIN', clip, c['target']['path'], 'range', round(move, 3))
g.write(Path(sys.argv[2]))
