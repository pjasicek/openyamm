#!/usr/bin/env python3
"""UV drift per class at rest: points on the candidate's faces (barycentric grid) against the nearest point of the installed
surface (dense grid, same class, facing the same way): the difference of their UVs in texels of a 2048 map. A texture motif
on a cut piece shifts by this much (the medallion rosette). Usage: uv_drift.py <candidate glb> <sets tag> [class,...]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
cand, tag = sys.argv[1:3]; want = sys.argv[3].split(',') if len(sys.argv) > 3 else None
_, _, _, S = glbio.load(HERE / 'before' / 'mm9_honkm.glb', 'HonkM'); _, _, _, Cd = glbio.load(cand, 'HonkM')
s = np.load(HERE / 'work' / f'glb_sets_{tag}.npz'); CN = json.load(open(HERE / 'work' / 'classes.json'))['names']
def grid(k):
    i, j = np.meshgrid(np.arange(k + 1), np.arange(k + 1)); m = i + j <= k
    return np.stack([i[m], j[m], k - i[m] - j[m]], 1) / k
gs, gc = grid(16), grid(6); off = 0
for name in ('HonkM_A', 'HonkMHead'):
    A, B = S[name], Cd[name]; n = len(A['T']); cls = s['cls'][off:off + n]; off += n
    key = lambda D: {tuple(sorted(map(tuple, D['P'][t].round(6)))): f for f, t in enumerate(D['T'])}
    ka = key(A)
    for c in np.unique(cls):
        if want and CN[c] not in want:
            continue
        fs = np.flatnonzero(cls == c)
        sp = np.einsum('sk,fkc->fsc', gs, A['P'][A['T'][fs]]).reshape(-1, 3)
        su = np.einsum('sk,fkc->fsc', gs, A['UV'][A['T'][fs]]).reshape(-1, 2)
        # candidate faces of this class: those whose vertices are all vertices of this class's source faces
        vs = {tuple(p) for p in A['P'][A['T'][fs]].reshape(-1, 3).round(6)}
        cf = [f for f, t in enumerate(B['T']) if all(tuple(p) in vs for p in B['P'][t].round(6))]
        new = [f for f in cf if tuple(sorted(map(tuple, B['P'][B['T'][f]].round(6)))) not in ka]
        if not new:
            continue
        cp = np.einsum('sk,fkc->fsc', gc, B['P'][B['T'][new]]).reshape(-1, 3)
        cu = np.einsum('sk,fkc->fsc', gc, B['UV'][B['T'][new]]).reshape(-1, 2)
        d, q = cKDTree(sp).query(cp)
        dt = np.linalg.norm(cu - su[q], axis=1) * 2048
        print(f'{name:10s} {CN[c]:10s} new faces {len(new):5d}  UV drift texels p50 {np.median(dt):6.2f} p95 {np.percentile(dt, 95):6.2f} '
              f'max {dt.max():6.2f}  (surface gap p95 {np.percentile(d, 95) * 1000:.2f} mm)')
