#!/usr/bin/env python3
"""MM9 cloth chains: link lengths across clips, keyed translations. Args: <glb>"""
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
g = Glb(sys.argv[1]); m = Model(g); names = [n.get('name') for n in g.json['nodes']]
par = {c: i for i, n in enumerate(g.json['nodes']) for c in n.get('children', [])}
sk = [i for i in range(81) if names[i][0] in 'XY' and names[i] != 'Xmain' ]
bone_len = {}
for a in g.json['animations']:
    trans = set(names[c['target']['node']] for c in a['channels'] if c['target']['path'] == 'translation')
    dur = max(g.accessor(s['input']).max() for s in a['samplers'])
    for t in np.linspace(0, dur, 7):
        w = m.world(m.sample(a['name'], t))
        for i in sk:
            l = np.linalg.norm(w[i][:3, 3] - w[par[i]][:3, 3]); bone_len.setdefault(names[i], []).append(l)
print('translated in last clip', len(trans), sorted(trans)[:12])
for k, v in bone_len.items():
    print(f'{k:10s} {min(v):.3f} {max(v):.3f}')
