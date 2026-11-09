#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy),
MM8 Minotaur Peasant. Pieces: body (7,797, head included), wrap skirt (799), rope belt (449), two wrist bands (220).
Labels: 0 rest (torso, arms, legs, hooves), 1 head (B_Head dominant: muzzle, eyes, ears, horns, neck hump),
2 palms (B_*_Hand), 3 fingers (B_*_Finger*), 4 wrap skirt.
Kept exactly: the rope belt (painted twist lines), small pieces of up to REA_SMALL faces (wrist bands), and the
soles (faces below 6 cm)."""
import os, numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
c = v[f].mean(1); dom = info['dom']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; cnt = np.bincount(pc); size = cnt[pc]
order = cnt.argsort()[::-1]; body, wrap, belt = order[0], order[1], order[2]
assert cnt[wrap] == 799 and cnt[belt] == 449, (cnt[wrap], cnt[belt])
g = np.zeros(len(f), int)
g[(pc == body) & (dom == 'B_Head')] = 1
g[(pc == body) & np.char.endswith(dom.astype(str), '_Hand')] = 2
g[(pc == body) & (np.char.find(dom.astype(str), 'Finger') >= 0)] = 3
g[pc == wrap] = 4
small = size <= int(os.environ.get('REA_SMALL', '220'))
sole = c[:, 2] < .06
keep = (pc == belt) | small | sole
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in range(5)}, 'keep', int(keep.sum()), 'belt', int((pc == belt).sum()),
      'small', int(small.sum()), 'sole', int(sole.sum()))
