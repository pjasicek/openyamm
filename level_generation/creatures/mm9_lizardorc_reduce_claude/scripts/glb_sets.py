#!/usr/bin/env python3
"""mesh_in face sets (make_sets.py: keep_<k>.npy, groups_<g>.npy on work/mesh_in.npz) -> per GLB LOD0 face (primitives in
order) for mpqem.py: work/glb_sets_<tag>.npz with keep, group, lining (none), lined (none). GLB faces are matched to mesh_in
faces by centroid (glTF -> Blender: x, -z, y); the degenerate faces Blender dropped (head and cutlass, both kept whole) are kept.
Extra keeps: EXTRA=<.npy per mesh_in face>[,...]. Usage: glb_sets.py <tag> <keep .npy> <groups .npy>"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
tag, kf, gf = sys.argv[1:4]
d = np.load(HERE / 'work' / 'mesh_in.npz'); fc = d['verts'][d['faces']].mean(1)
keep_mi = np.load(kf).astype(bool); grp_mi = np.load(gf)
for e in [x for x in os.environ.get('EXTRA', '').split(',') if x]:
    keep_mi |= np.load(e).astype(bool)
g = np.load(HERE / 'work' / 'glb_parts.npz'); gc = g['cen'][:, [0, 2, 1]] * [1, -1, 1]
dist, nn = cKDTree(fc).query(gc); hit = dist < 1e-5
keep = np.where(hit, keep_mi[nn], True); group = np.where(hit, grp_mi[nn], 0)
group[keep] = 0
print('GLB faces', len(gc), 'unmatched (kept)', int((~hit).sum()), 'keep', int(keep.sum()), 'groups', np.bincount(group[~keep]).tolist())
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=np.zeros(len(gc), bool), lined=np.zeros(len(gc), bool))
