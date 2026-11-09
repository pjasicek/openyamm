#!/usr/bin/env python3
"""Every installed LOD0 triangle of the kept classes (head shell with the face, leaf cards; classes.npz) is present in the
candidate with the same corner positions, UVs and normals (bytes of the installed vertices). Usage: kept_exact.py <cand.glb>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
_, _, _, A = glbio.load(HERE / 'before' / 'mm9_greenman.glb', 'GreenMan'); _, _, _, B = glbio.load(sys.argv[1], 'GreenMan')
c = np.load(HERE / 'work' / 'classes.npz'); cls = c['cls']; names = [str(x) for x in c['names']]; off = 0
for name in ('GreenMan', 'GreenManHead'):
    a, b = A[name], B[name]; n = len(a['T']); cl = cls[off:off + n]; off += n
    key = lambda d, T: [tuple(sorted(tuple(np.r_[d['P'][v], d['UV'][v], d['N'][v]].round(7)) for v in t)) for t in T]
    bset = set(key(b, b['T'])); ka = key(a, a['T'])
    for k in np.unique(cl):
        idx = np.flatnonzero(cl == k); miss = sum(ka[i] not in bset for i in idx)
        print(f'{name} {names[k]:11s}: {len(idx)} installed faces, {len(idx) - miss} present exactly, {miss} changed')
