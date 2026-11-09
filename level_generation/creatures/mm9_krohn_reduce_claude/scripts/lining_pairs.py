#!/usr/bin/env python3
"""Krohn's rim linings (../mm9_krohn_claude/scripts/linings_kr.sh -> rim_lining.py): band faces (master face index < 9816 with
`lined`) were duplicated behind themselves (4 mm, 0.5 mm for Meshy's inner layer, clamped behind nearby cloth), flipped, same
weights; rim strips join each open rim loop to its twin loop. Per body GLB face: band / lining / rim, and per band topological
vertex its lining twin (GLB vertex), found from the face pairs (each lining face = one band face, corners matched by the best of
the 3 rotations). -> work/lining_pairs.npz: band, lining, rim (per body face), twin (per body GLB vertex: lining GLB vertex or -1;
for a band vertex with UV copies, the lining copy whose UV is nearest), stats printed."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_krohn.glb', 'Krohn')
L = np.load(HERE / 'work' / 'glb_labels.npz')
B = D['Krohn']; P, T, UV, J, W = B['P'], B['T'], B['UV'], B['J'], B['W']
n = len(T); src = L['src'][:n]; lined = L['lined'][:n] > 0
added = lined & (src >= 9816); band = lined & (src < 9816)
key = np.concatenate([np.round(P, 6), J.astype(float), np.round(W, 4)], 1)
_, topo = np.unique(key, axis=0, return_inverse=True); topo = topo.ravel()
_, ptopo = np.unique(np.round(P, 6), axis=0, return_inverse=True); ptopo = ptopo.ravel()
bandpos = np.zeros(ptopo.max() + 1, bool); bandpos[ptopo[T[band]].ravel()] = True
rim = added & bandpos[ptopo[T]].any(1)
lining = added & ~rim
print('band', int(band.sum()), 'lining', int(lining.sum()), 'rim', int(rim.sum()))
bf = np.flatnonzero(band); lf = np.flatnonzero(lining)
cb = P[T[bf]].mean(1); cl = P[T[lf]].mean(1)
nb = np.cross(P[T[bf, 1]] - P[T[bf, 0]], P[T[bf, 2]] - P[T[bf, 0]]); nb /= np.linalg.norm(nb, axis=1, keepdims=True) + 1e-20
nl = np.cross(P[T[lf, 1]] - P[T[lf, 0]], P[T[lf, 2]] - P[T[lf, 0]]); nl /= np.linalg.norm(nl, axis=1, keepdims=True) + 1e-20
tree = cKDTree(cb)
twin_t = {}; conflicts = 0; pairs = 0; resid = []
used = np.zeros(len(bf), bool); pair_of = -np.ones(n, np.int64); glb_votes = {}
for i, f in enumerate(lf):
    d, cand = tree.query(cl[i], 8)
    best = None
    for dd, c in zip(d, cand):
        o = T[bf[c]]; l = T[f]
        # lining is reversed: corner k of the lining ~ corner of the band in reversed order; try every rotation of both orders
        for perm in ((0, 2, 1), (2, 1, 0), (1, 0, 2), (0, 1, 2), (1, 2, 0), (2, 0, 1)):
            e = np.linalg.norm(P[o[list(perm)]] - P[l], axis=1).max()
            if not np.allclose(W[o[list(perm)]], W[l], atol=2e-3) or (J[o[list(perm)]] != J[l]).any():
                continue
            if best is None or e < best[0]:
                best = (e, c, perm)
    if best is None or best[0] > 0.0045:
        print('unmatched lining face', f, None if best is None else round(best[0] * 1000, 2)); continue
    e, c, perm = best; used[c] = True; pairs += 1; resid.append(e); pair_of[bf[c]] = f
    o = T[bf[c]][list(perm)]; l = T[f]
    for a, b_ in zip(o, l):
        glb_votes.setdefault(int(a), []).append(int(b_))
        t = topo[a]
        if t in twin_t and topo[twin_t[t]] != topo[b_]:
            conflicts += 1
        twin_t.setdefault(t, b_)
resid = np.array(resid)
print('pairs', pairs, 'of', len(lf), 'band faces used', int(used.sum()), 'of', len(bf), 'corner residual max mm',
      round(resid.max() * 1000, 2), 'p99', round(np.percentile(resid, 99) * 1000, 2), 'topo conflicts', conflicts)
# per band GLB vertex: the lining copy (same twin topology) with the nearest UV
lin_by_topo = {}
for g in np.unique(T[lf]):
    lin_by_topo.setdefault(topo[g], []).append(g)
twin = -np.ones(len(P), np.int64)
for g in np.unique(T[bf]):
    t = topo[g]
    if t not in twin_t:
        continue
    if g in glb_votes:
        v, c = np.unique(glb_votes[g], return_counts=True); twin[g] = v[c.argmax()]; continue
    cands = lin_by_topo[topo[twin_t[t]]]
    twin[g] = min(cands, key=lambda c: np.abs(UV[c] - UV[g]).sum())
miss = [g for g in np.unique(T[bf]) if twin[g] < 0]
print('GLB vertex vote conflicts', sum(len(set(v)) > 1 for v in glb_votes.values()))
print('band GLB vertices', len(np.unique(T[bf])), 'without twin', len(miss))
# re-emission check: the twins of the band faces used reproduce the installed lining faces exactly
re = twin[T[bf[used]]][:, ::-1]
inst = {tuple(sorted(topo[x])) for x in T[lf]}
same = sum(tuple(sorted(topo[x])) in inst for x in re)
print('re-emitted from the installed band', len(re), 'match installed lining faces (topology)', same)
exact = {tuple(sorted(x)) for x in T[lf]}
print('  exact GLB-vertex match', sum(tuple(sorted(x)) in exact for x in re))
np.savez(HERE / 'work' / 'lining_pairs.npz', band=band, lining=lining, rim=rim, twin=twin, band_used=np.isin(np.arange(n), bf[used]), pair_of=pair_of)
