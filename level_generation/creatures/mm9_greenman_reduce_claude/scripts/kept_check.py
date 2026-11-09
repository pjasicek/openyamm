#!/usr/bin/env python3
"""Every installed LOD0 face of the kept classes (work/glb_sets_<tag>.npz keep, plus extra classes) is present in the candidate
with the same corner attributes (position, normal, UV, joints, weights, compared as bytes-equal floats). Per class counts.
Usage: kept_check.py <candidate.glb> <sets tag> [extra cls,...]"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
cand, tag = sys.argv[1:3]; extra = [int(c) for c in sys.argv[3].split(',')] if len(sys.argv) > 3 else []
_, _, _, A = glbio.load(HERE / 'before' / 'mm9_greenman.glb', 'GreenMan'); _, _, _, B = glbio.load(cand, 'GreenMan')
s = np.load(HERE / 'work' / f'glb_sets_{tag}.npz'); keep = s['keep'] | np.isin(s['cls'], extra); cls = s['cls']
off = np.cumsum([0] + [len(d['T']) for d in A.values()])
for k, name in enumerate(A):
    a, b = A[name], B[name]
    key = lambda d: np.concatenate([d['P'], d['N'], d['UV'], d['J'], d['W']], 1)
    ka = [tuple(r) for r in key(a)]; kb = {tuple(r): i for i, r in enumerate(key(b))}
    fb = {tuple(sorted(t)) for t in b['T'].tolist()}
    sel = np.flatnonzero(keep[off[k]:off[k + 1]])
    miss = {}
    for f in sel:
        ids = [kb.get(ka[v]) for v in a['T'][f]]
        if None in ids or tuple(sorted(ids)) not in fb:
            c = int(cls[off[k] + f]); miss[c] = miss.get(c, 0) + 1
    present = {int(c): int((cls[off[k]:off[k + 1]][sel] == c).sum()) for c in np.unique(cls[off[k]:off[k + 1]][sel])}
    print(name, 'kept faces', len(sel), 'by class', present, 'missing', miss or 0)
