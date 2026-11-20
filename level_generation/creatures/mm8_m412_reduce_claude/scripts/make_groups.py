#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy),
MM8 Pirate Warrior. Head texture set = u > 0.5 of the merged 2080x1024 atlas.
Labels: 0 rest (shirt, trousers, boots, sash), 1 face skin (head set, B_Head, front, below the bandanna), 2 neck,
chest skin and scalp (rest of the head-set skin piece), 3 bandanna, 4 left hook and its socket.
Kept exactly: the sword fist (B_R_Hand / B_R_Finger* dominant faces), small pieces of up to REA_SMALL faces (eyes,
eyepatch and strap, earrings, buckle, sash knots, cuffs), and the soles (faces below 6 cm; foot-yaw gates)."""
import os, numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
c = v[f].mean(1); dom = info['dom']; head = info['u'] > .5
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; size = np.bincount(pc)[pc]
big = np.bincount(pc).argsort()[::-1]
g = np.zeros(len(f), int)
# bandanna: the large head-set piece above the eyes that is all B_Head
band = [p for p in big[:8] if head[pc == p].all() and (dom[pc == p] == 'B_Head').all() and c[pc == p][:, 2].mean() > 1.5]
assert len(band) == 1, band
skin = head & (pc != band[0]) & (size > 1000)
FACE_Y, FACE_Z = float(os.environ.get('FACE_Y', '-0.03')), float(os.environ.get('FACE_Z', '1.47'))
face = skin & (dom == 'B_Head') & (c[:, 1] < FACE_Y) & (c[:, 2] > FACE_Z)
g[skin & ~face] = 2; g[face] = 1; g[pc == band[0]] = 3
hook = (dom == 'B_L_ForearmTwist') & (size == 500)
g[hook] = 4
fist = np.array([x == 'B_R_Hand' or x.startswith('B_R_Finger') for x in dom])
small = size <= int(os.environ.get('REA_SMALL', '180'))
sole = c[:, 2] < .06
keep = fist | small | sole
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('GROUPS', {k: int((g == k).sum()) for k in range(5)}, 'keep', int(keep.sum()), 'fist', int(fist.sum()),
      'small', int(small.sum()), 'sole', int(sole.sum()))
