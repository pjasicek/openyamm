#!/usr/bin/env python3
"""Body and leg channels: new GLB against the approved one, largest difference per clip, skirt bones excluded. Args: <new> <old>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb
A, B = Glb(sys.argv[1]), Glb(sys.argv[2])
na = [n.get('name') for n in A.json['nodes']]; nb = [n.get('name') for n in B.json['nodes']]
ca = {a['name']: a for a in A.json['animations']}
for b in B.json['animations']:
    a = ca[b['name']]; worst = (0, ''); wt = (0, '')
    cha = {(na[c['target']['node']], c['target']['path']): c for c in a['channels']}
    for c in b['channels']:
        k = (nb[c['target']['node']], c['target']['path'])
        vb = B.accessor(b['samplers'][c['sampler']]['output']); va = A.accessor(a['samplers'][cha[k]['sampler']]['output'])
        if len(va) != len(vb): worst = (9, k[0] + ' key count'); continue
        d = np.abs(np.abs(va) - np.abs(vb)).max() if k[1] == 'rotation' else np.abs(va - vb).max()
        if k[1] == 'translation':
            if d > wt[0]: wt = (float(d), k[0])
        elif d > worst[0]: worst = (float(d), k[0])
    print(f"{b['name']:15s} rotation diff {worst[0]:.5f} {worst[1]:18s} translation diff {wt[0] * 100:.2f} cm {wt[1]}")
