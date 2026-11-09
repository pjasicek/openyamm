#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_lesserdemon.glb) from the creature project's per-face dump
(../mm9_stage1demon_claude/work/faces.npz: part per face; parts 0 skin, 1 armour shells, 2 small pieces, 4 tail,
10 head shell, 12 teeth, 13 eyes, 14 tongue, others talons/palms). Faces are matched by centroid after fitting the axis
map and offset; faces not matched (the pass-2 crotch-shard removal and later edits) get -1.
Writes work/glb_parts.npz: per GLB face (LesserDemon primitive then LesserDemonHead) mat, part, centroid, match dist."""
import sys, itertools
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio
doc, b = bglbio.read(HERE / 'before' / 'mm9_lesserdemon.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'LesserDemon' and 'mesh' in n)
pr = bglbio.prims(doc, b, node['mesh'])
gc = np.vstack([p['POSITION'][p['T']].mean(1) for p in pr]); gmat = np.concatenate([np.full(len(p['T']), i) for i, p in enumerate(pr)])
d = np.load(HERE.parent / 'mm9_stage1demon_claude' / 'work' / 'faces.npz')
nc = d['co'].astype(np.float64).mean(1)
best = None
for perm in itertools.permutations(range(3)):
    for sg in itertools.product([1, -1], repeat=3):
        q = nc[:, perm] * sg; o = np.median(gc, 0) - np.median(q, 0)
        for _ in range(3):
            dist, nn = cKDTree(gc).query(q[::5] + o); o += np.median(gc[nn] - (q[::5] + o), 0)
        s = np.mean(np.minimum(dist, 0.05))
        if best is None or s < best[0]: best = (s, perm, sg, o)
s, perm, sg, off = best; q = nc[:, perm] * np.array(sg) + off
dist, nn = cKDTree(q).query(gc)
# UV match (UVs never changed after uv_demon.py; positions did: horns, soles, sunk pieces): per material, UV centroid
for m in (0, 1):
    sel = np.flatnonzero(gmat == m); src = np.flatnonzero((d['head'] > 0) == (m == 1))
    uv = (d['uvh'] if m else d['uvb'])[src].astype(np.float64); uv[..., 1] = 1 - uv[..., 1]
    guv = pr[m]['TEXCOORD_0'][pr[m]['T']].astype(np.float64)
    # centroid plus the sorted corners, so faces sharing a centroid by symmetry do not swap
    key = lambda a: np.concatenate([a.mean(1), np.sort(a.reshape(len(a), -1), 1)], 1)
    du, k = cKDTree(key(uv)).query(key(guv))
    print('UV match mat', m, 'median', np.median(du), 'p99', np.percentile(du, 99), 'max', du.max(), 'over 1e-4', int((du > 1e-4).sum()))
    good = du < 1e-4
    dist[sel[good]] = 0; nn[sel[good]] = src[k[good]]
print('MAP perm', perm, 'sign', sg, 'offset', np.round(off, 4), 'median d', np.median(dist), 'p99', np.percentile(dist, 99), 'max', dist.max())
part = d['part'][nn].copy(); part[dist > 1e-3] = -1
hd = d['head'][nn]
print('head agreement', ((hd > 0) == (gmat == 1))[dist <= 1e-3].mean(), 'unmatched', int((dist > 1e-3).sum()))
for m in (0, 1):
    u, c = np.unique(part[gmat == m], return_counts=True); print('mat', m, dict(zip(u.tolist(), c.tolist())))
np.savez(HERE / 'work' / 'glb_parts.npz', mat=gmat, part=part, src=nn, cen=gc, dist=dist)
