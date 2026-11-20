#!/usr/bin/env python3
"""Per-face region labels (work/groups.npy) and exact-keep mask (work/keep_base.npy), MM8 Dark Dwarf.
Labels: 0 rest (torso, armour, skirt, boots), 1 face and neck skin (head-set faces of the main body piece),
2 beard (front piece and two side strands), 3 helmet dome, 4 helmet horns, 5 braid and rear hair, 6 spiked
pauldrons, 7 upper-arm sleeves, 8 trousers and mail skirt, 9 boots, 10 arm skin
(body piece), 11 torso skin (body piece).
Kept exactly: both hands (the crossbow's trigger and support grips are fitted to them), small pieces of up to
REA_SMALL faces (eyes, spikes, studs, buckle, bracer rings) and the soles (faces below 6 cm)."""
import os, numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
c = v[f].mean(1); dom = info['dom']; head = info['u'] > .5
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; size = np.bincount(pc)[pc]
pieces = {}
for p in np.unique(pc):
    m = pc == p; pieces[p] = (int(m.sum()), c[m].mean(0), head[m].mean())
def find(nf, x=None, y=None, z=None, tol=.03):
    out = [p for p, (k, cc, _) in pieces.items() if k == nf and all(t is None or abs(cc[i] - t) < tol for i, t in enumerate((x, y, z)))]
    assert len(out) == 1, (nf, x, y, z, out); return out[0]
body = find(2299); beard = [find(360, y=-.19), find(219, x=-.066, y=-.18), find(219, x=.053, y=-.18)]
helmet = find(300, z=1.265); horns = [find(225, x=-.161), find(223, x=.15)]
hair = [find(450, y=.154), find(219, x=.092, y=.173), find(219, x=-.092, y=.172)]
g = np.zeros(len(f), int)
g[(pc == body) & head] = 1; g[np.isin(pc, beard)] = 2; g[pc == helmet] = 3; g[np.isin(pc, horns)] = 4
g[np.isin(pc, hair)] = 5
pauldrons = [find(220, x=.221), find(220, x=-.231)]; upper = [find(180, x=-.268), find(180, x=.261)]
skirt = [find(400, z=.461), find(358, z=.509)]; boots = [find(219, x=.225, z=.089), find(219, x=-.227, z=.083)]
arm = np.array([('Arm' in x or 'Forearm' in x) for x in dom])
g[(pc == body) & ~head & arm] = 10; g[(pc == body) & ~head & ~arm] = 11
g[np.isin(pc, pauldrons)] = 6; g[np.isin(pc, upper)] = 7; g[np.isin(pc, skirt)] = 8; g[np.isin(pc, boots)] = 9
hands = np.array([x.startswith(('B_L_Hand', 'B_R_Hand', 'B_L_Finger', 'B_R_Finger')) for x in dom])
hands |= np.isin(pc, [find(525, x=.511), find(522, x=-.514)])
small = size <= int(os.environ.get('REA_SMALL', '100'))
sole = c[:, 2] < .06
keep = hands | small | sole
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('GROUPS', {k: int((g == k).sum()) for k in range(12)}, 'keep', int(keep.sum()), 'hands', int(hands.sum()),
      'small', int(small.sum()), 'sole', int(sole.sum()))
