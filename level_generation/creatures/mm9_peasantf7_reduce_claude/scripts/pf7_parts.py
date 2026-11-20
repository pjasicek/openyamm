#!/usr/bin/env python3
"""Part label per installed LOD0 face (primitive order PeasantF7_A, PeasantF7Head) from the creature's own build mesh
../mm9_peasantf7_claude/work/uv_lined.npz (parts head, dress, skirt, hair, legs, hands, bracelets, braids; `inner` = linings and
caps from line_rims_pf7.py). GLB (x, y, z) = build (x, z, -y). Matched by face centroid + vertex set; prints the match residuals.
-> work/pf7_parts.npz (part, inner, dist per GLB face, names)."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, b, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantf7.glb', 'PeasantF7')
S = np.load(HERE.parent / 'mm9_peasantf7_claude' / 'work' / 'uv_lined.npz')
co = S['co']; P0 = np.c_[co[:, 0], co[:, 2], -co[:, 1]]; tri = S['tri']; part0 = S['comp'][tri[:, 0]]; inner0 = S['inner']
names = [str(x) for x in S['names']]
# key: sorted vertex positions (rounded) for exact matches, else centroid nearest
cen0 = P0[tri].mean(1); kt = cKDTree(cen0)
part, inner, dist = [], [], []
for pr in ('PeasantF7_A', 'PeasantF7Head'):
    P, T = D[pr]['P'], D[pr]['T']; c = P[T].mean(1)
    d, i = kt.query(c, k=4)
    # among the 4 nearest centroids take the one whose vertex set is closest (twin linings share centroids within mm)
    best = np.zeros(len(T), int); bd = np.full(len(T), 9.0)
    for k in range(4):
        cand = i[:, k]; vd = np.abs(np.sort(P[T], 1) - np.sort(P0[tri[cand]], 1)).max((1, 2))
        vd = np.array([np.min([np.abs(P[T[f]][None] - P0[tri[cand[f]]][[a, b_, c_]][None]).max() for a, b_, c_ in
                               ((0, 1, 2), (1, 2, 0), (2, 0, 1))]) for f in range(len(T))])
        better = vd < bd; best[better] = cand[better]; bd[better] = vd[better]
    part.append(part0[best]); inner.append(inner0[best]); dist.append(bd)
    print(pr, 'faces', len(T), 'max vertex residual mm p50/p99/max', np.percentile(bd * 1000, [50, 99]).round(3), round(bd.max() * 1000, 2),
          '>1mm', int((bd > 0.001).sum()))
    for n in range(len(names)):
        s = part[-1] == n
        if s.any():
            print(f'   {names[n]:10s} {int(s.sum()):5d} inner {int((s & inner[-1]).sum()):4d}')
np.savez(HERE / 'work' / 'pf7_parts.npz', part=np.concatenate(part), inner=np.concatenate(inner), dist=np.concatenate(dist),
         names=np.array(names))
