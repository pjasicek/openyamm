#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM8 Vampire (faces -y). Pieces: body skin with head, hands and feet in one piece (6,500), ragged vest 1,499, torn
trousers 900, belt 274 + 223, eyes 196 / 194, mouth and teeth pieces (154 and below). Labels: 0 body skin (torso,
arms, legs), 1 head skin (head atlas, u > .505), 2 hands and clawed fingers, 3 feet and toes, 4 vest, 5 trousers.
Kept exactly: pieces of up to 280 faces (eyes, mouth, fangs and teeth, the belt with its buckle)."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); size = sizes[pc]
order = np.argsort(-sizes); body, vest, trousers = order[:3]
dom = info['dom'].astype(str)
g = np.zeros(len(f), int)
on_body = pc == body
g[on_body & (info['u'] > .505)] = 1
g[on_body & (info['u'] <= .505) & np.char.find(dom, 'Hand').__ge__(0)] = 2
g[on_body & (info['u'] <= .505) & np.char.find(dom, 'Finger').__ge__(0)] = 2
g[on_body & (info['u'] <= .505) & (np.char.find(dom, 'Foot') >= 0) | on_body & (np.char.find(dom, 'Toe') >= 0)] = 3
g[pc == vest] = 4; g[pc == trousers] = 5
keep = size <= 280
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in range(6)}, 'keep', int(keep.sum()),
      'pieces', sizes[body], sizes[vest], sizes[trousers])
