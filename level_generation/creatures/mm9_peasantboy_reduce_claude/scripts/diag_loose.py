#!/usr/bin/env python3
"""Diagnostic: where the unpaired one-texel faces (not the tube) are, and whether each vertex has a same-weight vertex in front
of it (any distance up to 25 mm, any direction). Read-only."""
import sys
from pathlib import Path
import numpy as np
from collections import defaultdict
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantboy.glb', 'PeasantBoy')
s = np.load(HERE / 'work' / 'glb_sets_a.npz'); tw = np.load(HERE / 'work' / 'twins.npz')
B = D['PeasantBoy_A']; P, T, Jt, Wt = B['P'], B['T'], B['J'], B['W']; nb = len(T)
part = s['part'][:nb]; zero = tw['zero_PeasantBoy_A']; lin = tw['lining'][:nb]
_, tp = np.unique(np.round(P, 6), axis=0, return_inverse=True); tp = tp.ravel()
linp = np.zeros(tp.max() + 1, bool); linp[tp[T[lin].ravel()]] = True
strip = ~lin & (part != 6) & linp[tp[T]].any(1)
loose = zero & ~lin & ~strip & (part != 6)
c = P[T].mean(1)
for nm, m in (('loose', loose), ('strip', strip)):
    print(nm, int(m.sum()), 'by part', np.bincount(part[m], minlength=7).tolist())
    for p_ in np.unique(part[m]):
        mm = m & (part == p_)
        print('   part', p_, 'y', np.percentile(c[mm, 1], [0, 50, 100]).round(3), '|x|', np.percentile(np.abs(c[mm, 0]), [0, 50, 100]).round(3))
order = np.argsort(Jt, 1); Js = np.take_along_axis(Jt, order, 1); Ws = np.round(np.take_along_axis(Wt, order, 1), 4)
Js[Ws == 0] = -1; key = [tuple(a) + tuple(b) for a, b in zip(Js, Ws)]
g = defaultdict(list)
for i, k in enumerate(key):
    g[k].append(i)
lv = np.unique(T[loose].ravel()); has = 0; dd = []
nonz = np.zeros(len(P), bool); nonz[T[~zero].ravel()] = True
for v in lv:
    cand = [j for j in g[key[v]] if j != v and nonz[j] and (np.round(P[j], 6) != np.round(P[v], 6)).any()]
    if cand:
        d = np.linalg.norm(P[cand] - P[v], axis=1).min(); dd.append(d); has += d < 0.025
print('loose vertices', len(lv), 'with a same-weight UV vertex within 25 mm', has, 'dist mm pct', np.percentile(np.array(dd) * 1000, [0, 25, 50, 75, 100]).round(2) if dd else None)
