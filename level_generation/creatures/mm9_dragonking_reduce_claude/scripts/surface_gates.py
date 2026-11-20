#!/usr/bin/env python3
"""Two GLB gates of a reduced Dragon King against the installed one (same vertices: every candidate LOD0 vertex is an
installed vertex, so kept vertices move exactly as installed; what can change is the surface between them).
  wing attachment: anchors = vertices with wing (Y*) and non-wing weight both > 0.05 (the membrane's body line and the
     wing root): how many survive, and over every clip (10 Hz) the largest distance from a posed removed vertex within
     ROOT_R of an anchor to the posed candidate surface (does the root band keep its shape);
  jitter: each removed vertex is pinned at rest to its nearest candidate face (barycentric) and carried by that face through
     every clip at 48 fps; per clip the largest second difference |p[i+1] - 2 p[i] + p[i-1]| (mm/frame^2) of these surface
     points against the largest of the kept vertices (the same in both models) and of the removed source vertices.
     A clip passes when the surface-point maximum is not above the kept-vertex maximum (or not above the removed source
     vertices' own maximum).
Usage: surface_gates.py <candidate glb> <out json>"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model  # noqa: E402
import bglbio as gb  # noqa: E402
ROOT_R = 0.5; FPS = 48.0
src = HERE / 'before' / 'mm9_dragonking.glb'; cand = Path(sys.argv[1])


def load(p):
    doc, b = gb.read(p); node = next(n for n in doc['nodes'] if n.get('name') == 'DragonKing' and 'mesh' in n)
    return gb.prims(doc, b, node['mesh']), [doc['nodes'][i]['name'] for i in doc['skins'][0]['joints']]


sp, names = load(src); cp, _ = load(cand)
key = lambda p: np.c_[np.round(p['POSITION'].astype(float), 6), p['JOINTS_0'], np.round(p['WEIGHTS_0'].astype(float), 4)]
# candidate vertex -> source vertex (per primitive, exact attribute rows)
SV = np.concatenate([p['POSITION'] for p in sp]).astype(float); sk = np.concatenate([key(p) for p in sp])
ck = np.concatenate([key(p) for p in cp])
tree = cKDTree(sk); d, c2s = tree.query(ck); assert d.max() < 1e-6, d.max()
voff = np.cumsum([0] + [len(p['POSITION']) for p in cp])
CT = np.concatenate([p['T'].astype(np.int64) + voff[k] for k, p in enumerate(cp)])     # candidate faces, candidate ids
CTs = c2s[CT]                                                                          # in source ids
svoff = np.cumsum([0] + [len(p['POSITION']) for p in sp])
used_pos = set(map(tuple, np.round(SV[np.unique(CTs)], 6)))
srcV = np.concatenate([np.unique(p['T']) + svoff[k] for k, p in enumerate(sp)])
removed = np.array([v for v in srcV if tuple(np.round(SV[v], 6)) not in used_pos], np.int64)
kept = np.unique(CTs)
J = np.concatenate([p['JOINTS_0'] for p in sp]); W = np.concatenate([p['WEIGHTS_0'] for p in sp]).astype(float)
wing = np.array([n.startswith('Y') for n in names])
ww = sum(np.where(wing[J[:, k]], W[:, k], 0) for k in range(4)); nw = W.sum(1) - ww
anchors = np.flatnonzero((ww > 0.05) & (nw > 0.05))
anchor_kept = np.isin(np.round(SV[anchors], 6).view([('', float)] * 3), np.round(SV[kept], 6).view([('', float)] * 3)).sum()
near = removed[cKDTree(SV[anchors]).query(SV[removed])[0] < ROOT_R] if len(removed) else removed
print('removed', len(removed), 'kept', len(kept), 'anchors', len(anchors), 'anchors kept', int(anchor_kept), 'removed near root', len(near))


def pt_tri_bary(p, a, b, c):
    """closest point barycentrics (n,3) of points p on single triangles (n each)"""
    ab, ac, ap = b - a, c - a, p - a
    d00 = (ab * ab).sum(-1); d01 = (ab * ac).sum(-1); d11 = (ac * ac).sum(-1); d20 = (ap * ab).sum(-1); d21 = (ap * ac).sum(-1)
    den = np.maximum(d00 * d11 - d01 * d01, 1e-30)
    v = (d11 * d20 - d01 * d21) / den; w = (d00 * d21 - d01 * d20) / den
    bc = np.clip(np.stack([1 - v - w, v, w], -1), 0, None); return bc / bc.sum(-1, keepdims=True)


def nearest_face(X, pts, k=24):
    C = X[CTs].mean(1); _, nn = cKDTree(C).query(pts, k)
    tri = X[CTs[nn]]                                     # (n,k,3,3)
    best = None
    for j in range(k):
        bc = pt_tri_bary(pts, tri[:, j, 0], tri[:, j, 1], tri[:, j, 2])
        q = np.einsum('nk,nkc->nc', bc, tri[:, j]); dd = np.linalg.norm(q - pts, axis=1)
        if best is None:
            best = [dd, nn[:, j], bc]
        else:
            m = dd < best[0]; best[0][m] = dd[m]; best[1][m] = nn[m, j]; best[2][m] = bc[m]
    return best


m = Model(Glb(str(src)))
X0 = np.concatenate([pz for pz, _ in m.skinned_positions(m.world({}))])
_, pf, pb = nearest_face(X0, X0[removed]) if len(removed) else (None, np.zeros(0, int), np.zeros((0, 3)))
out = {'removed': int(len(removed)), 'anchors': int(len(anchors)), 'anchors_kept': int(anchor_kept), 'clips': {}}
for clip in m.clips:
    t1 = m.clip_times(clip)[-1]
    ts = np.append(np.arange(0, t1, 1 / FPS), t1)
    surf, kv, rv = [], [], []
    root = 0.0
    for i, t in enumerate(ts):
        X = np.concatenate([pz for pz, _ in m.skinned_positions(m.world(m.sample(clip, t)))])
        surf.append(np.einsum('nk,nkc->nc', pb, X[CTs[pf]])); kv.append(X[kept]); rv.append(X[removed])
        if len(near) and i % 5 == 0:
            root = max(root, float(nearest_face(X, X[near])[0].max()))
    S, K, R = (np.stack(a) for a in (surf, kv, rv))
    acc = lambda A: np.linalg.norm(A[2:] - 2 * A[1:-1] + A[:-2], axis=-1).max() * 1000 if len(A) > 2 and A.shape[1] else 0.0
    s_, k_, r_ = acc(S), acc(K), acc(R)
    out['clips'][clip] = {'surface_max': round(s_, 3), 'kept_max': round(k_, 3), 'removed_src_max': round(r_, 3),
                          'pass': bool(s_ <= k_ + 1e-6 or s_ <= r_ + 1e-6), 'root_near_dev_mm': round(root * 1000, 2)}
    print(f'{clip:12s} jitter surface {s_:7.2f} kept {k_:7.2f} removed-src {r_:7.2f} mm/f^2  {"ok" if out["clips"][clip]["pass"] else "FAIL"}  root-near dev {root * 1000:6.1f} mm')
Path(sys.argv[2]).write_text(json.dumps(out, indent=1))
