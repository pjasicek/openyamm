#!/usr/bin/env python3
"""Sets for mpqem.py per installed GLB LOD0 face (Monk_A, then MonkHead) from the welded-mesh sets of the first pass
(work/keep_<..>.npy, work/groups_c.npy on work/mesh_in.npz faces), matched by rest centroid (work/glb_parts.npz holds the GLB
face centroids). GLB faces with no welded counterpart (4 degenerate body faces) and all of MonkHead are kept. Linings are
not cut (they are kept faces), so lining/lined are all False. Groups: 2 belt, 3 knots, 4 hands.
Usage: glb_sets.py <keep npy> <tag> -> work/glb_sets_<tag>.npz"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
W = Path(__file__).resolve().parents[1] / 'work'
keep_w = np.load(sys.argv[1]).astype(bool); group_w = np.load(W / 'groups_c.npy').astype(int)
d = np.load(W / 'mesh_in.npz'); fc = d['verts'][d['faces']].mean(1)
g = np.load(W / 'glb_parts.npz'); gc = g['cen'][:, [0, 2, 1]] * [1, -1, 1]
dist, nn = cKDTree(fc).query(gc)
hit = dist < 1e-4
keep = np.where(hit, keep_w[nn], True) | (g['mat'] == 1)
group = np.where(hit, group_w[nn], 0); group[keep] = 0
z = np.zeros(len(keep), bool)
np.savez(W / f'glb_sets_{sys.argv[2]}.npz', keep=keep, group=group, lining=z, lined=z)
print('SETS', sys.argv[2], 'faces', len(keep), 'unmatched', int((~hit).sum()), 'keep', int(keep.sum()), 'groups', np.bincount(group[~keep]))
