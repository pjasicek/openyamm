#!/usr/bin/env python3
"""Faces of the neck/head label bad at a pose: bind position table. Args glb clip t"""
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); doc = m.glb.json; names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
PR = m.primitives; rest = np.vstack([np.asarray(p['positions'], float) for p in PR]); OFF = np.cumsum([0] + [len(p['positions']) for p in PR]); pv = np.concatenate([np.full(len(p['positions']), i) for i, p in enumerate(PR)])
T = np.vstack([np.asarray(x[1]).reshape(-1, 3) + o for x, o in zip(m.skinned_positions(m.world({})), OFF)])
J = np.vstack([p['joints'] for p in PR]); W = np.vstack([p['weights'] for p in PR])
w = m.world(m.sample(sys.argv[2], float(sys.argv[3]))); P = np.vstack([x[0] for x in m.skinned_positions(w)])
fw = np.zeros((len(T), len(names)))
for k in range(J.shape[1]):
    for c in range(3): np.add.at(fw, (np.arange(len(T)), J[T[:, c], k]), W[T[:, c], k])
dom = fw.argmax(1)
def tri(P):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); return n, np.linalg.norm(n, axis=1) / 2
n0, a0 = tri(rest); n, a = tri(P); pal = w[m.joints] @ m.inverse_binds
nr = np.einsum('fij,fj->fi', np.einsum('fb,bij->fij', fw / 3, pal[:, :3, :3]), n0)
d = (n * nr).sum(1) / np.maximum(np.linalg.norm(n, axis=1) * np.linalg.norm(nr, axis=1), 1e-12)
bad = (a0 > 1e-9) & ((a < .2 * a0) | (d < 0)); sel = bad & np.isin(dom, [names.index(x) for x in ('Bip01 Neck', 'Bip01 Head', 'Bip01 XhalfHead')])
c = rest[T[sel]].mean(1); print('n', sel.sum(), 'prim', np.bincount(pv[T[sel, 0]], minlength=len(PR))[:4], 'area ratio', np.round(a[sel] / a0[sel], 2)[:20], 'dot', np.round(d[sel], 2)[:20])
print(np.round(c[np.argsort(c[:, 1])], 3)[:40])
