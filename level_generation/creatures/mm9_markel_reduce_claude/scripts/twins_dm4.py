#!/usr/bin/env python3
"""Lining twins of the installed PeasantDM4 LOD0 (the creature's linings.sh: rim_lining.py bands duplicated 3 mm behind
themselves, or 0.5 mm for Meshy's inner-layer faces, clipped to 40 % of the distance to cloth behind; cap_lining.py the cap
3 mm inward; twin_patch.py own-paint twins 0.5 mm behind; all flipped, weights copied, then body_reweight.py/head_rigid.py
changed some weights, so a twin's weights are near-equal, not identical).
Partners (topological vertices by position): a painted copy keeps its face's UVs, so its partner is the vertex with the same
UV at another position within 4.2 mm with opposite normal; a one-texel lining vertex's partner is the nearest painted vertex
within 4.2 mm with opposite normal, the offset along the normal and weights within L1 0.35. Faces are paired when one face's
corners map onto another face (triangles; quads of two triangles as a fallback for reversed quads split on the other
diagonal). Roles: the one-texel side is the lining (re-emitted by mpqem.py), the painted side is 'lined' (cut under the texture
and chart guards); both painted: the later face is the lining. Rim strips (one-texel quads joining a rim to its lining) map
onto themselves and stay unpaired (kept). Bands = connected components of the lining faces; an outer vertex on the border of
two bands has a twin in each, so the corner map is per band (mpqem.py cuts each band on its own); a pair whose corner has two
twins within its band is dropped (kept). Validation: each pair's corners mapped through its band's map land exactly on its own
lining face's corners. Writes work/twins.npz: lining, lined, band (per GLB face, prim order), map_<prim> (bands x GLB vertices), pair (pair id per face, -1).
"""
import sys
from pathlib import Path
from itertools import product
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio  # noqa: E402
doc, binary = bglbio.read(HERE / 'before' / 'mm9_peasantdm4.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantDM4' and 'mesh' in n)
prims = bglbio.prims(doc, binary, node['mesh'])
R, WMAX = 0.0042, 0.35
out = {}; lin_all, lined_all, band_all, pid_all = [], [], [], []
for pr in prims:
    name = pr['material']; P = pr['POSITION'].astype(np.float64); T = pr['T']
    J = pr['JOINTS_0'].astype(np.int64); W = pr['WEIGHTS_0'].astype(np.float64)
    _, tp = np.unique(np.round(P, 6), axis=0, return_inverse=True); tp = tp.ravel(); n = tp.max() + 1
    X = np.zeros((n, 3)); X[tp] = P; TF = tp[T]
    fn = np.cross(X[TF[:, 1]] - X[TF[:, 0]], X[TF[:, 2]] - X[TF[:, 0]])
    fnu = fn / np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-20)
    N = np.zeros((n, 3))
    for c in range(3):
        np.add.at(N, TF[:, c], fn)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    rep = np.zeros(n, int); rep[tp] = np.arange(len(P))
    WD = np.zeros((n, int(J.max()) + 1))
    for c in range(4):
        WD[np.arange(n), J[rep, c]] += W[rep, c]
    # front[v]: the back-to-back partner of topo vertex v. Painted copies (twin patches, inner-layer twins, the cap lining)
    # keep their face's UVs: partner = a vertex with the same UV (1e-6) at another position within R, opposite normal.
    # One-texel lining vertices: partner = the nearest vertex of a painted face with opposite normal, offset along the
    # normal and near-equal weights.
    U = pr['TEXCOORD_0'].astype(np.float64)
    ua = np.abs((U[T[:, 1], 0] - U[T[:, 0], 0]) * (U[T[:, 2], 1] - U[T[:, 0], 1]) - (U[T[:, 2], 0] - U[T[:, 0], 0]) * (U[T[:, 1], 1] - U[T[:, 0], 1]))
    zero = ua < 1e-10
    painted_v = np.zeros(n, bool); painted_v[TF[~zero].ravel()] = True
    texel_v = np.zeros(n, bool); texel_v[TF[zero].ravel()] = True
    front = -np.ones(n, np.int64)

    def ok(v, j):
        dv = X[j] - X[v]; L = np.linalg.norm(dv)
        return L > 1e-7 and L <= R and N[v] @ N[j] < -0.3 and abs(dv @ N[v]) > 0.7 * L and np.abs(WD[v] - WD[j]).sum() <= WMAX
    uvkey = {}
    for i in range(len(P)):
        uvkey.setdefault((round(U[i, 0], 6), round(U[i, 1], 6)), set()).add(int(tp[i]))
    for i in range(len(P)):
        v = tp[i]
        if front[v] >= 0 or not painted_v[v]:
            continue
        c = [j for j in uvkey[(round(U[i, 0], 6), round(U[i, 1], 6))] if j != v and ok(v, j)]
        if c:
            front[v] = min(c, key=lambda j: np.linalg.norm(X[j] - X[v]))
    pv = np.flatnonzero(painted_v); ptree = cKDTree(X[pv])
    for v in np.flatnonzero(texel_v & ~painted_v):
        for dd, k in zip(*ptree.query(X[v], k=8)):
            if dd <= R and ok(v, pv[k]):
                front[v] = pv[k]; break
    # painted vertices without a same-UV partner but with a one-texel lining behind them: partner = that lining vertex
    for v in np.flatnonzero(texel_v & ~painted_v):
        o = front[v]
        if o >= 0 and front[o] < 0:
            front[o] = v
    fkey = {}
    for f, t in enumerate(TF):
        fkey.setdefault(frozenset(t.tolist()), []).append(f)
    lining = np.zeros(len(T), bool); lined = np.zeros(len(T), bool); pairs = []
    used = set()
    for g, t in enumerate(TF):
        if (front[t] < 0).any():
            continue
        hits = [f for f in fkey.get(frozenset(front[t].tolist()), []) if f != g and fnu[f] @ fnu[g] < -0.3]
        if len(hits) == 1 and hits[0] not in used and g not in used:
            pairs.append(([hits[0]], [g])); used |= {hits[0], g}
    tri_pairs = len(pairs)
    edges = {}
    for f, t in enumerate(TF):
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            edges.setdefault((min(a, b), max(a, b)), []).append(f)
    qkey = {}
    for e, fs in edges.items():
        if len(fs) == 2 and not set(fs) & used:
            qkey.setdefault(frozenset(np.r_[TF[fs[0]], TF[fs[1]]].tolist()), []).append(tuple(fs))
    for e, gs in edges.items():
        if len(gs) != 2 or set(gs) & used:
            continue
        q = np.unique(np.r_[TF[gs[0]], TF[gs[1]]])
        if len(q) != 4 or (front[q] < 0).any():
            continue
        hits = [fs for fs in qkey.get(frozenset(front[q].tolist()), []) if not set(fs) & used and not set(fs) & set(gs)
                and fnu[fs[0]] @ fnu[gs[0]] < -0.3]
        if len(hits) == 1:
            pairs.append((list(hits[0]), list(gs))); used |= set(hits[0]) | set(gs)
    quad_pairs = len(pairs) - tri_pairs
    # roles: the one-texel side is the lining (re-emitted); the painted side is cut under the texture and chart guards. Both
    # painted (twin patches, inner-layer twins, the cap lining: the copy keeps the face's own UVs): the later faces
    # are the lining. Both one-texel: dropped from pairing (kept by the set maker).
    roled = []; bothzero = 0
    for fs, gs in pairs:
        zf, zg = zero[fs].all(), zero[gs].all()
        if zf and zg or zero[fs].any() and not zf or zero[gs].any() and not zg:
            bothzero += 1; continue
        if zf or (not zg and min(fs) > min(gs)):
            fs, gs = gs, fs
        roled.append((fs, gs))
    pairs = roled
    for fs, gs in pairs:
        lined[fs] = True; lining[gs] = True
    both = lined & lining
    # bands: connected components of the lining faces (one rim_lining run, the cap lining, one twin patch); an outer vertex on
    # the border of two bands has a twin in each, so the corner map is per band and mpqem.py cuts each band on its own
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    lf = np.array([g for _, gs in pairs for g in gs], np.int64)
    eid = {}
    rows, cols = [], []
    for k, g in enumerate(lf):
        t = TF[g]
        for a_, b_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            e = (min(a_, b_), max(a_, b_), bool(zero[g]))     # one-texel and painted linings never share a band
            if e in eid:
                rows.append(eid[e]); cols.append(k)
            else:
                eid[e] = k
    nb_, lab = connected_components(coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(lf), len(lf))), directed=False)
    fband = -np.ones(len(T), np.int64); fband[lf] = lab
    band = -np.ones(len(T), np.int64)
    ctp = -np.ones((nb_, n), np.int64); conflT = np.zeros((nb_, n), bool)
    for fs, gs in pairs:
        bb = fband[gs[0]]
        assert (fband[gs] == bb).all()
        band[fs] = bb; band[gs] = bb
        for w in np.unique(TF[gs].ravel()):
            o = front[w]
            if ctp[bb, o] >= 0 and ctp[bb, o] != w:
                conflT[bb, o] = True
            ctp[bb, o] = w if ctp[bb, o] < 0 else ctp[bb, o]
    ok_pairs = []; badpairs = []
    for fs, gs in pairs:
        bb = band[fs[0]]; tv = TF[fs].ravel()
        if (ctp[bb, tv] < 0).any() or conflT[bb, tv].any():
            badpairs.append((fs, gs)); band[fs] = -1; band[gs] = -1; lined[fs] = False; lining[gs] = False
        else:
            ok_pairs.append((fs, gs))
    # per GLB corner: among the GLB vertices this band's own lining faces use at the twin position, the one whose UV is nearest
    # the outer corner's UV (painted copies keep the face's UVs, split at the same seams; one-texel linings keep their band's
    # texel), so a re-emitted face stays on its chart
    glbs = {}
    for fs, gs in ok_pairs:
        bb = band[gs[0]]
        for w in T[gs].ravel():
            glbs.setdefault((bb, tp[w]), set()).add(int(w))
    mp = -np.ones((nb_, len(P)), np.int64)
    for bb in range(nb_):
        for v in np.flatnonzero(ctp[bb, tp] >= 0):
            c = sorted(glbs.get((bb, ctp[bb, tp[v]]), ()))
            if c:
                mp[bb, v] = c[int(np.argmin(np.abs(U[c] - U[v]).sum(1)))]
    # validation: each pair's re-emitted corners (per-band map) against its own lining face's corners
    conf = conflT.any(0)[tp]
    pd = np.array([max(np.linalg.norm(P[mp[band[fs[0]]][T[fs]].ravel()] [:, None] - P[T[gs].ravel()][None], axis=2).min(1).max(), 0) for fs, gs in ok_pairs])
    A_ = np.array([mp[band[f]][T[f]] for fs, _ in ok_pairs for f in fs]).reshape(-1, 3)
    Ua = U[A_]; spread = np.abs(Ua - Ua[:, :1]).max((1, 2))
    print('  re-emitted faces mixing UVs of a one-texel band', int(((spread > 1e-7) & zero[np.array([g for _, gs in ok_pairs for g in gs])][:len(spread)]).sum()) if len(spread) else 0)
    print('  pair corner residual mm p99/max', np.percentile(pd, 99) * 1000, pd.max() * 1000, 'pairs > 1 mm', int((pd > 1e-3).sum()))
    sizes = np.bincount(band[band >= 0], minlength=nb_)
    pid = -np.ones(len(T), np.int64)
    for i, (fs, gs) in enumerate(ok_pairs):
        pid[fs] = i; pid[gs] = i
    print(f'{name}: faces {len(T)} pairs tri {tri_pairs} quad {quad_pairs}, mixed-UV pairs skipped {bothzero}, dropped for band '
          f'conflicts {len(badpairs)}; lining {int(lining.sum())} (one-texel {int((lining & zero).sum())}) lined {int(lined.sum())}; '
          f'bands {nb_} (largest {sorted(sizes.tolist(), reverse=True)[:10]}); one-texel faces unpaired (rim strips, unmatched) '
          f'{int((zero & ~lining).sum())}')
    out[f'map_{name}'] = mp; out[f'conf_{name}'] = conf; out[f'zero_{name}'] = zero
    lin_all.append(lining); lined_all.append(lined); band_all.append(band); pid_all.append(pid + (10 ** 6 if pid_all else 0) * (pid >= 0))
np.savez(HERE / 'work' / 'twins.npz', lining=np.concatenate(lin_all), lined=np.concatenate(lined_all), band=np.concatenate(band_all), pair=np.concatenate(pid_all), **out)
