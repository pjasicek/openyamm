#!/usr/bin/env python3
"""Put installed LOD0 faces of the given classes (work/glb_sets_<SETS>.npz cls) back into an mpqem result: every face of those
classes is re-emitted as installed, and the result's faces with all corners on those classes' vertices are dropped (each group
is cut on its own, so the rest of the result is the same as an mpqem run with the class kept). Yanmir: the crown band (cls 24),
whose knotwork medallions slid along the band at b r60. Usage: splice_keep.py <in npz> <out npz> <sets tag> <cls,...>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
src, dst, tag, cl = sys.argv[1:5]; cl = [int(c) for c in cl.split(',')]
doc, b, nd, D = glbio.load(HERE / 'before' / 'mm9_yanmir.glb', 'Yanmir')
s = np.load(HERE / 'work' / f'glb_sets_{tag}.npz'); cls = s['cls']
off = np.cumsum([0] + [len(d['T']) for d in D.values()])
mp = dict(np.load(HERE / 'work' / src))
for k, (name, d) in enumerate(D.items()):
    sel = np.isin(cls[off[k]:off[k + 1]], cl)
    if not sel.any():
        continue
    T0 = d['T'][sel]; vs = np.zeros(len(d['P']), bool); vs[T0.ravel()] = True
    T = mp[name]; drop = vs[T].all(1)
    mp[name] = np.concatenate([T[~drop], T0])
    print(name, 'dropped', int(drop.sum()), 'restored', len(T0), '->', len(mp[name]))
np.savez(HERE / 'work' / dst, **mp); print('TOTAL', sum(len(v) for v in mp.values()))
