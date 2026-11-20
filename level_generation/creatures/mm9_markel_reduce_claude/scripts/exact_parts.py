#!/usr/bin/env python3
"""Every installed triangle of the kept parts present exactly in a candidate (vertex position + UV + normal + joints + weights,
per corner): PeasantM1d: face shell (20), eyes/mouth (22), every kept face. Usage: exact_parts.py <candidate.glb> [set tag, default a]"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
_, _, _, S = glbio.load(HERE / 'before' / 'mm9_peasantm1.glb', 'PeasantM1'); _, _, _, C = glbio.load(sys.argv[1], 'PeasantM1')
g = np.load(HERE / 'work' / 'glb_parts.npz'); st = np.load(HERE / 'work' / f"glb_sets_{sys.argv[2] if len(sys.argv) > 2 else 'a'}.npz")
PR = ['PeasantM1_A', 'PeasantM1Head']


def keys(D, T):
    a = np.concatenate([D['P'], D['UV'], D['N'], D['J'], D['W']], 1)
    k = [tuple(np.round(a[t], 6).ravel()) for t in T]
    return k


for i, n in enumerate(PR):
    sl = slice(g['foff'][i], g['foff'][i + 1])
    ck = set(keys(C[n], C[n]['T']))
    for lab, m in (('face shell', g['part'][sl] == 20), ('eyes/mouth', g['part'][sl] == 22), ('all kept', st['keep'][sl])):
        if not m.any():
            continue
        sk = keys(S[n], S[n]['T'][m])
        miss = sum(1 for k in sk if k not in ck)
        print(f'{n:12s} {lab:10s} installed {m.sum():5d} missing in candidate {miss}')
