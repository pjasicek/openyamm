#!/usr/bin/env python3
"""(Krohn copy of Yanmir's) Put installed LOD0 faces of the given classes (work/glb_sets_<SETS>.npz cls) back into an mpqem result: every face of those
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
doc, b, nd, D = glbio.load(HERE / 'before' / 'mm9_krohn.glb', 'Krohn')
s = np.load(HERE / 'work' / f'glb_sets_{tag}.npz'); cls = s['cls']
off = np.cumsum([0] + [len(d['T']) for d in D.values()])
mp = dict(np.load(HERE / 'work' / src))
for k, (name, d) in enumerate(D.items()):
    sel = np.isin(cls[off[k]:off[k + 1]], cl)
    if not sel.any():
        continue
    T0 = d['T'][sel]; vs = np.zeros(len(d['P']), bool); vs[T0.ravel()] = True
    T = mp[name]; drop = vs[T].all(1)
    # Krohn: faces of other classes kept byte-exact (the shaft grip band, rims beside the plates) stay
    other = {tuple(sorted(t)) for t in d['T'][~sel].tolist()}
    keep_other = np.array([tuple(sorted(t)) in other for t in T.tolist()])
    print(name, 'all-corner faces', int(drop.sum()), 'of them installed faces of other classes', int((drop & keep_other).sum()))
    drop &= ~keep_other
    new = np.concatenate([T[~drop], T0])
    # Krohn: a dropped face of another group whose corners all sit on the class's vertices leaves a hole; put back every dropped
    # face that has an edge the spliced mesh no longer closes (position-welded open edges)
    from collections import Counter
    _, w = np.unique(np.round(d['P'], 6), axis=0, return_inverse=True); w = w.ravel()
    ed = lambda TT: Counter(tuple(sorted((a, c))) for t in w[TT] for a, c in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])))
    e0, e1 = ed(T), ed(new)
    holes = {k for k, v in e1.items() if v == 1 and e0.get(k) == 2}
    back = [f for f in np.flatnonzero(drop) if any(tuple(sorted((a, c))) in holes for t in [w[T[f]]] for a, c in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])))]
    if back:
        new = np.concatenate([new, T[back]]); print(name, 'put back', len(back), 'dropped faces of other groups (holes)')
    mp[name] = new
    print(name, 'dropped', int(drop.sum()), 'restored', len(T0), '->', len(mp[name]))
np.savez(HERE / 'work' / dst, **mp); print('TOTAL', sum(len(v) for v in mp.values()))
