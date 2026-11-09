#!/usr/bin/env python3
"""Skirt -> lining twin map of the installed girl body (assemble_pg.py's lining: an inner copy 4 mm in along the vertex
normal with reversed faces, plus rim strips along the hem and the apron's lower edge, plus add_cap.py's waist disc).
Vertices are compared as position classes (GLB vertices split at UV seams). Seed: skirt classes whose 4 mm prediction hits a
lining class within SEED m; then propagation over faces: a skirt face with two twinned corners takes as twin of its third
corner the third corner of the lining face on the twinned edge nearest the prediction. Writes work/lining_twins.npz:
twin_face (lining face per skirt face or -1), twin_cls (lining class per skirt class), pk (position class per body vertex)."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, b, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantgirl1e.glb', 'PeasantGirl')
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part'][g['mat'] == 0]
B = D['PeasantGirl_G1E']; P, T, UV = B['P'], B['T'], B['UV']
SEED = 0.0006
sk = np.flatnonzero(part == 1); ln = np.flatnonzero(part == 8)
_, pk = np.unique(np.round(P, 5), axis=0, return_inverse=True); pk = pk.ravel(); nc = pk.max() + 1
C = np.zeros((nc, 3)); C[pk] = P
TS = pk[T[sk]]; TL = pk[T[ln]]
fn = np.cross(C[TS[:, 1]] - C[TS[:, 0]], C[TS[:, 2]] - C[TS[:, 0]]) / 2
Ns = np.zeros((nc, 3))
for c in range(3):
    np.add.at(Ns, TS[:, c], fn)
sc = np.unique(TS); lc = np.unique(TL)
n_ = Ns[sc] / np.linalg.norm(Ns[sc], axis=1, keepdims=True)
pred = np.zeros((nc, 3)); pred[sc] = C[sc] - 0.004 * n_
dd, q = cKDTree(C[lc]).query(pred[sc])
twin = -np.ones(nc, np.int64); ok = dd < SEED; twin[sc[ok]] = lc[q[ok]]
print('seed', int(ok.sum()), 'of', len(sc))
edge_l = {}
for i, t in enumerate(TL):
    for a, b_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
        edge_l.setdefault((min(a, b_), max(a, b_)), []).append(i)
changed = True; rounds = 0
while changed:
    changed = False; rounds += 1
    for t in TS:
        tw = twin[t]
        if (tw >= 0).sum() != 2:
            continue
        k = int(np.flatnonzero(tw < 0)[0]); a, b_ = [tw[j] for j in range(3) if j != k]
        cand = [x for f in edge_l.get((min(a, b_), max(a, b_)), []) for x in TL[f] if x not in (a, b_)]
        if not cand:
            continue
        x = min(cand, key=lambda c_: np.linalg.norm(C[c_] - pred[t[k]]))
        if np.linalg.norm(C[x] - pred[t[k]]) < 0.012 and x not in twin:
            twin[t[k]] = x; changed = True
print('propagated in', rounds, 'rounds; twinned classes', int((twin[sc] >= 0).sum()), 'of', len(sc))
lfaces = {tuple(sorted(t)): ln[i] for i, t in enumerate(TL)}
twin_face = -np.ones(len(T), np.int64)
for f, t in zip(sk, TS):
    if (twin[t] >= 0).all():
        k = tuple(sorted(twin[t]))
        if k in lfaces:
            twin_face[f] = lfaces[k]
hit = twin_face[sk] >= 0
print('skirt faces with a lining twin face', int(hit.sum()), 'of', len(sk), '; lining faces twinned', len(set(twin_face[sk][hit])),
      'of', len(ln))
res = np.linalg.norm(C[twin[sc[twin[sc] >= 0]]] - pred[sc[twin[sc] >= 0]], axis=1)
print('twin residual vs 4 mm prediction: median', round(float(np.median(res)) * 1000, 2), 'p99', round(float(np.percentile(res, 99)) * 1000, 2),
      'max', round(float(res.max()) * 1000, 2), 'mm')
# UV seams: GLB vertices per class on the skirt and on the lining
ns = np.bincount(pk[np.unique(T[sk])], minlength=nc); nl = np.bincount(pk[np.unique(T[ln])], minlength=nc)
tws = sc[twin[sc] >= 0]
print('skirt classes with >1 GLB vertex', int((ns[sc] > 1).sum()), '; their twins with >1 lining GLB vertex',
      int((nl[twin[tws]] > 1).sum()), '; lining seam classes whose skirt class has 1 vertex', int(((nl[twin[tws]] > 1) & (ns[tws] == 1)).sum()))
np.savez(HERE / 'work' / 'lining_twins.npz', twin_face=twin_face, twin_cls=twin, pk=pk)
