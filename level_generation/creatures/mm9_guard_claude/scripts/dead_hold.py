#!/usr/bin/env python3
"""Dead = the last pose of Death on every channel, after the arm and weapon corrections. Args: <in glb> <out glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb
g = Glb(Path(sys.argv[1])); d = g.json
A = {a['name']: a for a in d['animations']}
de, da = A['Death'], A['Dead']
n = 0
src = {(c['target']['node'], c['target']['path']): c for c in de['channels']}
for c in da['channels']:
    s = src.get((c['target']['node'], c['target']['path']))
    if s is None: continue
    last = np.asarray(g.accessor(de['samplers'][s['sampler']]['output']))[-1]
    sm = da['samplers'][c['sampler']]
    cnt = d['accessors'][sm['output']]['count']
    sm['output'] = g.append_accessor(np.tile(last, (cnt, 1)).astype(np.float32), d['accessors'][sm['output']]['type'])
    n += 1
g.write(Path(sys.argv[2]))
print('DEAD held', n, 'channels')
