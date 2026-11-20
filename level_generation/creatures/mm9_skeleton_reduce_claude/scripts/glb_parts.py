#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_skeleton.glb) from the creature project's final master dump
(../mm9_skeleton_claude/work/faces.npz: pid (Meshy part) per face, head, lining, scim flags, face corners fco).
Faces are matched by centroid after fitting the axis map (permutation/sign) and offset.
Writes work/glb_parts.npz: per GLB face (Skel, SkelHead, Dagger primitives in order) pid, lining, head, src face, dist."""
import sys, itertools
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(str(HERE / 'before' / 'mm9_skeleton.glb')))
P = [np.asarray(p['positions']) for p in m.primitives]; T = [np.asarray(p['triangles']) for p in m.primitives]
gc = np.vstack([p[t].mean(1) for p, t in zip(P, T)]); gmat = np.concatenate([np.full(len(t), i) for i, t in enumerate(T)])
d = np.load(HERE.parent / 'mm9_skeleton_claude' / 'work' / 'faces.npz')
nc = d['fco'].mean(1)
best = None
for perm in itertools.permutations(range(3)):
    for sg in itertools.product([1, -1], repeat=3):
        q = nc[:, perm] * sg
        for sc in (1.0,):
            o = np.median(gc, 0) - np.median(q, 0)
            dist, _ = cKDTree(gc).query(q[::5] + o)
            s = np.mean(dist)
            if best is None or s < best[0]: best = (s, perm, sg, o)
s, perm, sg, off = best; q = nc[:, perm] * np.array(sg); off = off.copy()
for _ in range(8):
    dist, nn = cKDTree(gc).query(q + off); off += np.median(gc[nn] - (q + off), 0)
dist, nn = cKDTree(q + off).query(gc)
print('MAP perm', perm, 'sign', sg, 'offset', np.round(off, 4), 'median d', np.median(dist), 'p99', np.percentile(dist, 99), 'max', dist.max())
print('unique src', len(np.unique(nn)), 'of', len(gc))
np.savez(HERE / 'work' / 'glb_parts.npz', mat=gmat, pid=d['pid'][nn], lining=d['lining'][nn], head=d['head'][nn],
         scim=d['scim'][nn], src=nn, cen=gc, dist=dist)
for k in ('lining', 'head', 'scim'):
    print(k, [(i, int((d[k][nn][gmat == i] > 0).sum())) for i in range(3)])
