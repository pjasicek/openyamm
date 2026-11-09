"""Face groups for the ratman ladder: work/groups.npy (0 head set = main ladder cut, 2 hands and fingers,
3 rest of the body) and work/keep_small.npy (from small_pieces.py) unchanged. The head texture set is the right
half of the merged 2080x1024 atlas (u > 1056/2080); hands are faces whose hand+finger weight is over 0.5."""
import numpy as np
d = np.load('work/mesh_in.npz'); r = np.load('work/regions.npz')
u = d['wuv'].reshape(-1, 3, 2)[:, :, 0].mean(1)
head = u > 1056 / 2080
hands = ~head & (r['finger'] + r['hand'] > .5)
g = np.where(head, 0, np.where(hands, 2, 3))
small = np.load('work/keep_small.npy')
np.save('work/groups.npy', g)
for k, n in [(0, 'head'), (2, 'hands'), (3, 'rest')]:
    print(n, int(((g == k) & ~small).sum()), 'faces to cut,', int(((g == k) & small).sum()), 'kept small')
# the ragged shirt (connected piece of 799 faces over the torso) loses its back flaps under the shared cut (25 mm in
# Running): own group 4
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
f = d['faces']; n = len(d['verts']); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl)
shirt = (fl == np.argsort(-sizes)[2]) & (g == 3)
assert 700 < shirt.sum() < 900, shirt.sum()
g[shirt] = 4; np.save('work/groups.npy', g)
np.save('work/keep_small_shirt.npy', small | shirt)
print('shirt', int(shirt.sum()), 'faces; rest now', int(((g == 3) & ~small).sum()))
