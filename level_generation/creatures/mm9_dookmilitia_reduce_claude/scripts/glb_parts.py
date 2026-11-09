#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_dookmilitia.glb) from the creature project's final rest mesh
(work/final_tris.npz from dump_final.py: part, hand, lining, weapon, mat, graft_s per corner). Faces matched by centroid
after fitting the axis map and offset. Parts: 0 hands, 1 tunic, 2 old neck V, 3 sleeves, 5 pants, 6 boots, 7 skirt,
8 mantle, 9 belt, 10 buckle, 13 shoulder caps, 20 face, 21 helm/hood, 22 eyes, 30 sword, 31/32 linings.
Writes work/glb_parts.npz: per GLB face (primitives in order) mat, part, hand, lining, graft (max graft_s in (0,1)), src, cen."""
import sys, itertools
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(str(HERE / 'before' / 'mm9_dookmilitia.glb')))
P = [np.asarray(p['positions']) for p in m.primitives]; T = [np.asarray(p['triangles']) for p in m.primitives]
gc = np.vstack([p[t].mean(1) for p, t in zip(P, T)]); gmat = np.concatenate([np.full(len(t), i) for i, t in enumerate(T)])
d = np.load(HERE / 'work' / 'final_tris.npz')
nc = d['cen']
best = None
for perm in itertools.permutations(range(3)):
    for sg in itertools.product([1, -1], repeat=3):
        q = nc[:, perm] * sg
        q = q - np.median(q, 0) + np.median(gc, 0)
        dist, _ = cKDTree(gc).query(q[::7])
        s = np.median(dist)
        if best is None or s < best[0]: best = (s, perm, sg)
s, perm, sg = best; q = nc[:, perm] * np.array(sg)
off = np.median(gc, 0) - np.median(q, 0)
for _ in range(5):
    dist, nn = cKDTree(gc).query(q + off); off += np.median(gc[nn] - (q + off), 0)
dist, nn = cKDTree(q + off).query(gc)
print('MAP perm', perm, 'sign', sg, 'offset', np.round(off, 5), 'median d', np.median(dist), 'p99', np.percentile(dist, 99), 'max', dist.max())
g = d['graft_s']; graft = np.where((g > 1e-6) & (g < 0.999), g, 0).max(1)
mat = d['a_mat'][nn]
print('mat agreement', (mat == gmat).mean(), 'unique src', len(np.unique(nn)), 'of', len(gc))
out = dict(mat=gmat, part=d['a_part'][nn], hand=d['a_hand'][nn], lining=d['a_lining'][nn], graft=graft[nn],
           graft_any=((g > 1e-6).any(1))[nn], src=nn, cen=gc, dist=dist)
for p in np.unique(out['part']): print(p, (out['part'] == p).sum())
np.savez(HERE / 'work' / 'glb_parts.npz', **out)
