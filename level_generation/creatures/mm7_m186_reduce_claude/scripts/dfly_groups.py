"""Per-face labels for the dragonfly ladder (work/mesh_in.npz): connected pieces by size.
- keep (work/keep_eyes.npy): the two compound-eye pieces (167 / 179 faces at the head), kept exactly;
- protect (work/protect_head.npy): main-piece faces dominated by the Head bone (face, mandible roots), own gentle ratio;
- groups (work/groups.npy): 1 = the ~60 small separate pieces (crest spines, bristles, mandibles, claw prongs), own ratio;
  0 = the rest of the main piece (abdomen, neck, claw) takes the remaining ladder budget."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl)
main = sizes[fl] == sizes.max()
cen = v[f].mean(1)
eyes = np.zeros(len(f), bool)
for c in np.unique(fl[~main]):
    m = fl == c
    if 150 <= sizes[c] <= 200 and cen[m, 2].mean() > 0.38 and cen[m, 1].mean() < -0.14:
        eyes |= m
small = ~main & ~eyes
prot = main & (d['protect'] > .5)
np.save('work/keep_eyes.npy', eyes); np.save('work/protect_head.npy', prot); np.save('work/groups.npy', small.astype(int))
print('FACES', len(f), 'main', int(main.sum()), 'main head', int(prot.sum()), 'eyes', int(eyes.sum()), 'small', int(small.sum()))
