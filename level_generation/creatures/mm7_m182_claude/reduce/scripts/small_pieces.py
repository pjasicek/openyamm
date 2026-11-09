# Copied from mm8_m492_reduce_claude/scripts (read-only reference) for the m182 v3b reduction.
"""Connected pieces of the rest mesh (work/mesh_in.npz): print sizes and centres; keep pieces of up to REA_SMALL faces
(default 80: teeth, eyes, small spikes) exactly -> work/keep_small.npy. Their ends taper to points at any cut."""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl)
LIM = int(os.environ.get('REA_SMALL', '80'))
for c in np.argsort(-sizes)[:60]:
    if sizes[c]:
        print('piece', c, sizes[c], 'faces, centre', np.round(v[f[fl == c]].reshape(-1, 3).mean(0), 3))
keep = sizes[fl] <= LIM
np.save('work/keep_small.npy', keep); print('KEEP small pieces', int(keep.sum()), 'faces in', int(((sizes > 0) & (sizes <= LIM)).sum()), 'pieces')
