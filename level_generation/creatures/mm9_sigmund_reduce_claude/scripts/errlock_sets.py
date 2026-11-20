#!/usr/bin/env python3
"""err_lock.py's extra faces (mesh_in faces: <locked .npy> minus <base .npy>) carried into a GLB set (glb_sets.py's centroid
match). Usage: errlock_sets.py <in set tag> <base keep .npy> <locked keep .npy> <out set tag> -> work/glb_sets_<out>.npz"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
src, base, locked, dst = sys.argv[1:5]
d = np.load(HERE / 'work' / 'mesh_in.npz'); V, F = d['verts'], d['faces']
g = np.load(HERE / 'work' / 'glb_parts.npz')
gc = g['cen'][:, [0, 2, 1]] * [1, -1, 1]; gc[:, 2] += V[:, 2].min()
dist, nn = cKDTree(V[F].mean(1)).query(gc); assert dist.max() < 1e-4, dist.max()
extra = (np.load(HERE / base) ^ np.load(HERE / locked))[nn]
S = dict(np.load(HERE / 'work' / f'glb_sets_{src}.npz')); new = extra & ~S['keep']
S['keep'] = S['keep'] | extra; S['group'] = np.where(S['keep'], 0, S['group'])
np.savez(HERE / 'work' / f'glb_sets_{dst}.npz', **S)
print('SET', dst, 'keep', int(S['keep'].sum()), f'(+{int(new.sum())})', 'groups', {int(k): int((S['group'][~S['keep']] == k).sum()) for k in np.unique(S['group'][~S['keep']])})
