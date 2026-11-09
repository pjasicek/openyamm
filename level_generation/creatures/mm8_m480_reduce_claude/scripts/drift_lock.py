"""Lock the source faces around drifted faces (texture_drift.py > THRESH on faces over REA_LOCK_AREA m2, default 3 cm2; smaller ones are invisible except as dark slivers) so the next ladder keeps them exactly.
Usage: drift_lock.py <base keep .npy> <out .npy> <tag> ...  (radius REA_LOCK_R metres, default 0.03)"""
import os, sys
import numpy as np
from scipy.spatial import cKDTree
base, out, tags = sys.argv[1], sys.argv[2], sys.argv[3:]
R = float(os.environ.get('REA_LOCK_R', '0.03')); THRESH = 40
src = np.load('work/mesh_in.npz'); scen = src['verts'][src['faces']].mean(1)
keep = np.load(base).copy(); tree = cKDTree(scen); n0 = int(keep.sum())
for t in tags:
    d = np.load(f'work/mesh_{t}.npz'); drift = np.load(f'work/drift_{t}.npy')
    tri = d['verts'][d['faces']]
    area = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) / 2
    for i in np.where((drift > THRESH) & (area > float(os.environ.get('REA_LOCK_AREA', '3e-4'))))[0]:
        for p in [*tri[i], tri[i].mean(0)]:
            keep[tree.query_ball_point(p, R)] = True
np.save(out, keep); print('LOCK', n0, '->', int(keep.sum()), 'faces kept')
