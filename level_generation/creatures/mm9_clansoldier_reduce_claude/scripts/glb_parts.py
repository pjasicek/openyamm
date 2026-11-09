#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_clansoldier.glb) from the creature project's final rest mesh
(work/final_faces.npz, dump_final.py of ../mm9_clansoldier_claude/work/final_v1.blend: part per face 1 coat, 2 neck, 4 hand,
5 pants, 6 boot, 7 skirt, 9 sash, 20 face/neck, 21 helmet, 22 eyes, 30 weapons, ...; hand, lining, weapon flags). Faces are
matched by centroid after fitting the axis map and offset (from the Lizard-Orc's glb_parts.py).
Writes work/glb_parts.npz: per GLB face (primitives in order) mat, part, hand, lining, weapon, src, cen (GLB rest)."""
import sys, itertools
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(str(HERE / 'before' / 'mm9_clansoldier.glb')))
PR = [p for p in m.primitives if p['node'] == m.primitives[0]['node']][:4]
P = [np.asarray(p['positions']) for p in PR]; T = [np.asarray(p['triangles']).reshape(-1, 3) for p in PR]
gc = np.vstack([p[t].mean(1) for p, t in zip(P, T)]); gmat = np.concatenate([np.full(len(t), i) for i, t in enumerate(T)])
d = np.load(HERE / 'work' / 'final_faces.npz')
nc = d['co'].mean(1)
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
out = dict(mat=gmat, src=nn, cen=gc, dist=dist)
for k in ('part', 'hand', 'lining', 'weapon', 'mat'):
    out[k if k != 'mat' else 'fmat'] = d['f_' + k][nn]
print('unique src', len(np.unique(nn)), 'of', len(gc))
for p in np.unique(out['part']):
    sel = out['part'] == p
    print('part', p, int(sel.sum()), 'by prim', np.bincount(gmat[sel], minlength=4), 'lining', int(out['lining'][sel].astype(bool).sum()), 'hand', int(out['hand'][sel].astype(bool).sum()))
print('fmat vs prim', [(a, b, int(((out['fmat'] == a) & (gmat == b)).sum())) for a in np.unique(out['fmat']) for b in range(4) if ((out['fmat'] == a) & (gmat == b)).any()])
np.savez(HERE / 'work' / 'glb_parts.npz', **out)
