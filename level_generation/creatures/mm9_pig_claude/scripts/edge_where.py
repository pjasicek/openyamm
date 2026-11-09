#!/usr/bin/env python3
"""Where the largest edge stretches sit: per clip the worst edges (bind midpoint, ratio) on the largest primitive.
Usage: edge_where.py <glb> [clips...]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1]))
pi = int(np.argmax([len(q['weights']) for q in m.primitives]))
rest, tris = m.skinned_positions(m.world({}))[pi]
t = np.asarray(tris).reshape(-1, 3)
e = np.unique(np.sort(np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1), axis=0)
L0 = np.linalg.norm(rest[e[:, 0]] - rest[e[:, 1]], axis=1)
keep = L0 > 1e-4
clips = sys.argv[2:] or [a['name'] for a in m.glb.json['animations']]
for c in clips:
    ts = m.clip_times(c)
    worst = {}
    for tt in np.arange(ts[0], ts[-1] + 1e-6, 1 / 30):
        P, _ = m.skinned_positions(m.world(m.sample(c, tt)))[pi]
        r = np.linalg.norm(P[e[:, 0]] - P[e[:, 1]], axis=1) / np.maximum(L0, 1e-6)
        r[~keep] = 1
        for i in np.argsort(-r)[:5]:
            if r[i] > worst.get(i, (0,))[0]:
                worst[i] = (float(r[i]), float(tt))
    top = sorted(worst.items(), key=lambda kv: -kv[1][0])[:6]
    print(c, [(round(v[0], 1), round(v[1], 2), np.round((rest[e[i, 0]] + rest[e[i, 1]]) / 2, 3).tolist(), round(float(L0[i]), 4)) for i, v in top])
