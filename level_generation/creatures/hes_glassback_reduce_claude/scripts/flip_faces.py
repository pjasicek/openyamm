#!/usr/bin/env python3
"""Folded or flipped faces of decimated candidates: a candidate face whose normal opposes the source surface at its
centre (dense source samples, nearest with the source face normal) or which is a near-zero-area sliver.
Usage: flip_faces.py <tag...>  (work/mesh_in.npz, work/mesh_<tag>.npz) -> work/flip_<tag>.npy (bool per face)"""
import sys
import numpy as np
from scipy.spatial import cKDTree
s = np.load('work/mesh_in.npz'); sv, sf = s['verts'], s['faces']
st = sv[sf]; sn = np.cross(st[:, 1] - st[:, 0], st[:, 2] - st[:, 0]); sa = np.linalg.norm(sn, axis=1); sn /= sa[:, None] + 1e-20
rng = np.random.default_rng(0); B = rng.dirichlet((1, 1, 1), 6)
pts = np.einsum('sk,fkc->fsc', B, st).reshape(-1, 3); owner = np.repeat(np.arange(len(sf)), len(B))
tree = cKDTree(pts)
for tag in sys.argv[1:]:
    c = np.load(f'work/mesh_{tag}.npz'); t = c['verts'][c['faces']]
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); a = np.linalg.norm(n, axis=1); n /= a[:, None] + 1e-20
    d, i = tree.query(t.mean(1), 4)
    dots = (sn[owner[i]] * n[:, None]).sum(-1).max(1)
    flip = dots < -0.2
    edge = np.max([np.linalg.norm(t[:, k] - t[:, (k + 1) % 3], axis=1) for k in range(3)], 0)
    sliver = (a / 2) < 0.02 * edge ** 2          # area under 2 % of the longest edge squared
    np.save(f'work/flip_{tag}.npy', flip | sliver)
    print(tag, 'faces', len(t), 'flipped', int(flip.sum()), 'slivers', int(sliver.sum()))
    for k in np.flatnonzero(flip)[:8]:
        print('   flip at', t[k].mean(0).round(3), 'dot', round(float(dots[k]), 2), 'group', int(c['group'][k]))
s_t = st; sedge = np.max([np.linalg.norm(s_t[:, k] - s_t[:, (k + 1) % 3], axis=1) for k in range(3)], 0)
print('source slivers', int(((sa / 2) < 0.02 * sedge ** 2).sum()))
