#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_lizardorc.glb) from the creature project's final rest mesh
(../mm9_lizardorc_claude/work/final.npz: part per vertex: 0 hide, 1 head skin, 3/4 teeth, 7 tongue, 8+ armour shells,
30 cutlass; ringv = neck ring vertices). Faces are matched by centroid after fitting the axis map and offset
(from mm9_wyrdold_reduce_claude/scripts/glb_parts.py). Writes work/glb_parts.npz: per GLB face (primitives in order)
mat, part, ring (any ring vertex), src (final.npz face), cen (GLB rest)."""
import sys, itertools
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(str(HERE / 'before' / 'mm9_lizardorc.glb')))
P = [np.asarray(p['positions']) for p in m.primitives]; T = [np.asarray(p['triangles']) for p in m.primitives]
gc = np.vstack([p[t].mean(1) for p, t in zip(P, T)]); gmat = np.concatenate([np.full(len(t), i) for i, t in enumerate(T)])
d = np.load(HERE.parent / 'mm9_lizardorc_claude' / 'work' / 'final.npz', allow_pickle=True)
nc = d['co'][d['tri']].mean(1)
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
part = d['part'][d['tri'][:, 0]][nn]; mat = d['mat'][nn]; ring = d['ringv'][d['tri']].any(1)[nn]
print('mat agreement', (mat == gmat).mean(), 'unique src', len(np.unique(nn)), 'of', len(gc))
for p in np.unique(part):
    print(p, (part == p).sum())
np.savez(HERE / 'work' / 'glb_parts.npz', mat=gmat, part=part, ring=ring, src=nn, cen=gc, dist=dist)
