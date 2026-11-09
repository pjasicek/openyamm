#!/usr/bin/env python3
"""Every kept face of the sets (face skin, eyes/mouth, collar, ...) present in the candidate's LOD0 with the same vertex bytes:
compares triangles as sorted triples of (position, UV, normal, joints, weights) per primitive.
Usage: face_exact.py <candidate glb> <sets tag>"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
cand, tag = sys.argv[1:3]
_, _, _, S = glbio.load(HERE / 'before' / 'mm9_honkm.glb', 'HonkM'); _, _, _, Cd = glbio.load(cand, 'HonkM')
s = np.load(HERE / 'work' / f'glb_sets_{tag}.npz'); CN = json.load(open(HERE / 'work' / 'classes.json'))['names']
off = 0
for name in ('HonkM_A', 'HonkMHead'):
    def keys(D):
        V = np.concatenate([D['P'], D['UV'], D['N'], D['J'], D['W']], 1).round(6)
        return [tuple(sorted(map(tuple, V[t]))) for t in D['T']]
    ks = keys(S[name]); kc = set(keys(Cd[name])); n = len(ks)
    cls = s['cls'][off:off + n]; keep = s['keep'][off:off + n]
    for c in np.unique(cls):
        sel = np.flatnonzero((cls == c) & keep)
        miss = sum(ks[i] not in kc for i in sel)
        print(f'{name:10s} {CN[c]:10s} kept {len(sel):5d} missing in candidate {miss}')
    off += n
