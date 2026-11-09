#!/usr/bin/env python3
"""Targeted drift lock: source faces within REA_LOCK_R (default 2 cm) of reduced faces that drifted, where drifted
means texture_drift.py > 25 on the face region (any size: the grey face is seen up close) or > 40 on faces over 3 cm2
elsewhere. Usage: face_lock.py <base keep .npy> <out .npy> <tag> ..."""
import os, sys
import numpy as np
from scipy.spatial import cKDTree
base, out, tags = sys.argv[1], sys.argv[2], sys.argv[3:]
R = float(os.environ.get('REA_LOCK_R', '0.02'))
src = np.load('work/mesh_in.npz'); scen = src['verts'][src['faces']].mean(1); g = np.load('work/groups_bh.npy')
keep = np.load(base).copy(); tree = cKDTree(scen); n0 = int(keep.sum())
for t in tags:
    d = np.load(f'work/mesh_{t}.npz'); drift = np.load(f'work/drift_{t}.npy')
    tri = d['verts'][d['faces']]; cen = tri.mean(1)
    area = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) / 2
    grp = g[tree.query(cen)[1]]
    hit = ((grp == 1) & (drift > 25)) | ((drift > 40) & (area > 3e-4))
    for i in np.where(hit)[0]:
        for p in [*tri[i], cen[i]]:
            keep[tree.query_ball_point(p, R)] = True
np.save(out, keep); print('LOCK', n0, '->', int(keep.sum()), 'faces kept')
