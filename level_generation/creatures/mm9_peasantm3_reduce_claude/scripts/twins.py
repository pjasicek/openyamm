#!/usr/bin/env python3
"""PeasantDM4 copy (2026-11-04) of mm9_peasantdboy_reduce_claude/scripts/twins.py. DM4 change: body_reweight.py and
head_rigid.py ran after the linings, so a lining vertex's weights can differ a little from its outer vertex's on the chest and
collar: candidates need joints+weights within L1 0.35 (summed absolute weight difference over the joint union), not identical.
Original docstring: Lining twins of the installed LOD0 (the creature's linings_dboy.sh: hair_lining, rim_lining, sleeve_twin each duplicate
faces offset behind themselves, flipped, with the same weights). Per primitive: each vertex's twin candidates are the other
vertices with identical joints+weights (4 dp) within 6 mm; a face pair (f, g) is a twin pair when g's corners are the twins of
f's corners and g is a separate face. Lining = the side with a one-texel UV (zero UV area); a pair where both carry UVs (the
rim lining's inner-layer twins keep their UVs) takes the later face index as the lining. Writes work/twins.npz:
per GLB face (prim order as in the file) lining, lined, pair (face index of the twin, -1), and per prim a corner map
outer GLB vertex -> lining GLB vertex (map_<prim>, -1 where none). Read-only on the GLB."""
import sys
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio  # noqa: E402
doc, binary = bglbio.read(HERE / 'before' / 'mm9_peasantdm4.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantDM4' and 'mesh' in n)
prims = bglbio.prims(doc, binary, node['mesh'])
R = 0.006
WMAX = 0.35
out = {}; lin_all, lined_all, pair_all = [], [], []
for pr in prims:
    name = pr['material']; P = pr['POSITION'].astype(np.float64); T = pr['T']; U = pr['TEXCOORD_0'].astype(np.float64)
    J = pr['JOINTS_0'].astype(np.int64); W = pr['WEIGHTS_0'].astype(np.float64)
    N = pr['NORMAL'].astype(np.float64); N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    order = np.argsort(J, 1); Js = np.take_along_axis(J, order, 1); Ws = np.round(np.take_along_axis(W, order, 1), 4)
    Ws[Ws == 0] = 0; Js[Ws == 0] = -1
    pos = np.round(P, 6)
    nj = int(J.max()) + 1; WD = np.zeros((len(P), nj))
    for c in range(4):
        np.add.at(WD, (np.arange(len(P)), J[:, c]), W[:, c])
    cand = [set() for _ in range(len(P))]        # vertices at a different position, near-equal weights, within R
    if True:
        tr = cKDTree(P)
        for i, j in tr.query_pairs(R):
            if (pos[i] == pos[j]).all():
                continue
            if np.abs(WD[i] - WD[j]).sum() > WMAX:
                continue
            dv = P[j] - P[i]; dl = np.linalg.norm(dv)
            # back to back: opposite normals, the offset along the normal (either side)
            if N[i] @ N[j] < -0.3 and abs(dv @ N[i]) > 0.7 * dl and abs(dv @ N[j]) > 0.7 * dl:
                cand[i].add(j); cand[j].add(i)
    # faces by vertex-position triple
    _, tp = np.unique(pos, axis=0, return_inverse=True); tp = tp.ravel()
    fkey = {}
    for f, t in enumerate(T):
        fkey.setdefault(frozenset(tp[t].tolist()), []).append(f)
    ua = np.abs((U[T[:, 1], 0] - U[T[:, 0], 0]) * (U[T[:, 2], 1] - U[T[:, 0], 1]) - (U[T[:, 2], 0] - U[T[:, 0], 0]) * (U[T[:, 1], 1] - U[T[:, 0], 1]))
    zero = ua < 1e-10
    pair = -np.ones(len(T), np.int64); amb = 0
    for f, t in enumerate(T):
        cs = [sorted({int(tp[c]) for c in cand[v]}) for v in t]
        if not all(cs):
            continue
        hits = set()
        for a in cs[0]:
            for b in cs[1]:
                for c in cs[2]:
                    for g in fkey.get(frozenset((a, b, c)), []):
                        if g != f:
                            hits.add(g)
        if len(hits) == 1:
            pair[f] = hits.pop()
        elif len(hits) > 1:
            amb += 1
    mutual = (pair >= 0) & (pair[np.maximum(pair, 0)] == np.arange(len(T)))
    lining = np.zeros(len(T), bool)
    for f in np.flatnonzero(mutual):
        g = pair[f]
        if zero[f] != zero[g]:
            lining[f] = zero[f]
        elif not zero[f] and not zero[g]:
            lining[f] = f > g
        else:
            lining[f] = f > g      # both one-texel: should not happen
    lined = np.zeros(len(T), bool); lined[pair[lining]] = True
    both_zero = int((mutual & zero & zero[np.maximum(pair, 0)]).sum())
    # corner map outer GLB vertex -> lining GLB vertex
    mp = -np.ones(len(P), np.int64); conflicts = 0; conf_v = np.zeros(len(P), bool)
    for g in np.flatnonzero(lining):
        f = pair[g]
        for v in T[f]:
            m = [w for w in T[g] if w in cand[v]]
            if len(m) != 1:
                conflicts += 1; conf_v[v] = True; continue
            if mp[v] >= 0 and mp[v] != m[0]:
                # one-texel lining vertices split by UV are equivalent; keep the first
                if (pos[mp[v]] != pos[m[0]]).any():
                    conflicts += 1; conf_v[v] = True
                continue
            mp[v] = m[0]
    zl = zero & ~mutual
    print(f'{name}: faces {len(T)} zeroUV {int(zero.sum())} pairs {int(mutual.sum()) // 2} one-sided {int(((pair >= 0) & ~mutual).sum())} '
          f'ambiguous {amb} lining {int(lining.sum())} (one-texel {int((lining & zero).sum())}, with UVs {int((lining & ~zero).sum())}) '
          f'lined {int(lined.sum())} both-zero {both_zero} unpaired zeroUV {int(zl.sum())} map {int((mp >= 0).sum())} conflicts {conflicts}')
    d = np.linalg.norm(P[np.flatnonzero(mp >= 0)] - P[mp[mp >= 0]], axis=1)
    print(f'   twin offset mm: min {d.min()*1000:.2f} p50 {np.median(d)*1000:.2f} max {d.max()*1000:.2f}')
    out[f'map_{name}'] = mp; out[f'zero_{name}'] = zero; out[f'pair_{name}'] = pair
    out[f'conf_{name}'] = conf_v
    lin_all.append(lining); lined_all.append(lined); pair_all.append(pair)
np.savez(HERE / 'work' / 'twins.npz', lining=np.concatenate(lin_all), lined=np.concatenate(lined_all), **out)
# diagnostics: unpaired one-texel faces, rim strips (sharing a position with a non-lining UV face) vs loose linings
if __name__ == '__main__' and len(sys.argv) > 1:
    off = 0
    for pr in prims:
        name = pr['material']; T = pr['T']; P = pr['POSITION'].astype(np.float64)
        zero = out[f'zero_{name}']; lin = np.concatenate(lin_all)[off:off + len(T)]; ld = np.concatenate(lined_all)[off:off + len(T)]
        off += len(T)
        _, tp = np.unique(np.round(P, 6), axis=0, return_inverse=True); tp = tp.ravel()
        normal_v = np.zeros(tp.max() + 1, bool); normal_v[tp[T[~zero & ~lin]].ravel()] = True
        un = zero & ~lin
        strip = un & normal_v[tp[T]].any(1)
        loose = un & ~strip
        c = P[T[loose]].mean(1)
        print(name, 'unpaired one-texel', int(un.sum()), 'rim strips', int(strip.sum()), 'loose', int(loose.sum()))
        if loose.any():
            print('   loose y', np.percentile(c[:, 1], [0, 25, 50, 75, 100]).round(3), '|x|', np.percentile(np.abs(c[:, 0]), [0, 50, 100]).round(3))
            hist = np.histogram(c[:, 1], bins=np.arange(0, 1.1, 0.1))[0]; print('   by y decile', hist.tolist())
