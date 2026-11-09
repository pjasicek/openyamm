#!/usr/bin/env python3
"""Where throw_hand is at the release: world point of the socket joint against the hand's mesh, per clip. Args: <glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); names = [n.get('name') for n in m.glb.json['nodes']]
jn = [names[j] for j in m.joints]
S = names.index('Bip01 L Finger11'); H = names.index('Bip01 L Hand')
for clip, t in (('AttackRanged', 0.377), ('AttackRanged2', 0.971)):
    w = m.world(m.sample(clip, t))
    sp = np.concatenate([r[0] for r in m.skinned_positions(w)])
    hv = []
    off = 0
    for k, pr in enumerate(m.primitives):
        if pr['node'] != m.primitives[0]['node']: continue
        dom = np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))])
        hv.append(off + np.where(np.char.find(dom.astype(str), ' L ') >= 0)[0]); off += len(pr['positions'])
    hv = np.concatenate(hv)
    p = w[S][:3, 3]; h = w[H][:3, 3]
    d = np.linalg.norm(sp[:len(sp)] - p, axis=1)
    print(clip, 'socket', p.round(3), 'wrist', h.round(3), 'socket-to-wrist %.3f m' % np.linalg.norm(p - h), 'nearest mesh %.3f m' % d.min(), 'forward (z) of pelvis %.3f' % (p[2] - w[names.index('Bip01 Pelvis')][2, 3]), 'height %.3f' % p[1])
