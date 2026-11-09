"""Connected components of the welded source mesh (work/mesh_in.npz) -> work/comp.npy (component id per face);
prints each component's face count, dominant region (work/regions.npy) and centre."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']; reg = np.load('work/regions.npy')
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
comp = lab[f[:, 0]]; np.save('work/comp.npy', comp)
ids, cnt = np.unique(comp, return_counts=True)
for i in ids[np.argsort(-cnt)]:
    s = comp == i; c = v[f[s]].reshape(-1, 3)
    print(f'comp {i:4d} faces {s.sum():5d} region {np.bincount(reg[s], minlength=4).argmax()} centre {np.round(c.mean(0), 3)} size {np.round(np.ptp(c, 0), 3)}')
