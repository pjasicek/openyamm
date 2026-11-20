#!/usr/bin/env python3
"""Cluster the flagged faces of a ladder mesh (texture_drift.py > 40 and dark_slivers.py, re-run here) within 4 cm and
print the N largest clusters as 'x,y,z/nx,ny,nz' (centroid and mean outward normal) for spot_blend.py.
Usage: flag_spots.py <tag, e.g. cr74> [N]"""
import subprocess, sys
import numpy as np
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
tag = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 8
subprocess.run([sys.executable, 'scripts/texture_drift.py', tag], capture_output=True, check=True)
drift = np.load(f'work/drift_{tag}.npy')
subprocess.run([sys.executable, 'scripts/dark_slivers.py', tag], capture_output=True, check=True)
dark = np.load(f'work/drift_{tag}.npy')
d = np.load(f'work/mesh_{tag}.npz'); tri = d['verts'][d['faces']]
n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); area = np.linalg.norm(n, axis=1) / 2
n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
bad = np.where((drift > 40) | (dark > 0))[0]; cen = tri[bad].mean(1)
pairs = cKDTree(cen).query_pairs(0.04, output_type='ndarray')
from scipy.sparse import coo_matrix
m = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(len(bad), len(bad))) if len(pairs) else coo_matrix((len(bad), len(bad)))
_, lab = connected_components(m, directed=False)
cl = sorted(np.unique(lab), key=lambda c: -area[bad[lab == c]].sum())[:N]
out = []
for c in cl:
    s = bad[lab == c]; w = area[s]; p = (tri[s].mean(1) * w[:, None]).sum(0) / w.sum(); nn = (n[s] * w[:, None]).sum(0)
    nn /= np.linalg.norm(nn) + 1e-12
    print('CLUSTER', len(s), 'faces', round(float(w.sum() * 1e4), 1), 'cm2 at', np.round(p, 3).tolist(), 'normal', np.round(nn, 2).tolist())
    out.append(','.join(f'{x:.4f}' for x in p) + '/' + ','.join(f'{x:.3f}' for x in nn))
print('SPOTS', ';'.join(out))
