#!/usr/bin/env python3
"""Lining poke gate (Hanndl reduction's lining_gate.py, adapted to appended linings, 2026-11-05): per primitive and clip at
FPS, each lining twin vertex's signed distance to the posed cloth it lines (the installed faces of the 2-ring of its
source vertex; closest point, sign along that face's normal: at rest a lining lies inside, negative; a layered part's other
layer is not its cloth: the twin of a hair curtain lying over another hair layer is between them, under its own layer). Lining twins and the vertex each lines come from <candidate>.twins.json (glb_lining.py; rim-strip copies sit on the rim
and cap centres far inside: both left out). Reports per
clip and primitive the largest outward distance and the most twins more than TOL outside (a lining speck through cloth).
Usage: lining_gate.py <candidate glb> <installed glb> <out json> [fps 10] [tol m 0.0005]"""
import json
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
glb, src_glb, out = sys.argv[1:4]
FPS = float(sys.argv[4]) if len(sys.argv) > 4 else 10.0
TOL = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0005
LK = int(os.environ.get('LK', '32'))
m = Model(Glb(glb)); src = Model(Glb(src_glb))
TW = json.load(open(glb + '.twins.json'))['0']
setup = []
for k in range(2):
    sp, cp = src.primitives[k], m.primitives[k]
    nv0, nf0 = len(sp['positions']), len(sp['triangles'])
    P0 = sp['positions']; T0 = cp['triangles'][:nf0]
    assert np.array_equal(T0, sp['triangles']) and np.array_equal(cp['positions'][:nv0], P0)
    _, inv = np.unique(P0.round(6), axis=0, return_inverse=True); inv = inv.ravel(); n = inv.max() + 1
    TT = inv[T0]; e = np.concatenate([TT[:, [0, 1]], TT[:, [1, 2]], TT[:, [2, 0]]])
    _, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    fpiece = lab[TT[:, 0]]; vpiece = lab[inv]
    t = TW[list(TW)[k]]
    assert t['nv0'] == nv0
    kind = np.array(t['kind']); srcv = np.array(t['src'])
    new = nv0 + np.flatnonzero(kind == 1); j = srcv[kind == 1]
    keep = np.ones(len(new), bool)
    # each twin's own cloth: the installed faces of the 2-ring of the welded vertex it lines (padded per twin)
    from collections import defaultdict
    vf = defaultdict(set)
    for fi, tt in enumerate(TT):
        for v in tt:
            vf[v].add(fi)
    groups = []
    for pc in np.unique(vpiece[j]):
        sel = vpiece[j] == pc; lv = new[sel]
        rings = []
        for s_ in j[sel]:
            w = inv[s_]; r1 = vf[w]; r2 = set(r1)
            for f in r1:
                for v in TT[f]:
                    r2 |= vf[v]
            rings.append(sorted(r2))
        K = max(len(r) for r in rings)
        R = np.array([r + [r[0]] * (K - len(r)) for r in rings])
        groups.append((T0, lv, int(pc), R))
    setup.append(groups)
    print('prim', k, 'lining twins', int(keep.sum()), 'pieces', [(g[2], len(g[1])) for g in groups])


def signed(X, outer, linv, R):
    tr = X[outer]; nn = np.cross(tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0])
    nn /= np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-12)
    Q = X[linv]; ids = R
    best = np.full(len(Q), 1e9); sd = np.zeros(len(Q))
    for i in range(ids.shape[1]):
        f = ids[:, i]; q, _ = closest_on_triangles(Q, tr[f, 0], tr[f, 1], tr[f, 2]); dd = np.linalg.norm(q - Q, axis=1)
        u = dd < best; best[u] = dd[u]; sd[u] = ((Q - q) * nn[f])[u].sum(1)
    return sd


rep = {}
for clip in m.clips:
    t1 = m.clip_times(clip)[-1]; res = {}
    for t in np.append(np.arange(0, t1, 1 / FPS), t1):
        Xs = m.skinned_positions(m.world(m.sample(clip, t)))
        for k in range(2):
            for outer, linv, pc, R in setup[k]:
                sd = signed(Xs[k][0], outer, linv, R)
                r = res.setdefault(f'prim{k}:p{pc}', [-1.0, 0, 0])
                r[0] = max(r[0], float(sd.max())); c = int((sd > TOL).sum()); r[1] = max(r[1], c); r[2] += c > 0
    rep[clip] = {k: dict(max_out_mm=round(v[0] * 1000, 2), max_verts_out=v[1], frames_out=v[2]) for k, v in res.items()}
    print(f'{clip:12s} ' + ' | '.join(f'{k}: {v[0] * 1000:6.2f} mm, >{TOL * 1000:.1f} mm {v[1]:3d} verts, {v[2]:3d} frames'
                                     for k, v in res.items()), flush=True)
Path(out).write_text(json.dumps(rep, indent=1))
