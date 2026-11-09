#!/usr/bin/env python3
"""Every kept-exact class triangle (Mummy: face, eyes, strips) of the installed LOD0 is in the candidate with
byte-identical corner attributes (position, normal, UV, joints, weights). Usage: face_exact.py <candidate.glb> <sets tag>"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
cand, tag = sys.argv[1:3]
_, _, _, S = glbio.load(HERE / 'before' / 'mm9_mummy.glb', 'Mummy'); _, _, _, C = glbio.load(cand, 'Mummy')
s = np.load(HERE / 'work' / f'glb_sets_{tag}.npz'); CLS = json.load(open(HERE / 'work' / 'classes.json'))['names']
off = 0
for name in ('Mummy', 'MummyHead'):
    T = S[name]['T']; cls = s['cls'][off:off + len(T)]; off += len(T)
    def keys(D):
        V = np.concatenate([D['P'], D['N'], D['UV'], D['J'], D['W']], 1)
        return {tuple(np.round(V[t].ravel(), 7)) for t in D['T']}
    have = keys(C[name])
    V = np.concatenate([S[name]['P'], S[name]['N'], S[name]['UV'], S[name]['J'], S[name]['W']], 1)
    for c in ('face', 'eyes', 'strips'):
        sel = cls == CLS.index(c)
        if sel.any():
            miss = sum(tuple(np.round(V[t].ravel(), 7)) not in have for t in T[sel])
            print(f'{name:13s} {c:6s} {int(sel.sum()):5d} triangles, missing or changed {miss}')
