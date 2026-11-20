#!/usr/bin/env python3
"""Rest-pose two-way surface error per source group (drone: rigid, so the rest shape is what the clips show):
dense surface samples of source and candidate, nearest-sample distances, p99/max per group of the source face.
Usage: region_err.py <tag...>  (work/mesh_in.npz, work/groups.npy, work/keep.npy, work/mesh_<tag>.npz)"""
import sys
import numpy as np
from scipy.spatial import cKDTree
rng = np.random.default_rng(0)


def sample(v, f, per_m2=4e6):
    t = v[f]; a = np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1) / 2
    n = np.maximum(1, (a * per_m2).astype(int)); fi = np.repeat(np.arange(len(f)), n)
    b = rng.dirichlet((1, 1, 1), len(fi))
    return np.einsum('nk,nkc->nc', b, t[fi]), fi


s = np.load('work/mesh_in.npz'); g = np.load('work/groups.npy'); keep = np.load('work/keep.npy')
g = np.where(keep, -1, g)
sp, sfi = sample(s['verts'], s['faces'])
names = {-1: 'kept', 0: 'shell', 1: 'tubes', 2: 'plates', 3: 'chitin', 4: 'drum', 5: 'g5', 6: 'g6'}
for tag in sys.argv[1:]:
    c = np.load(f'work/mesh_{tag}.npz'); cp, cfi = sample(c['verts'], c['faces'])
    d1 = cKDTree(cp).query(sp)[0]                      # source -> candidate (lost shape)
    d2, near = cKDTree(sp).query(cp)                   # candidate -> source (bulges), attributed to the source face
    out = []
    for k in sorted(set(g.tolist())):
        e = np.r_[d1[g[sfi] == k], d2[g[sfi[near]] == k]] * 1000
        if len(e):
            out.append(f'{names.get(k, k)} p99 {np.percentile(e, 99):.2f} max {e.max():.2f}')
    e = np.r_[d1, d2] * 1000
    print(tag, len(c['faces']), 'all p99 %.2f max %.2f |' % (np.percentile(e, 99), e.max()), ' | '.join(out))
