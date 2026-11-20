#!/usr/bin/env python3
"""Lining holes of an mpqem step (new open edges, welded by position per primitive, that the installed LOD0 does not have):
where a lining band meets another band or the hair twin's border, the re-emitted lining can miss a triangle. For each new
open edge, the installed faces (lining or not) holding both end positions that the step dropped, and their twin faces
(outer side), are marked; the outer faces go into keep (their installed linings are re-used unchanged).
Usage: hole_keeps.py <mp npz> <sets tag> [previous keep npy] -> work/hole_keep.npy (bool per GLB face, prim order), counts"""
import sys
from pathlib import Path
from collections import Counter
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio  # noqa: E402
doc, b = bglbio.read(HERE / 'before' / 'mm9_peasantdm3.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantDM3' and 'mesh' in n)
d = np.load(HERE / 'work' / sys.argv[1]); S = np.load(HERE / 'work' / f'glb_sets_{sys.argv[2]}.npz')
prims = bglbio.prims(doc, b, node['mesh']); nf = [len(p['T']) for p in prims]; offs = np.cumsum([0] + nf)
out = np.load(HERE / 'work' / sys.argv[3]) if len(sys.argv) > 3 else np.zeros(offs[-1], bool)
pair = S['pair']; TW = np.load(HERE / 'work' / 'twins.npz')
for k, pr in enumerate(prims):
    P = pr['POSITION'].astype(float); T = pr['T']; _, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel()
    def edges(TT):
        c = Counter()
        for t in w[TT]:
            for a, b_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                c[(min(a, b_), max(a, b_))] += 1
        return c
    c0 = edges(T); T1 = d[pr['material']].astype(int); c1 = edges(T1)
    new = {e for e, n in c1.items() if n == 1} - {e for e, n in c0.items() if n == 1}
    have = {tuple(sorted(w[t])) for t in T1}
    hit = 0
    for f, t in enumerate(T):
        wt = set(w[t].tolist())
        if tuple(sorted(w[t])) in have:
            continue
        if any(a in wt and b_ in wt for a, b_ in new):
            g = offs[k] + f; out[g] = True; hit += 1
            if pair[g] >= 0:
                out[pair[g]] = True
            else:
                # second-pass lining (no face twin): the outer faces whose corner map lands on its positions
                mp_ = TW[f"map_{pr['material']}"]; tv = set(w[t].tolist())
                hitv = np.array([mp_[x] >= 0 and w[mp_[x]] in tv for x in range(len(P))])
                og = np.flatnonzero(hitv[T].any(1)); out[offs[k] + og] = True
    print(pr['material'], 'new open edges', len(new), 'dropped faces at them', hit)
np.save(HERE / 'work' / 'hole_keep.npy', out); print('hole keep total', int(out.sum()))
