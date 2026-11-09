#!/usr/bin/env python3
"""Largest rest-pose misses of a decimated mesh (source vertex -> candidate surface), clustered (5 cm): position,
distance, region label. Used to pick spot locks for thin features a group ratio loses (head 2's mane spikes).
Usage: rest_misses.py <groups.npy> <keep.npy> <tag> [threshold mm, default 15]"""
import sys
import numpy as np
from scipy.spatial import cKDTree
groups, keep, tag = np.load(sys.argv[1]), np.load(sys.argv[2]), sys.argv[3]
T = float(sys.argv[4]) / 1000 if len(sys.argv) > 4 else .015
s = np.load('work/mesh_in.npz'); sv, sf = s['verts'], s['faces']; c = np.load(f'work/mesh_{tag}.npz'); cv, cf = c['verts'], c['faces']
t = cv[cf]; a = np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1) / 2
n = np.clip((a / .0015 ** 2).astype(int), 1, 400); idx = np.repeat(np.arange(len(cf)), n)
r = np.random.default_rng(0).random((len(idx), 2)); fl = r.sum(1) > 1; r[fl] = 1 - r[fl]
p = np.concatenate([t[idx, 0] + r[:, :1] * (t[idx, 1] - t[idx, 0]) + r[:, 1:] * (t[idx, 2] - t[idx, 0]), cv])
d, _ = cKDTree(p).query(sv)
vlab = np.full(len(sv), -9); vlab[sf.reshape(-1)] = np.repeat(np.where(keep, -1, groups), 3)
order = np.argsort(-d); taken = []
for i in order:
    if d[i] < T:
        break
    if any(np.linalg.norm(sv[i] - sv[j]) < .05 for j in taken):
        continue
    taken.append(i); print(f'MISS {d[i] * 1000:.1f} mm label {vlab[i]} at {",".join(f"{x:.3f}" for x in sv[i])}')
