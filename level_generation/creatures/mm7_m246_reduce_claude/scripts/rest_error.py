#!/usr/bin/env python3
"""Rest-pose geometry error of a decimated mesh (work/mesh_r<NN>.npz) against the source (work/mesh_in.npz), both
directions, by dense surface samples (2 mm). Prints p95/p99/max per region label (work/groups_<set>.npy) and saves the
per-source-face error to work/rest_err_<NN>.npy for label_view.py. Usage: rest_error.py <NN> <set>"""
import sys
import numpy as np
from scipy.spatial import cKDTree
tag, gset = sys.argv[1], sys.argv[2]
s = np.load('work/mesh_in.npz'); c = np.load(f'work/mesh_r{tag}.npz'); g = np.load(f'work/groups_{gset}.npy')


def samples(v, f, step=0.002):
    pts, fid = [], []
    for i, t in enumerate(v[f]):
        n = int(max(np.linalg.norm(t[1] - t[0]), np.linalg.norm(t[2] - t[0]), np.linalg.norm(t[2] - t[1])) / step) + 1
        a, b = np.meshgrid(np.arange(n + 1), np.arange(n + 1)); m = a + b <= n
        a, b = a[m] / n, b[m] / n
        pts.append(t[0] + a[:, None] * (t[1] - t[0]) + b[:, None] * (t[2] - t[0])); fid.append(np.full(len(a), i))
    return np.concatenate(pts), np.concatenate(fid)


sp, sf = samples(s['verts'], s['faces']); cp, cf = samples(c['verts'], c['faces'])
d_sc = cKDTree(cp).query(sp)[0]; d_cs, nn = cKDTree(sp).query(cp)
fe = np.zeros(len(s['faces'])); np.maximum.at(fe, sf, d_sc); np.maximum.at(fe, sf[nn], d_cs)
np.save(f'work/rest_err_{tag}.npy', fe)
print('REST', tag, 'src->cand p99 %.2f max %.2f mm | cand->src p99 %.2f max %.2f mm' % (
    np.percentile(d_sc, 99) * 1e3, d_sc.max() * 1e3, np.percentile(d_cs, 99) * 1e3, d_cs.max() * 1e3))
for k in np.unique(g):
    e = fe[g == k] * 1e3
    print(f'  group {k:2d} faces {len(e):5d} p95 {np.percentile(e, 95):6.2f} p99 {np.percentile(e, 99):6.2f} max {e.max():6.2f} mm')
