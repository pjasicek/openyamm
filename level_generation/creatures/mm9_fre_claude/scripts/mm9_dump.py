#!/usr/bin/env python3
"""MM9 mesh with weights as npz, Blender frame (x, -z, y of glTF), welded per piece by position. Args: <glb> <out npz>"""
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb
g = Glb(sys.argv[1]); j = g.json; names = [n.get('name') for n in j['nodes']]; sk = j['skins'][0]['joints']; jn = [names[i] for i in sk]
V = []; T = []; W = []; PC = []; off = 0; pieces = []
for k, m in enumerate(j['meshes']):
    p = m['primitives'][0]; v = g.accessor(p['attributes']['POSITION']); J = g.accessor(p['attributes']['JOINTS_0']).astype(int); w = g.accessor(p['attributes']['WEIGHTS_0'])
    t = g.accessor(p['indices']).astype(int).reshape(-1, 3)
    Wf = np.zeros((len(v), len(jn)))
    for c in range(J.shape[1]): np.add.at(Wf, (np.arange(len(v)), J[:, c]), w[:, c])
    key = np.round(v, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); n = inv.max() + 1
    Q = np.zeros((n, 3)); Q[inv] = v; Wn = np.zeros((n, len(jn))); Wn[inv] = Wf
    V.append(np.c_[Q[:, 0], -Q[:, 2], Q[:, 1]]); T.append(inv[t] + off); W.append(Wn); PC.append(np.full(n, k)); off += n; pieces.append(m['name'])
np.savez(sys.argv[2], co=np.vstack(V), tri=np.vstack(T), W=np.vstack(W), piece=np.concatenate(PC), pieces=np.array(pieces), jn=np.array(jn))
c = np.vstack(V); print(c.shape, c.min(0), c.max(0))
for z in (-0.9, -0.7, -0.5, -0.3, -0.1, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
    q = np.vstack(V[:1]); s = q[np.abs(q[:, 2] - z) < 0.04]
    if len(s): print(z, 'x', s[:, 0].min().round(3), s[:, 0].max().round(3), 'y', s[:, 1].min().round(3), s[:, 1].max().round(3))
