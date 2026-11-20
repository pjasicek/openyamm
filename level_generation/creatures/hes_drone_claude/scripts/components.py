#!/usr/bin/env python3
"""Connected mesh components of the master's triangles (work/uv3d.npz, welded by position) -> work/tri_comp.npy
(component id per triangle), used by compose_hdr.py to find the rib spurs."""
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
ROOT = Path(__file__).resolve().parents[1]
d = np.load(ROOT / 'work' / 'uv3d.npz'); co = d['co']
_, inv = np.unique(np.round(co.reshape(-1, 3), 5), axis=0, return_inverse=True)
T = inv.reshape(-1, 3); n = T.max() + 1
r = np.concatenate([T[:, 0], T[:, 1], T[:, 2]]); c = np.concatenate([T[:, 1], T[:, 2], T[:, 0]])
k, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)
tc = lab[T[:, 0]]
old = ROOT / 'work' / 'tri_comp.npy'
if old.exists() and np.load(old).shape == tc.shape:
    print('COMPONENTS same as before:', bool((np.load(old) == tc).all()))
np.save(old, tc); print('COMPONENTS', k)
