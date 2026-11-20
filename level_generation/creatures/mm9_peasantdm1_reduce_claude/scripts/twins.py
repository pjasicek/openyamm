#!/usr/bin/env python3
"""Lining twins of the installed LOD0 (the creature's linings_dboy.sh: hair_lining, rim_lining, sleeve_twin each duplicate
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
doc, binary = bglbio.read(HERE / 'before' / 'mm9_peasantdm1.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantDM1' and 'mesh' in n)
prims = bglbio.prims(doc, binary, node['mesh'])
R = 0.006
R2 = 0.0035
import os
UVTWIN = os.environ.get('UVTWIN', '1') == '1'; UVW_L1 = float(os.environ.get('UVW_L1', '0.35'))
out = {}; lin_all, lined_all, pair_all = [], [], []
for pr in prims:
    name = pr['material']; P = pr['POSITION'].astype(np.float64); T = pr['T']; U = pr['TEXCOORD_0'].astype(np.float64)
    J = pr['JOINTS_0'].astype(np.int64); W = pr['WEIGHTS_0'].astype(np.float64)
    N = pr['NORMAL'].astype(np.float64); N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    order = np.argsort(J, 1); Js = np.take_along_axis(J, order, 1); Ws = np.round(np.take_along_axis(W, order, 1), 4)
    Ws[Ws == 0] = 0; Js[Ws == 0] = -1
    key = [tuple(a) + tuple(b) for a, b in zip(Js, Ws)]
    groups = defaultdict(list)
    for i, k in enumerate(key):
        groups[k].append(i)
    pos = np.round(P, 6)
    cand = [set() for _ in range(len(P))]        # vertices at a different position, same weights, within R
    for k, vs in groups.items():
        if len(vs) < 2:
            continue
        vs = np.array(vs); tr = cKDTree(P[vs])
        for a, b in tr.query_pairs(R):
            i, j = vs[a], vs[b]
            if (pos[i] == pos[j]).all():
                continue
            dv = P[j] - P[i]; dl = np.linalg.norm(dv)
            # back to back: opposite normals, the offset along the normal (either side)
            if N[i] @ N[j] < -0.3 and abs(dv @ N[i]) > 0.7 * dl and abs(dv @ N[j]) > 0.7 * dl:
                cand[i].add(j); cand[j].add(i)
    # PeasantDM1 (hair_twin.py: the hair shell below 0.44 m duplicated 2 mm behind itself with the same UVs): a painted copy
    # keeps its UV, so a vertex with the identical UV at another position within R, weights within L1 UVW_L1 and the offset
    # >= 0.5 mm is a twin too, whatever the normals (the twin band's border normals differ: 31 % failed the normal test) and
    # despite small weight differences (8 % of the border vertices; the runtime's 4-influence normalisation)
    if UVTWIN:
        uvk = defaultdict(list)
        for i in range(len(P)):
            uvk[(round(U[i, 0], 6), round(U[i, 1], 6))].append(i)
        for vs in uvk.values():
            if len(vs) < 2 or len(vs) > 8:
                continue
            for a_ in range(len(vs)):
                for b_ in range(a_ + 1, len(vs)):
                    i, j = vs[a_], vs[b_]
                    dl = np.linalg.norm(P[i] - P[j])
                    if dl < 0.0005 or dl > R:
                        continue
                    x = np.zeros(J.max() + 1); y = np.zeros(J.max() + 1); np.add.at(x, J[i], W[i]); np.add.at(y, J[j], W[j])
                    if np.abs(x - y).sum() < UVW_L1:
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
    if len(d): print(f'   twin offset mm: min {d.min()*1000:.2f} p50 {np.median(d)*1000:.2f} max {d.max()*1000:.2f}')
    # PeasantDM1 second pass: one-texel linings that pair with no face (the lining quad split on the other diagonal) but whose
    # three corners each have exactly one back-to-back twin among the painted outer vertices -> lining2 (re-emitted by vertex
    # map); painted unpaired outer faces whose three corners each have exactly one one-texel twin -> lined2 (map extended)
    zv = np.zeros(len(P), bool); zv[T[zero].ravel()] = True
    ov = np.zeros(len(P), bool); ov[T[~zero].ravel()] = True
    # second-pass twins: same weights (4 dp key), within R2, no normal test (rim normals are smoothed across the strip)
    cand2 = [set() for _ in range(len(P))]
    for k, vs in groups.items():
        if len(vs) < 2:
            continue
        vs = np.array(vs); tr = cKDTree(P[vs])
        for a, b_ in tr.query_pairs(R2):
            i, j = vs[a], vs[b_]
            if (pos[i] == pos[j]).all() or zv[i] == zv[j]:
                continue
            if not ((zv[i] and ov[j] and not zv[j]) or (zv[j] and ov[i] and not zv[i])):
                continue
            cand2[i].add(j); cand2[j].add(i)
    def uniq(v, want):
        ps = {int(tp[c]) for c in cand2[v] if want[c]}
        if len(ps) != 1:
            return -1
        p_ = ps.pop()
        return next(c for c in cand2[v] if want[c] and tp[c] == p_)
    lining2 = np.zeros(len(T), bool); lined2 = np.zeros(len(T), bool)
    paint_p = np.zeros(tp.max() + 1, bool); paint_p[tp[T[~zero].ravel()]] = True
    for f in np.flatnonzero(zero & ~mutual & ~paint_p[tp[T]].any(1)):      # loose only (rim strips touch the painted rim)
        if all(uniq(v, ov) >= 0 for v in T[f]):
            lining2[f] = True
    l2p = np.zeros(tp.max() + 1, bool); l2p[tp[T[lining2].ravel()]] = True     # outer faces lined by a lining2 face only
    for f in np.flatnonzero(~zero & ~mutual):
        tws = [uniq(v, zv) for v in T[f]]
        if all(t >= 0 for t in tws) and all(l2p[tp[t]] for t in tws):
            lined2[f] = True
            for v, t in zip(T[f], tws):
                if mp[v] < 0 and not conf_v[v]:
                    mp[v] = t
    lined2 &= (mp[T] >= 0).all(1)
    # a lining2 face is dropped (re-emitted) only when every corner's outer twin lies on a lined2 face; the others stay loose
    d2p = np.zeros(tp.max() + 1, bool); d2p[tp[T[lined2].ravel()]] = True
    for f in np.flatnonzero(lining2):
        if not all(d2p[tp[uniq(v, ov)]] for v in T[f]):
            lining2[f] = False
    print(f'   second pass: lining2 {int(lining2.sum())} lined2 {int(lined2.sum())}')
    out[f'lining2_{name}'] = lining2; out[f'lined2_{name}'] = lined2
    out[f'map_{name}'] = mp; out[f'zero_{name}'] = zero; out[f'pair_{name}'] = pair
    out[f'conf_{name}'] = conf_v
    lin_all.append(lining); lined_all.append(lined); pair_all.append(pair)
np.savez(HERE / 'work' / 'twins.npz', lining=np.concatenate(lin_all), lined=np.concatenate(lined_all),
         lining2=np.concatenate([out[f'lining2_{p["material"]}'] for p in prims]),
         lined2=np.concatenate([out[f'lined2_{p["material"]}'] for p in prims]), **out)
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
