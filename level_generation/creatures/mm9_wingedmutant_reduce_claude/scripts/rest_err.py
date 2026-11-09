#!/usr/bin/env python3
"""Rest-pose two-way surface error between work/mesh_in.npz and work/mesh_r<tag>.npz (closest point on the 24 nearest
triangles by centroid). Prints percentiles and the worst source vertices with their labels; saves work/rest_err_<tag>.npy
(per source vertex). Usage: rest_err.py <tag> [n]"""
import sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from uv_weights_lib import closest_on_tris


def dist_to(p, v, f, k=24):
    t = cKDTree(v[f].mean(1)); _, cand = t.query(p, k); tri = v[f[cand]]
    _, d = closest_on_tris(np.repeat(p[:, None], k, 1), tri[:, :, 0], tri[:, :, 1], tri[:, :, 2])
    return d.min(1)


tag = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 15
s = np.load('work/mesh_in.npz'); d = np.load(f'work/mesh_r{tag}.npz'); S = np.load('work/sets.npz')
sw = np.load('work/src_weights.npz'); names = sw['names']; W = sw['weights']
a = dist_to(s['verts'], d['verts'], d['faces']); b = dist_to(d['verts'], s['verts'], s['faces'])
print('src->cand mm p50/p99/max', np.percentile(a, [50, 99, 100]).round(5) * 1000, ' cand->src', np.percentile(b, [50, 99, 100]).round(5) * 1000)
np.save(f'work/rest_err_{tag}.npy', a)
vg = np.zeros(len(s['verts']), int); vg[s['faces'][:, 0]] = S['group']
for i in np.argsort(-a)[:N]:
    print(f'  {a[i]*1000:6.1f} mm v{i} {s["verts"][i].round(3)} {names[W[i].argmax()]} group {vg[i]}')
