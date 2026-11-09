#!/usr/bin/env python3
"""Open edges (edges of one face, welded by position per primitive) of the installed LOD0 vs an mpqem step
(work/<mp>.npz): prints the count per primitive and the positions of open edges the step adds. Usage: open_edges.py <mp npz>"""
import sys
from pathlib import Path
from collections import Counter
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio  # noqa: E402
doc, b = bglbio.read(HERE / 'before' / 'mm9_peasantdm1.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantDM1' and 'mesh' in n)
d = np.load(HERE / 'work' / sys.argv[1])
for pr in bglbio.prims(doc, b, node['mesh']):
    P = pr['POSITION'].astype(float); _, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel()
    def opened(T):
        c = Counter()
        for t in w[T]:
            for a, b_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                c[(min(a, b_), max(a, b_))] += 1
        return {e for e, k in c.items() if k == 1}
    o0 = opened(pr['T']); o1 = opened(d[pr['material']].astype(int))
    rep = {}
    for i, x in enumerate(w):
        rep.setdefault(x, i)
    new = o1 - o0
    print(pr['material'], 'open', len(o0), '->', len(o1), 'new', len(new), 'closed', len(o0 - o1))
    for e in list(new)[:20]:
        print('   new', P[rep[e[0]]].round(3), P[rep[e[1]]].round(3))
